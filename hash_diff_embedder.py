#!/usr/bin/env python3
"""
hash_diff_embedder.py: Smart embedding system with hash-based change detection

This component:
1. Tracks document hashes to detect changes
2. Only re-embeds changed content
3. Manages embedding cache efficiently
4. Provides incremental updates to Qdrant
"""

import hashlib
import json
import click
import yaml
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue


@dataclass
class DocumentHash:
    """Track document hashes and metadata"""
    document_id: str
    file_path: str
    content_hash: str
    embedding_hash: str
    last_embedded: str
    vector_id: str
    

class HashDiffEmbedder:
    """Smart embedder with hash-based change detection"""
    
    def __init__(self, config_path: str = ".ctxrc.yaml", verbose: bool = False):
        self.config = self._load_config(config_path)
        self.hash_cache_path = Path("context/.embeddings_cache/hash_cache.json")
        self.hash_cache: Dict[str, DocumentHash] = self._load_hash_cache()
        self.client = None
        self.embedding_model = self.config.get('qdrant', {}).get('embedding_model', 'text-embedding-ada-002')
        self.verbose = verbose
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from .ctxrc.yaml"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            click.echo(f"Error: {config_path} not found", err=True)
            return {}
            
    def _load_hash_cache(self) -> Dict[str, DocumentHash]:
        """Load hash cache from disk"""
        if self.hash_cache_path.exists():
            try:
                with open(self.hash_cache_path, 'r') as f:
                    cache_data = json.load(f)
                    return {
                        k: DocumentHash(**v) for k, v in cache_data.items()
                    }
            except Exception as e:
                click.echo(f"Warning: Failed to load hash cache: {e}")
        return {}
    
    def _save_hash_cache(self) -> None:
        """Save hash cache to disk"""
        self.hash_cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        cache_data = {
            k: asdict(v) for k, v in self.hash_cache.items()
        }
        
        with open(self.hash_cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _compute_embedding_hash(self, embedding: List[float]) -> str:
        """Compute hash of embedding vector"""
        # Convert to bytes and hash
        embedding_bytes = json.dumps(embedding, sort_keys=True).encode()
        return hashlib.sha256(embedding_bytes).hexdigest()
    
    def connect(self) -> bool:
        """Connect to Qdrant and OpenAI"""
        # Connect to Qdrant
        qdrant_config = self.config.get('qdrant', {})
        host = qdrant_config.get('host', 'localhost')
        port = qdrant_config.get('port', 6333)
        
        try:
            self.client = QdrantClient(host=host, port=port, timeout=5)
            self.client.get_collections()
            
            # Check OpenAI API key
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                click.echo("Error: OPENAI_API_KEY environment variable not set", err=True)
                return False
                
            # Test OpenAI connection with new client
            try:
                client = openai.OpenAI(api_key=api_key)
                # Quick test
                client.models.list()
            except Exception as e:
                click.echo(f"Failed to connect to OpenAI: {e}", err=True)
                return False
                
            return True
            
        except Exception as e:
            click.echo(f"Failed to connect: {e}", err=True)
            return False
    
    def needs_embedding(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Check if a document needs re-embedding"""
        try:
            # Read file content
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Compute content hash
            content_hash = self._compute_content_hash(content)
            
            # Check cache
            cache_key = str(file_path)
            if cache_key in self.hash_cache:
                cached = self.hash_cache[cache_key]
                if cached.content_hash == content_hash:
                    return False, cached.vector_id
            
            return True, None
            
        except Exception as e:
            click.echo(f"Error checking {file_path}: {e}", err=True)
            return False, None
    
    def embed_document(self, file_path: Path, force: bool = False) -> Optional[str]:
        """Embed a document and store in Qdrant"""
        needs_embed, existing_id = self.needs_embedding(file_path)
        
        if not needs_embed and not force:
            if self.verbose:
                click.echo(f"  Skipping {file_path} - no changes detected")
            return existing_id
        
        try:
            # Load document
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return None
            
            # Prepare content for embedding
            content_parts = []
            
            # Add main fields
            if 'title' in data:
                content_parts.append(f"Title: {data['title']}")
            if 'description' in data:
                content_parts.append(f"Description: {data['description']}")
            if 'content' in data:
                content_parts.append(f"Content: {data['content']}")
            if 'goals' in data:
                content_parts.append(f"Goals: {', '.join(data['goals'])}")
            
            # Combine content
            embedding_text = "\n\n".join(content_parts)
            
            # Generate embedding with retry logic
            if self.verbose:
                click.echo(f"  Embedding {file_path}...")
            
            max_retries = 3
            retry_delay = 1.0
            
            for attempt in range(max_retries):
                try:
                    # Use the new OpenAI client API
                    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                    response = client.embeddings.create(
                        model=self.embedding_model,
                        input=embedding_text
                    )
                    break
                except openai.RateLimitError as e:
                    if attempt < max_retries - 1:
                        if self.verbose:
                            click.echo(f"    Rate limit hit, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        raise e
            
            embedding = response.data[0].embedding
            embedding_hash = self._compute_embedding_hash(embedding)
            
            # Generate vector ID
            doc_id = data.get('id', file_path.stem)
            vector_id = f"{doc_id}-{embedding_hash[:8]}"
            
            # Prepare payload
            payload = {
                'document_id': doc_id,
                'document_type': data.get('document_type', 'unknown'),
                'file_path': str(file_path),
                'title': data.get('title', ''),
                'created_date': data.get('created_date', ''),
                'last_modified': data.get('last_modified', ''),
                'content_hash': self._compute_content_hash(yaml.dump(data)),
                'embedding_hash': embedding_hash,
                'embedded_at': datetime.now().isoformat(),
            }
            
            # Store in Qdrant
            collection_name = self.config.get('qdrant', {}).get('collection_name', 'project_context')
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=vector_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            # Update cache
            self.hash_cache[str(file_path)] = DocumentHash(
                document_id=doc_id,
                file_path=str(file_path),
                content_hash=payload['content_hash'],
                embedding_hash=embedding_hash,
                last_embedded=payload['embedded_at'],
                vector_id=vector_id
            )
            
            # Delete old version if exists
            if existing_id and existing_id != vector_id:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=[existing_id]
                )
            
            return vector_id
            
        except Exception as e:
            click.echo(f"Failed to embed {file_path}: {e}", err=True)
            return None
    
    def embed_directory(self, directory: Path, force: bool = False) -> Tuple[int, int]:
        """Recursively embed all YAML files in directory"""
        embedded_count = 0
        total_count = 0
        
        for yaml_file in directory.rglob("*.yaml"):
            # Skip schemas and other system files
            if any(skip in yaml_file.parts for skip in ['schemas', '.embeddings_cache', 'archive']):
                continue
            
            total_count += 1
            vector_id = self.embed_document(yaml_file, force=force)
            if vector_id:
                embedded_count += 1
        
        # Save cache after batch
        self._save_hash_cache()
        
        return embedded_count, total_count
    
    def cleanup_orphaned_vectors(self) -> int:
        """Remove vectors for documents that no longer exist"""
        collection_name = self.config.get('qdrant', {}).get('collection_name', 'project_context')
        removed_count = 0
        
        # Get all vectors from Qdrant
        try:
            # Scroll through all points
            points, _ = self.client.scroll(
                collection_name=collection_name,
                limit=1000,
                with_payload=True
            )
            
            for point in points:
                file_path = Path(point.payload.get('file_path', ''))
                
                # Check if file still exists
                if not file_path.exists():
                    if self.verbose:
                        click.echo(f"  Removing orphaned vector: {point.id}")
                    
                    self.client.delete(
                        collection_name=collection_name,
                        points_selector=[point.id]
                    )
                    removed_count += 1
                    
                    # Remove from cache
                    cache_key = str(file_path)
                    if cache_key in self.hash_cache:
                        del self.hash_cache[cache_key]
            
            if removed_count > 0:
                self._save_hash_cache()
                
        except Exception as e:
            click.echo(f"Error during cleanup: {e}", err=True)
        
        return removed_count
    


@click.command()
@click.argument('path', type=click.Path(exists=True), default='context')
@click.option('--force', is_flag=True, help='Force re-embedding of all documents')
@click.option('--cleanup', is_flag=True, help='Remove orphaned vectors')
@click.option('--verbose', is_flag=True, help='Show detailed output')
def main(path: str, force: bool, cleanup: bool, verbose: bool):
    """Smart document embedder with hash-based change detection"""
    embedder = HashDiffEmbedder(verbose=verbose)
    
    # Connect to services
    if not embedder.connect():
        click.echo("Failed to connect to required services")
        return
    
    click.echo("=== Hash-Diff Embedder ===\n")
    
    # Cleanup orphaned vectors if requested
    if cleanup:
        click.echo("Cleaning up orphaned vectors...")
        removed = embedder.cleanup_orphaned_vectors()
        click.echo(f"Removed {removed} orphaned vectors\n")
    
    # Embed documents
    path_obj = Path(path)
    if path_obj.is_file():
        vector_id = embedder.embed_document(path_obj, force=force)
        if vector_id:
            click.echo(f"✓ Embedded: {path_obj} -> {vector_id}")
        else:
            click.echo(f"✗ Failed to embed: {path_obj}")
    else:
        embedded, total = embedder.embed_directory(path_obj, force=force)
        click.echo(f"\nEmbedding Results:")
        click.echo(f"  Embedded: {embedded}/{total}")
        click.echo(f"  Skipped: {total - embedded} (no changes)")
    
    click.echo("\n✓ Embedding complete!")


if __name__ == "__main__":
    main()