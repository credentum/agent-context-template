#!/usr/bin/env python3
"""
graphrag_integration.py: GraphRAG integration for enhanced context retrieval

This component:
1. Combines vector search with graph traversal
2. Implements GraphRAG patterns for context enhancement
3. Provides multi-hop reasoning capabilities
4. Generates contextual summaries from graph neighborhoods
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import click
import openai
import yaml
from neo4j import Driver, GraphDatabase
from qdrant_client import QdrantClient


@dataclass
class GraphRAGResult:
    """Enhanced search result combining vector and graph data"""

    query: str
    vector_results: List[Dict[str, Any]]
    graph_context: Dict[str, Any]
    combined_score: float
    reasoning_path: List[str]
    summary: str
    related_nodes: List[Dict[str, Any]]


class GraphRAGIntegration:
    """GraphRAG integration for enhanced context retrieval"""

    def __init__(self, config_path: str = ".ctxrc.yaml", verbose: bool = False):
        self.config = self._load_config(config_path)
        self.neo4j_driver: Optional[Driver] = None
        self.qdrant_client: Optional[QdrantClient] = None
        self.verbose = verbose
        self.database = self.config.get("neo4j", {}).get("database", "context_graph")
        self.collection_name = self.config.get("qdrant", {}).get(
            "collection_name", "project_context"
        )

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup"""
        try:
            self.close()
        except Exception as e:
            # Log the error but don't raise to avoid masking the original exception
            if self.verbose:
                click.echo(f"Error during cleanup: {e}", err=True)

        # Return False to propagate any exception that occurred in the with block
        return False

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from .ctxrc.yaml"""
        try:
            with open(config_path, "r") as f:
                result = yaml.safe_load(f)
                return cast(Dict[str, Any], result) if result else {}
        except FileNotFoundError:
            return {}

    def connect(self, neo4j_username: str = "neo4j", neo4j_password: Optional[str] = None) -> bool:
        """Connect to Neo4j and Qdrant"""
        # Connect to Neo4j
        neo4j_config = self.config.get("neo4j", {})
        neo4j_host = neo4j_config.get("host", "localhost")
        neo4j_port = neo4j_config.get("port", 7687)
        neo4j_uri = f"bolt://{neo4j_host}:{neo4j_port}"

        if not neo4j_password:
            click.echo("Error: Neo4j password is required", err=True)
            return False

        try:
            self.neo4j_driver = GraphDatabase.driver(
                neo4j_uri, auth=(neo4j_username, neo4j_password)
            )
            if self.neo4j_driver is not None:
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")
        except Exception as e:
            # Import locally to avoid circular imports
            from src.core.utils import sanitize_error_message

            error_msg = sanitize_error_message(str(e), [neo4j_password, neo4j_username])
            click.echo(f"Failed to connect to Neo4j: {error_msg}", err=True)
            return False

        # Connect to Qdrant
        qdrant_config = self.config.get("qdrant", {})
        qdrant_host = qdrant_config.get("host", "localhost")
        qdrant_port = qdrant_config.get("port", 6333)

        try:
            self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
            if self.qdrant_client is not None:
                self.qdrant_client.get_collections()
        except Exception as e:
            click.echo(f"Failed to connect to Qdrant: {e}", err=True)
            return False

        return True

    def _vector_search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Perform vector search in Qdrant"""
        try:
            if self.qdrant_client is None:
                return []
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
            )

            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "document_id": r.payload.get("document_id", "") if r.payload else "",
                    "document_type": r.payload.get("document_type", "") if r.payload else "",
                    "title": r.payload.get("title", "") if r.payload else "",
                    "file_path": r.payload.get("file_path", "") if r.payload else "",
                    "payload": r.payload if r.payload else {},
                }
                for r in results
            ]
        except Exception as e:
            if self.verbose:
                click.echo(f"Vector search error: {e}", err=True)
            return []

    def _graph_neighborhood(self, document_ids: List[str], max_hops: int = 2) -> Dict[str, Any]:
        """Get graph neighborhood for documents"""
        neighborhood: Dict[str, Any] = {"nodes": {}, "relationships": [], "paths": []}

        try:
            if self.neo4j_driver is None:
                return neighborhood
            with self.neo4j_driver.session(database=self.database) as session:
                # Get direct neighbors
                for doc_id in document_ids:
                    # Get node and its relationships up to max_hops with early termination
                    # Try APOC first for better performance, fallback to standard query
                    try:
                        query = """
                        MATCH (d:Document {id: $doc_id})
                        CALL apoc.path.expandConfig(d, {
                            maxLevel: $max_hops,
                            uniqueness: 'NODE_GLOBAL',
                            limit: 50,
                            relationshipFilter: 'REFERENCES|IMPLEMENTS|RELATES_TO|DEPENDS_ON'
                        }) YIELD path
                        WITH path, d, last(nodes(path)) as connected, relationships(path) as rels
                        WHERE connected:Document
                        RETURN
                            d as source,
                            connected as target,
                            [r in rels | {type: type(r), properties: properties(r)}] as relationships,
                            length(path) as distance
                        ORDER BY distance
                        """
                        result = session.run(query, doc_id=doc_id, max_hops=max_hops)
                    except Exception:
                        # Fallback to standard Cypher without APOC
                        query = """
                        MATCH path = (d:Document {id: $doc_id})-[r:REFERENCES|IMPLEMENTS|RELATES_TO|DEPENDS_ON*1..2]-(connected:Document)
                        WITH d, connected, path, relationships(path) as rels,
                             length(path) as distance
                        WHERE distance <= $max_hops
                        RETURN
                            d as source,
                            connected as target,
                            [r in rels | {type: type(r), properties: properties(r)}] as relationships,
                            distance
                        ORDER BY distance
                        LIMIT 50
                        """
                        result = session.run(query, doc_id=doc_id, max_hops=max_hops)

                    for record in result:
                        # Add source node
                        source = record["source"]
                        source_id = source["id"]
                        if source_id not in neighborhood["nodes"]:
                            neighborhood["nodes"][source_id] = dict(source)

                        # Add target node
                        target = record["target"]
                        target_id = target.get("id", str(target.id))
                        if target_id not in neighborhood["nodes"]:
                            neighborhood["nodes"][target_id] = dict(target)

                        # Add relationships
                        for rel in record["relationships"]:
                            neighborhood["relationships"].append(
                                {
                                    "source": source_id,
                                    "target": target_id,
                                    "type": rel["type"],
                                    "properties": rel.get("properties", {}),
                                }
                            )

                # Get common patterns
                if len(document_ids) > 1:
                    pattern_query = """
                    MATCH (d1:Document {id: $id1})
                    MATCH (d2:Document {id: $id2})
                    MATCH path = shortestPath((d1)-[*..5]-(d2))
                    RETURN path, length(path) as distance
                    """

                    for i in range(len(document_ids)):
                        for j in range(i + 1, len(document_ids)):
                            result = session.run(
                                pattern_query, id1=document_ids[i], id2=document_ids[j]
                            )

                            for record in result:
                                path = record["path"]
                                nodes = [n["id"] for n in path.nodes]
                                neighborhood["paths"].append(
                                    {"nodes": nodes, "distance": record["distance"]}
                                )

        except Exception as e:
            if self.verbose:
                click.echo(f"Graph traversal error: {e}", err=True)

        return neighborhood

    def _extract_reasoning_path(self, neighborhood: Dict[str, Any]) -> List[str]:
        """Extract reasoning path from graph neighborhood"""
        reasoning = []

        # Analyze node types
        node_types: Dict[str, int] = {}
        for node_id, node in neighborhood["nodes"].items():
            doc_type = node.get("document_type", "unknown")
            node_types[doc_type] = node_types.get(doc_type, 0) + 1

        if node_types:
            reasoning.append(
                f"Found {sum(node_types.values())} related documents: "
                + ", ".join(f"{count} {t}" for t, count in node_types.items())
            )

        # Analyze relationships
        rel_types: Dict[str, int] = {}
        for rel in neighborhood["relationships"]:
            rel_type = rel["type"]
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1

        if rel_types:
            reasoning.append(
                "Relationships: " + ", ".join(f"{count} {t}" for t, count in rel_types.items())
            )

        # Analyze paths
        if neighborhood["paths"]:
            avg_distance = sum(p["distance"] for p in neighborhood["paths"]) / len(
                neighborhood["paths"]
            )
            reasoning.append(f"Average connection distance: {avg_distance:.1f} hops")

        return reasoning

    def _generate_summary(
        self, query: str, vector_results: List[Dict[str, Any]], neighborhood: Dict[str, Any]
    ) -> str:
        """Generate contextual summary using LLM"""
        # Build context from results
        context_parts = [f"Query: {query}\n"]

        # Add vector search results
        context_parts.append("Vector Search Results:")
        for i, result in enumerate(vector_results[:3], 1):
            context_parts.append(
                f"{i}. {result['title']} ({result['document_type']}) - Score: {result['score']:.3f}"
            )

        # Add graph context
        context_parts.append("\nGraph Context:")
        for node_id, node in list(neighborhood["nodes"].items())[:5]:
            title = node.get("title", node_id)
            doc_type = node.get("document_type", "unknown")
            context_parts.append(f"- {title} ({doc_type}) [ID: {node_id}]")

        # Add relationships
        unique_rels = set()
        for rel in neighborhood["relationships"][:10]:
            source = neighborhood["nodes"].get(rel["source"], {})
            target = neighborhood["nodes"].get(rel["target"], {})
            if source.get("title") and target.get("title"):
                unique_rels.add(f"{source['title']} --{rel['type']}--> {target['title']}")

        if unique_rels:
            context_parts.append("\nKey Relationships:")
            for rel in list(unique_rels)[:5]:
                context_parts.append(f"- {rel}")

        # For now, return a structured summary
        # In production, this would call an LLM
        summary = "\n".join(context_parts)
        return summary

    def search(
        self, query: str, query_vector: List[float], max_hops: int = 2, top_k: int = 5
    ) -> GraphRAGResult:
        """Perform GraphRAG search combining vector and graph retrieval"""

        # Step 1: Vector search
        vector_results = self._vector_search(query_vector, limit=top_k)

        # Step 2: Extract document IDs from vector results
        doc_ids = [r["document_id"] for r in vector_results if r["document_id"]]

        # Step 3: Get graph neighborhood
        neighborhood = self._graph_neighborhood(doc_ids, max_hops=max_hops)

        # Step 4: Extract reasoning path
        reasoning_path = self._extract_reasoning_path(neighborhood)

        # Step 5: Calculate combined scores
        # Combine vector similarity with graph centrality
        combined_scores = {}
        for result in vector_results:
            doc_id = result["document_id"]
            vector_score = result["score"]

            # Simple graph centrality: count of connections
            graph_score: float = 0.0
            for rel in neighborhood["relationships"]:
                if rel["source"] == doc_id or rel["target"] == doc_id:
                    graph_score += 0.1

            combined_scores[doc_id] = vector_score * 0.7 + min(graph_score, 0.3)

        # Step 6: Generate summary
        summary = self._generate_summary(query, vector_results, neighborhood)

        # Step 7: Get related nodes for expansion
        related_nodes = []
        seen_ids = set(doc_ids)

        for node_id, node in neighborhood["nodes"].items():
            if node_id not in seen_ids and node.get("title"):
                related_nodes.append(
                    {
                        "id": node_id,
                        "title": node["title"],
                        "type": node.get("document_type", "unknown"),
                        "relevance": "graph_neighbor",
                    }
                )
                seen_ids.add(node_id)

                if len(related_nodes) >= 5:
                    break

        # Calculate final combined score
        avg_combined_score = (
            sum(combined_scores.values()) / len(combined_scores) if combined_scores else 0
        )

        return GraphRAGResult(
            query=query,
            vector_results=vector_results,
            graph_context=neighborhood,
            combined_score=avg_combined_score,
            reasoning_path=reasoning_path,
            summary=summary,
            related_nodes=related_nodes,
        )

    def analyze_document_impact(self, document_id: str) -> Dict[str, Any]:
        """Analyze the impact and connections of a specific document"""
        impact = {
            "document_id": document_id,
            "direct_connections": 0,
            "total_reachable": 0,
            "dependency_chain": [],
            "impacted_documents": [],
            "central_score": 0.0,
        }

        try:
            if self.neo4j_driver is None:
                return impact
            with self.neo4j_driver.session(database=self.database) as session:
                # Get direct connections
                result = session.run(
                    """
                    MATCH (d:Document {id: $doc_id})-[r]-(connected)
                    RETURN count(DISTINCT connected) as direct_count,
                           collect(DISTINCT {
                               id: connected.id,
                               type: connected.document_type,
                               relationship: type(r)
                           }) as connections
                """,
                    doc_id=document_id,
                )

                record = result.single()
                if record:
                    impact["direct_connections"] = record["direct_count"]
                    impact["impacted_documents"] = record["connections"]

                # Get reachability (up to 3 hops)
                result = session.run(
                    """
                    MATCH (d:Document {id: $doc_id})-[*1..3]-(reachable:Document)
                    RETURN count(DISTINCT reachable) as total
                """,
                    doc_id=document_id,
                )

                record = result.single()
                if record:
                    impact["total_reachable"] = record["total"]

                # Calculate centrality score
                total_reachable = impact.get("total_reachable", 0)
                direct_connections = impact.get("direct_connections", 0)
                if (
                    isinstance(total_reachable, int)
                    and isinstance(direct_connections, int)
                    and total_reachable > 0
                ):
                    impact["central_score"] = direct_connections / total_reachable

                # Get dependency chain (documents that depend on this one)
                result = session.run(
                    """
                    MATCH (d:Document {id: $doc_id})<-[:DEPENDS_ON|IMPLEMENTS|REFERENCES*1..3]-(dependent:Document)
                    RETURN DISTINCT dependent.id as id, dependent.title as title
                    LIMIT 10
                """,
                    doc_id=document_id,
                )

                for record in result:
                    dependency_chain = impact.get("dependency_chain", [])
                    if isinstance(dependency_chain, list):
                        dependency_chain.append({"id": record["id"], "title": record["title"]})
                        impact["dependency_chain"] = dependency_chain

        except Exception as e:
            impact["error"] = str(e)

        return impact

    def close(self):
        """Close connections"""
        exceptions = []

        # Close Neo4j
        if self.neo4j_driver:
            try:
                self.neo4j_driver.close()
            except Exception as e:
                exceptions.append(f"Neo4j close error: {e}")
            finally:
                self.neo4j_driver = None

        # Close Qdrant if needed (currently using stateless client)
        # In future, if we use persistent connections, close here

        # If there were exceptions, log them
        if exceptions and self.verbose:
            for exc in exceptions:
                click.echo(f"Cleanup error: {exc}", err=True)


@click.group()
def cli():
    """GraphRAG integration for enhanced context retrieval"""
    pass


@cli.command()
@click.option("--query", required=True, help="Search query")
@click.option("--max-hops", default=2, help="Maximum graph traversal hops")
@click.option("--top-k", default=5, help="Number of results")
@click.option("--neo4j-user", default="neo4j", help="Neo4j username")
@click.option("--neo4j-pass", help="Neo4j password (required)", required=True)
@click.option("--verbose", is_flag=True, help="Verbose output")
def search(query: str, max_hops: int, top_k: int, neo4j_user: str, neo4j_pass: str, verbose: bool):
    """Perform GraphRAG search"""
    graphrag = GraphRAGIntegration(verbose=verbose)

    if not graphrag.connect(neo4j_username=neo4j_user, neo4j_password=neo4j_pass):
        click.echo("Failed to connect to services", err=True)
        return

    try:
        # For demo, create random query vector
        # In production, this would use the embedding model
        import random

        query_vector = [random.random() for _ in range(1536)]

        # Perform search
        result = graphrag.search(query, query_vector, max_hops=max_hops, top_k=top_k)

        # Display results
        click.echo(f"\n=== GraphRAG Search Results ===")
        click.echo(f"Query: {result.query}")
        click.echo(f"Combined Score: {result.combined_score:.3f}")

        click.echo("\nReasoning Path:")
        for step in result.reasoning_path:
            click.echo(f"  - {step}")

        click.echo("\nSummary:")
        click.echo(result.summary)

        if result.related_nodes:
            click.echo("\nRelated Documents (for exploration):")
            for node in result.related_nodes:
                click.echo(f"  - {node['title']} ({node['type']})")

    finally:
        graphrag.close()


@cli.command()
@click.option("--document-id", required=True, help="Document ID to analyze")
@click.option("--neo4j-user", default="neo4j", help="Neo4j username")
@click.option("--neo4j-pass", help="Neo4j password (required)", required=True)
def analyze(document_id: str, neo4j_user: str, neo4j_pass: str):
    """Analyze document impact in the graph"""
    graphrag = GraphRAGIntegration()

    if not graphrag.connect(neo4j_username=neo4j_user, neo4j_password=neo4j_pass):
        click.echo("Failed to connect to services", err=True)
        return

    try:
        impact = graphrag.analyze_document_impact(document_id)

        click.echo(f"\n=== Document Impact Analysis ===")
        click.echo(f"Document ID: {impact['document_id']}")
        click.echo(f"Direct Connections: {impact['direct_connections']}")
        click.echo(f"Total Reachable: {impact['total_reachable']}")
        click.echo(f"Centrality Score: {impact['central_score']:.3f}")

        if impact["impacted_documents"]:
            click.echo("\nDirectly Connected Documents:")
            for doc in impact["impacted_documents"][:10]:
                click.echo(f"  - {doc['id']} ({doc['type']}) via {doc['relationship']}")

        if impact["dependency_chain"]:
            click.echo("\nDocuments that depend on this:")
            for doc in impact["dependency_chain"]:
                click.echo(f"  - {doc['title']} ({doc['id']})")

    finally:
        graphrag.close()


if __name__ == "__main__":
    cli()
