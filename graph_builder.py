#!/usr/bin/env python3
"""
graph_builder.py: Build and maintain the context graph from YAML documents

This component:
1. Parses YAML documents and extracts entities
2. Creates nodes and relationships in Neo4j
3. Maintains graph consistency
4. Provides graph update operations
"""

import click
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
import hashlib
import json
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


class GraphBuilder:
    """Build and maintain context graph from documents"""
    
    def __init__(self, config_path: str = ".ctxrc.yaml", verbose: bool = False):
        self.config = self._load_config(config_path)
        self.driver = None
        self.database = self.config.get('neo4j', {}).get('database', 'context_graph')
        self.verbose = verbose
        self.processed_cache_path = Path("context/.graph_cache/processed.json")
        self.processed_docs: Dict[str, str] = self._load_processed_cache()
    
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
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return {}
    
    def _load_processed_cache(self) -> Dict[str, str]:
        """Load cache of processed documents"""
        if self.processed_cache_path.exists():
            try:
                with open(self.processed_cache_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_processed_cache(self):
        """Save cache of processed documents"""
        self.processed_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.processed_cache_path, 'w') as f:
            json.dump(self.processed_docs, f, indent=2)
    
    def _compute_doc_hash(self, data: Dict[str, Any]) -> str:
        """Compute hash of document content"""
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def connect(self, username: str = "neo4j", password: Optional[str] = None) -> bool:
        """Connect to Neo4j"""
        neo4j_config = self.config.get('neo4j', {})
        host = neo4j_config.get('host', 'localhost')
        port = neo4j_config.get('port', 7687)
        
        uri = f"bolt://{host}:{port}"
        
        if not password:
            if self.verbose:
                click.echo("Error: Neo4j password is required", err=True)
            return False
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            # Import locally to avoid circular imports
            from utils import sanitize_error_message
            error_msg = sanitize_error_message(str(e), [password, username])
            if self.verbose:
                click.echo(f"Failed to connect to Neo4j: {error_msg}", err=True)
            return False
    
    def _create_document_node(self, session, data: Dict[str, Any], file_path: Path) -> str:
        """Create or update a document node"""
        doc_type = data.get('document_type', 'document')
        doc_id = data.get('id', file_path.stem)
        
        # Base properties
        props = {
            'id': doc_id,
            'document_type': doc_type,
            'file_path': str(file_path),
            'title': data.get('title', ''),
            'created_date': data.get('created_date', ''),
            'last_modified': data.get('last_modified', ''),
            'status': data.get('status', 'active'),
            'hash': self._compute_doc_hash(data),
        }
        
        # Type-specific properties
        if doc_type == 'sprint':
            props.update({
                'sprint_number': data.get('sprint_number', 0),
                'start_date': data.get('start_date', ''),
                'end_date': data.get('end_date', ''),
            })
        elif doc_type == 'decision':
            props.update({
                'decision_date': data.get('decision_date', ''),
                'status': data.get('status', 'active'),
            })
        
        # Create node with multiple labels
        labels = ['Document', doc_type.capitalize()]
        labels_str = ':'.join(labels)
        
        query = f"""
        MERGE (d:{labels_str} {{id: $id}})
        SET d += $props
        RETURN d
        """
        
        result = session.run(query, id=doc_id, props=props)
        return doc_id
    
    def _create_relationships(self, session, data: Dict[str, Any], doc_id: str):
        """Create relationships based on document content"""
        doc_type = data.get('document_type')
        
        # Sprint relationships
        if doc_type == 'sprint':
            # Link to phases
            phases = data.get('phases', [])
            for phase in phases:
                phase_num = phase.get('phase')
                if phase_num is not None:
                    session.run("""
                        MATCH (s:Sprint {id: $sprint_id})
                        MERGE (p:Phase {number: $phase_num})
                        ON CREATE SET p.name = $name, p.duration_days = $duration
                        MERGE (s)-[:HAS_PHASE {status: $status}]->(p)
                    """, sprint_id=doc_id, phase_num=phase_num,
                         name=phase.get('name', ''), 
                         duration=phase.get('duration_days', 0),
                         status=phase.get('status', 'pending'))
                    
                    # Link tasks to phases
                    tasks = phase.get('tasks', [])
                    for i, task in enumerate(tasks):
                        task_id = f"{doc_id}-phase{phase_num}-task{i}"
                        session.run("""
                            MATCH (p:Phase {number: $phase_num})
                            MERGE (t:Task {id: $task_id})
                            SET t.description = $description,
                                t.status = $status,
                                t.phase = $phase_num
                            MERGE (p)-[:HAS_TASK]->(t)
                        """, phase_num=phase_num, task_id=task_id,
                             description=task, status='pending')
            
            # Link to team members
            team = data.get('team', [])
            for member in team:
                agent = member.get('agent')
                if agent:
                    session.run("""
                        MATCH (s:Sprint {id: $sprint_id})
                        MATCH (a:Agent {name: $agent})
                        MERGE (s)-[:HAS_TEAM_MEMBER {role: $role}]->(a)
                    """, sprint_id=doc_id, agent=agent, role=member.get('role', ''))
        
        # Decision relationships
        elif doc_type == 'decision':
            # Link alternatives
            alternatives = data.get('alternatives_considered', {})
            for alt_name, alt_desc in alternatives.items():
                session.run("""
                    MATCH (d:Decision {id: $decision_id})
                    MERGE (a:Alternative {name: $name})
                    SET a.description = $description
                    MERGE (d)-[:CONSIDERED]->(a)
                """, decision_id=doc_id, name=alt_name, description=alt_desc)
            
            # Link related decisions
            related = data.get('related_decisions', [])
            for related_id in related:
                session.run("""
                    MATCH (d1:Decision {id: $decision_id})
                    MATCH (d2:Decision {id: $related_id})
                    MERGE (d1)-[:RELATES_TO]->(d2)
                """, decision_id=doc_id, related_id=related_id)
        
        # Graph metadata relationships
        graph_meta = data.get('graph_metadata', {})
        if graph_meta:
            relationships = graph_meta.get('relationships', [])
            for rel in relationships:
                rel_type = rel.get('type', 'RELATES_TO')
                target = rel.get('target')
                if target:
                    session.run(f"""
                        MATCH (d1:Document {{id: $source_id}})
                        MATCH (d2:Document {{id: $target_id}})
                        MERGE (d1)-[:{rel_type}]->(d2)
                    """, source_id=doc_id, target_id=target)
    
    def _extract_references(self, content: str) -> Set[str]:
        """Extract document references from content"""
        import re
        references = set()
        
        # Look for patterns like [[doc-id]] or @doc-id
        patterns = [
            r'\[\[([a-zA-Z0-9\-_]+)\]\]',  # [[doc-id]]
            r'@([a-zA-Z0-9\-_]+)',          # @doc-id
            r'#([a-zA-Z0-9\-_]+)',          # #doc-id
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            references.update(matches)
        
        return references
    
    def process_document(self, file_path: Path, force: bool = False) -> bool:
        """Process a single document and update graph"""
        try:
            # Load document
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return False
            
            # Check if needs processing
            doc_hash = self._compute_doc_hash(data)
            cache_key = str(file_path)
            
            if not force and cache_key in self.processed_docs:
                if self.processed_docs[cache_key] == doc_hash:
                    if self.verbose:
                        click.echo(f"  Skipping {file_path} - no changes")
                    return True
            
            # Process in transaction
            with self.driver.session(database=self.database) as session:
                # Create/update document node
                doc_id = self._create_document_node(session, data, file_path)
                
                # Create relationships
                self._create_relationships(session, data, doc_id)
                
                # Extract and link references from content
                content_fields = ['description', 'content', 'rationale']
                all_content = ' '.join(str(data.get(f, '')) for f in content_fields)
                
                references = self._extract_references(all_content)
                for ref_id in references:
                    session.run("""
                        MATCH (d1:Document {id: $source_id})
                        MATCH (d2:Document {id: $target_id})
                        MERGE (d1)-[:REFERENCES]->(d2)
                    """, source_id=doc_id, target_id=ref_id)
                
                # Create timeline relationships
                if 'created_date' in data:
                    session.run("""
                        MATCH (d:Document {id: $doc_id})
                        MERGE (t:Timeline {date: $date})
                        MERGE (d)-[:CREATED_ON]->(t)
                    """, doc_id=doc_id, date=data['created_date'])
            
            # Update cache
            self.processed_docs[cache_key] = doc_hash
            
            if self.verbose:
                click.echo(f"  ✓ Processed {file_path}")
            
            return True
            
        except Exception as e:
            click.echo(f"  ✗ Failed to process {file_path}: {e}", err=True)
            return False
    
    def process_directory(self, directory: Path, force: bool = False) -> Tuple[int, int]:
        """Process all documents in directory"""
        processed = 0
        total = 0
        
        for yaml_file in directory.rglob("*.yaml"):
            # Skip system files
            if any(skip in yaml_file.parts for skip in ['schemas', '.graph_cache', 'archive']):
                continue
            
            total += 1
            if self.process_document(yaml_file, force=force):
                processed += 1
        
        # Save cache
        self._save_processed_cache()
        
        return processed, total
    
    def cleanup_orphaned_nodes(self) -> int:
        """Remove nodes for documents that no longer exist"""
        removed = 0
        
        try:
            with self.driver.session(database=self.database) as session:
                # Get all document nodes
                result = session.run("""
                    MATCH (d:Document)
                    RETURN d.id as id, d.file_path as file_path
                """)
                
                for record in result:
                    file_path = Path(record['file_path'])
                    if not file_path.exists():
                        # Delete node and relationships
                        session.run("""
                            MATCH (d:Document {id: $id})
                            DETACH DELETE d
                        """, id=record['id'])
                        
                        removed += 1
                        
                        # Remove from cache
                        cache_key = str(file_path)
                        if cache_key in self.processed_docs:
                            del self.processed_docs[cache_key]
                        
                        if self.verbose:
                            click.echo(f"  Removed orphaned node: {record['id']}")
            
            if removed > 0:
                self._save_processed_cache()
                
        except Exception as e:
            click.echo(f"Error during cleanup: {e}", err=True)
        
        return removed
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        stats = {}
        
        try:
            with self.driver.session(database=self.database) as session:
                # Node counts by label
                result = session.run("""
                    MATCH (n)
                    UNWIND labels(n) as label
                    RETURN label, count(*) as count
                    ORDER BY count DESC
                """)
                
                label_counts = {}
                for record in result:
                    label_counts[record['label']] = record['count']
                stats['node_counts'] = label_counts
                
                # Relationship counts
                result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as type, count(*) as count
                    ORDER BY count DESC
                """)
                
                rel_counts = {}
                for record in result:
                    rel_counts[record['type']] = record['count']
                stats['relationship_counts'] = rel_counts
                
                # Document statistics
                result = session.run("""
                    MATCH (d:Document)
                    RETURN d.document_type as type, count(*) as count
                    ORDER BY count DESC
                """)
                
                doc_counts = {}
                for record in result:
                    doc_counts[record['type']] = record['count']
                stats['document_types'] = doc_counts
                
        except Exception as e:
            stats['error'] = str(e)
        
        return stats
    
    def close(self):
        """Close driver connection"""
        if self.driver:
            self.driver.close()


@click.command()
@click.argument('path', type=click.Path(exists=True), default='context')
@click.option('--username', default='neo4j', help='Neo4j username')
@click.option('--password', help='Neo4j password (required)', required=True)
@click.option('--force', is_flag=True, help='Force reprocessing of all documents')
@click.option('--cleanup', is_flag=True, help='Remove orphaned nodes')
@click.option('--stats', is_flag=True, help='Show graph statistics')
@click.option('--verbose', is_flag=True, help='Show detailed output')
def main(path: str, username: str, password: str, force: bool, 
         cleanup: bool, stats: bool, verbose: bool):
    """Build and maintain context graph from YAML documents"""
    
    builder = GraphBuilder(verbose=verbose)
    
    # Connect to Neo4j
    if not builder.connect(username=username, password=password):
        click.echo("Failed to connect to Neo4j")
        click.echo("Ensure Neo4j is running with:")
        click.echo("  docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5")
        return
    
    try:
        click.echo("=== Context Graph Builder ===\n")
        
        # Cleanup if requested
        if cleanup:
            click.echo("Cleaning up orphaned nodes...")
            removed = builder.cleanup_orphaned_nodes()
            click.echo(f"Removed {removed} orphaned nodes\n")
        
        # Show statistics if requested
        if stats:
            stats_data = builder.get_statistics()
            click.echo("Graph Statistics:")
            click.echo("-" * 40)
            
            click.echo("\nNode counts by label:")
            for label, count in stats_data.get('node_counts', {}).items():
                click.echo(f"  {label}: {count}")
            
            click.echo("\nRelationship counts:")
            for rel_type, count in stats_data.get('relationship_counts', {}).items():
                click.echo(f"  {rel_type}: {count}")
            
            click.echo("\nDocument types:")
            for doc_type, count in stats_data.get('document_types', {}).items():
                click.echo(f"  {doc_type}: {count}")
            
            return
        
        # Process documents
        path_obj = Path(path)
        if path_obj.is_file():
            success = builder.process_document(path_obj, force=force)
            click.echo(f"\n{'✓' if success else '✗'} Processed: {path_obj}")
        else:
            processed, total = builder.process_directory(path_obj, force=force)
            click.echo(f"\nProcessing Results:")
            click.echo(f"  Processed: {processed}/{total}")
            click.echo(f"  Skipped: {total - processed}")
        
        click.echo("\n✓ Graph building complete!")
        
    finally:
        builder.close()


if __name__ == "__main__":
    main()