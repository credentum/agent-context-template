#!/usr/bin/env python3
"""
sum_scores_api.py: Advanced vector search with sum-of-scores ranking

This component provides:
1. Multi-query search with score aggregation
2. Contextual re-ranking based on document relationships
3. Temporal decay for outdated documents
4. Boost factors for document types
"""

import click
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchRequest


@dataclass
class SearchResult:
    """Enhanced search result with metadata"""

    vector_id: str
    document_id: str
    document_type: str
    file_path: str
    title: str
    score: float
    raw_scores: List[float]
    decay_factor: float
    boost_factor: float
    final_score: float
    payload: Dict[str, Any]


class SumScoresAPI:
    """Advanced vector search with sum-of-scores ranking"""

    def __init__(
        self, config_path: str = ".ctxrc.yaml", perf_config_path: str = "performance.yaml"
    ):
        self.config = self._load_config(config_path)
        self.perf_config = self._load_perf_config(perf_config_path)
        self.client = None
        self.collection_name = self.config.get("qdrant", {}).get(
            "collection_name", "project_context"
        )

        # Load scoring configuration from performance config
        ranking_config = self.perf_config.get("search", {}).get("ranking", {})
        self.decay_days = ranking_config.get("temporal_decay_days", 30)
        self.decay_rate = ranking_config.get("temporal_decay_rate", 0.01)

        # Document type boost factors from config
        self.type_boosts = ranking_config.get(
            "type_boosts",
            {
                "design": 1.2,
                "decision": 1.15,
                "sprint": 1.1,
                "architecture": 1.25,
                "api": 1.0,
                "test": 0.9,
                "documentation": 0.85,
            },
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from .ctxrc.yaml"""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}

    def _load_perf_config(self, perf_config_path: str) -> Dict[str, Any]:
        """Load performance configuration"""
        try:
            with open(perf_config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Return default config if file not found
            return {"search": {"ranking": {"temporal_decay_days": 30, "temporal_decay_rate": 0.01}}}

    def connect(self) -> bool:
        """Connect to Qdrant"""
        qdrant_config = self.config.get("qdrant", {})
        host = qdrant_config.get("host", "localhost")
        port = qdrant_config.get("port", 6333)

        try:
            self.client = QdrantClient(host=host, port=port)
            self.client.get_collections()
            return True
        except Exception as e:
            click.echo(f"Failed to connect to Qdrant: {e}", err=True)
            return False

    def _calculate_temporal_decay(self, last_modified: str) -> float:
        """Calculate temporal decay factor based on document age"""
        try:
            if not last_modified:
                return 1.0

            mod_date = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
            age_days = (datetime.now() - mod_date).days

            if age_days <= self.decay_days:
                return 1.0

            # Exponential decay after threshold
            decay = 1.0 - (self.decay_rate * (age_days - self.decay_days))
            return max(0.5, decay)  # Minimum 50% score

        except Exception:
            return 1.0

    def _get_type_boost(self, document_type: str) -> float:
        """Get boost factor for document type"""
        return self.type_boosts.get(document_type, 1.0)

    def search_single(
        self,
        query_vector: List[float],
        limit: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Perform single vector search"""
        search_params = {
            "collection_name": self.collection_name,
            "query_vector": query_vector,
            "limit": limit,
            "with_payload": True,
        }

        # Add filters if provided
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
            search_params["query_filter"] = Filter(must=conditions)

        # Search
        results = self.client.search(**search_params)

        # Convert to SearchResult objects
        search_results = []
        for result in results:
            payload = result.payload

            # Calculate factors
            decay_factor = self._calculate_temporal_decay(payload.get("last_modified", ""))
            boost_factor = self._get_type_boost(payload.get("document_type", "unknown"))

            # Calculate final score
            final_score = result.score * decay_factor * boost_factor

            search_results.append(
                SearchResult(
                    vector_id=result.id,
                    document_id=payload.get("document_id", ""),
                    document_type=payload.get("document_type", ""),
                    file_path=payload.get("file_path", ""),
                    title=payload.get("title", ""),
                    score=result.score,
                    raw_scores=[result.score],
                    decay_factor=decay_factor,
                    boost_factor=boost_factor,
                    final_score=final_score,
                    payload=payload,
                )
            )

        # Sort by final score
        search_results.sort(key=lambda x: x.final_score, reverse=True)

        return search_results

    def search_multi(
        self,
        query_vectors: List[List[float]],
        limit: int = 10,
        aggregation: str = "sum",
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Perform multi-query search with score aggregation"""

        # Collect results from all queries
        all_results: Dict[str, SearchResult] = {}

        for query_vector in query_vectors:
            results = self.search_single(
                query_vector, limit=limit * 2, filter_conditions=filter_conditions
            )

            for result in results:
                if result.vector_id in all_results:
                    # Aggregate scores
                    existing = all_results[result.vector_id]
                    existing.raw_scores.append(result.score)

                    if aggregation == "sum":
                        existing.score += result.score
                    elif aggregation == "max":
                        existing.score = max(existing.score, result.score)
                    elif aggregation == "avg":
                        existing.score = sum(existing.raw_scores) / len(existing.raw_scores)
                else:
                    all_results[result.vector_id] = result

        # Recalculate final scores
        for result in all_results.values():
            result.final_score = result.score * result.decay_factor * result.boost_factor

        # Sort and limit
        sorted_results = sorted(all_results.values(), key=lambda x: x.final_score, reverse=True)

        return sorted_results[:limit]

    def search_contextual(
        self,
        query_vector: List[float],
        context_doc_ids: List[str],
        limit: int = 10,
        context_weight: float = 0.3,
    ) -> List[SearchResult]:
        """Search with contextual re-ranking based on related documents"""

        # Get base results
        base_results = self.search_single(query_vector, limit=limit * 2)

        # Get vectors for context documents
        context_vectors = []
        for doc_id in context_doc_ids:
            try:
                # Search by document_id
                filter_cond = {"document_id": doc_id}
                context_results = self.search_single(
                    [0.0] * 1536, limit=1, filter_conditions=filter_cond
                )
                if context_results:
                    context_vectors.append(context_results[0])
            except Exception:
                continue

        # Re-rank based on similarity to context
        if context_vectors:
            for result in base_results:
                # Calculate average similarity to context documents
                context_scores = []

                for context in context_vectors:
                    # This would require actual vector similarity calculation
                    # For now, we'll use a simple heuristic based on document relationships
                    if result.document_type == context.document_type:
                        context_scores.append(0.8)
                    elif result.payload.get("sprint_number") == context.payload.get(
                        "sprint_number"
                    ):
                        context_scores.append(0.7)
                    else:
                        context_scores.append(0.5)

                if context_scores:
                    avg_context_score = sum(context_scores) / len(context_scores)
                    # Blend original score with context score
                    result.final_score = (
                        result.final_score * (1 - context_weight)
                        + avg_context_score * context_weight
                    )

        # Sort by final score
        base_results.sort(key=lambda x: x.final_score, reverse=True)

        return base_results[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get search index statistics"""
        try:
            collection_info = self.client.get_collection(self.collection_name)

            # Get document type distribution using sampling for large collections
            total_points = collection_info.points_count
            type_counts = {}

            if total_points > 1000:
                # Sample for large collections
                sample_size = min(500, total_points)
                sample_ids = []

                # Get a sample of point IDs
                points, _ = self.client.scroll(
                    collection_name=self.collection_name, limit=sample_size, with_payload=False
                )
                sample_ids = [p.id for p in points]

                # Retrieve payloads for sampled points
                retrieved = self.client.retrieve(
                    collection_name=self.collection_name, ids=sample_ids, with_payload=True
                )

                for point in retrieved:
                    doc_type = point.payload.get("document_type", "unknown")
                    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

                # Extrapolate counts
                factor = total_points / sample_size
                type_counts = {k: int(v * factor) for k, v in type_counts.items()}
            else:
                # For small collections, get all points
                offset = None
                while True:
                    points, next_offset = self.client.scroll(
                        collection_name=self.collection_name,
                        limit=100,
                        offset=offset,
                        with_payload=True,
                    )

                    for point in points:
                        doc_type = point.payload.get("document_type", "unknown")
                        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

                    if next_offset is None:
                        break
                    offset = next_offset

            return {
                "total_vectors": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": str(collection_info.config.params.vectors.distance),
                "document_types": type_counts,
                "type_boosts": self.type_boosts,
                "decay_config": {"decay_days": self.decay_days, "decay_rate": self.decay_rate},
            }
        except Exception as e:
            return {"error": str(e)}


@click.group()
def cli():
    """Sum-of-scores vector search API"""
    pass


@cli.command()
@click.option("--query", required=True, help="Search query text")
@click.option("--limit", default=10, help="Number of results")
@click.option("--doc-type", help="Filter by document type")
@click.option("--format", type=click.Choice(["json", "table"]), default="table")
def search(query: str, limit: int, doc_type: Optional[str], format: str):
    """Perform vector search"""
    api = SumScoresAPI()

    if not api.connect():
        return

    # For demo purposes, we'll create a dummy query vector
    # In production, this would use the embedding model
    import random

    query_vector = [random.random() for _ in range(1536)]

    # Build filters
    filters = {}
    if doc_type:
        filters["document_type"] = doc_type

    # Search
    results = api.search_single(
        query_vector, limit=limit, filter_conditions=filters if filters else None
    )

    if format == "json":
        output = []
        for r in results:
            output.append(
                {
                    "document_id": r.document_id,
                    "title": r.title,
                    "type": r.document_type,
                    "score": r.final_score,
                    "decay_factor": r.decay_factor,
                    "boost_factor": r.boost_factor,
                }
            )
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\nSearch Results for: '{query}'")
        click.echo("=" * 80)
        for i, r in enumerate(results, 1):
            click.echo(f"\n{i}. {r.title}")
            click.echo(f"   ID: {r.document_id} | Type: {r.document_type}")
            click.echo(
                f"   Score: {r.final_score:.3f} (base: {r.score:.3f}, decay: {r.decay_factor:.2f}, boost: {r.boost_factor:.2f})"
            )
            click.echo(f"   Path: {r.file_path}")


@cli.command()
def stats():
    """Show search index statistics"""
    api = SumScoresAPI()

    if not api.connect():
        return

    stats = api.get_statistics()

    click.echo("\n=== Vector Search Statistics ===")
    click.echo(f"Total vectors: {stats.get('total_vectors', 0)}")
    click.echo(f"Vector size: {stats.get('vector_size', 0)}")
    click.echo(f"Distance metric: {stats.get('distance_metric', 'unknown')}")

    click.echo("\nDocument type distribution:")
    for doc_type, count in stats.get("document_types", {}).items():
        boost = stats.get("type_boosts", {}).get(doc_type, 1.0)
        click.echo(f"  {doc_type}: {count} (boost: {boost}x)")

    click.echo("\nDecay configuration:")
    decay = stats.get("decay_config", {})
    click.echo(f"  Decay starts after: {decay.get('decay_days', 0)} days")
    click.echo(f"  Decay rate: {decay.get('decay_rate', 0)*100}% per day")


if __name__ == "__main__":
    cli()
