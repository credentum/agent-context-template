#!/usr/bin/env python3
"""
neo4j_init.py: Initialize Neo4j graph database for the Agent-First Context System

This script:
1. Connects to Neo4j instance
2. Creates constraints and indexes
3. Sets up node labels and relationship types
4. Initializes the context graph schema
"""

import sys
import click
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError


class Neo4jInitializer:
    """Initialize and configure Neo4j graph database"""
    
    def __init__(self, config_path: str = ".ctxrc.yaml"):
        self.config = self._load_config(config_path)
        self.driver = None
        self.database = self.config.get('neo4j', {}).get('database', 'context_graph')
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from .ctxrc.yaml"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            click.echo(f"Error: {config_path} not found", err=True)
            sys.exit(1)
            
    def connect(self, username: str = "neo4j", password: Optional[str] = None) -> bool:
        """Connect to Neo4j instance"""
        neo4j_config = self.config.get('neo4j', {})
        host = neo4j_config.get('host', 'localhost')
        port = neo4j_config.get('port', 7687)
        
        uri = f"bolt://{host}:{port}"
        
        try:
            if not password:
                click.echo("Neo4j password required")
                import getpass
                password = getpass.getpass("Password: ")
            
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
                
            click.echo(f"✓ Connected to Neo4j at {uri}")
            return True
            
        except ServiceUnavailable:
            click.echo(f"✗ Neo4j is not available at {uri}", err=True)
            click.echo("Please ensure Neo4j is running:")
            click.echo("  docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5")
            return False
        except AuthError:
            click.echo("✗ Authentication failed", err=True)
            return False
        except Exception as e:
            click.echo(f"✗ Failed to connect: {e}", err=True)
            return False
    
    def create_constraints(self) -> bool:
        """Create uniqueness constraints for node types"""
        constraints = [
            # Document nodes
            ("Document", "id"),
            ("Design", "id"),
            ("Decision", "id"),
            ("Sprint", "id"),
            
            # System nodes
            ("Agent", "name"),
            ("Phase", "number"),
            ("Task", "id"),
            ("Metric", "name"),
            
            # Version tracking
            ("Version", "hash"),
        ]
        
        try:
            with self.driver.session(database=self.database) as session:
                for label, property in constraints:
                    query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{property} IS UNIQUE"
                    session.run(query)
                    click.echo(f"  Created constraint: {label}.{property}")
                    
            return True
        except Exception as e:
            click.echo(f"✗ Failed to create constraints: {e}", err=True)
            return False
    
    def create_indexes(self) -> bool:
        """Create indexes for common queries"""
        indexes = [
            # Document indexes
            ("Document", ["document_type", "created_date"]),
            ("Document", ["last_modified"]),
            ("Document", ["status"]),
            
            # Relationship traversal
            ("Sprint", ["sprint_number", "status"]),
            ("Task", ["status", "assigned_to"]),
            
            # Full-text search
            ("Document", ["title"], "fulltext"),
            ("Document", ["description"], "fulltext"),
        ]
        
        try:
            with self.driver.session(database=self.database) as session:
                for index_spec in indexes:
                    if len(index_spec) == 2:
                        label, properties = index_spec
                        index_type = "btree"
                    else:
                        label, properties, index_type = index_spec
                    
                    props_str = ", ".join([f"n.{p}" for p in properties])
                    index_name = f"idx_{label}_{'_'.join(properties)}"
                    
                    if index_type == "fulltext":
                        query = f"""
                        CALL db.index.fulltext.createNodeIndex(
                            '{index_name}',
                            ['{label}'],
                            {properties}
                        )
                        """
                    else:
                        query = f"CREATE INDEX {index_name} IF NOT EXISTS FOR (n:{label}) ON ({props_str})"
                    
                    try:
                        session.run(query)
                        click.echo(f"  Created index: {index_name}")
                    except Exception as e:
                        if "already exists" not in str(e):
                            click.echo(f"  Warning: {e}")
                            
            return True
        except Exception as e:
            click.echo(f"✗ Failed to create indexes: {e}", err=True)
            return False
    
    def setup_graph_schema(self) -> bool:
        """Initialize the graph schema with example relationships"""
        try:
            with self.driver.session(database=self.database) as session:
                # Create root System node
                session.run("""
                    MERGE (s:System {id: 'agent-context-system'})
                    SET s.name = 'Agent-First Context System',
                        s.version = $version,
                        s.created_date = $date
                """, version=self.config.get('system', {}).get('schema_version', '1.0.0'),
                     date=self.config.get('system', {}).get('created_date', '2025-07-11'))
                
                # Create agent nodes
                agents = [
                    ('code_agent', 'Code Agent', 'Primary implementation agent'),
                    ('doc_agent', 'Documentation Agent', 'Maintains documentation'),
                    ('pm_agent', 'Project Manager Agent', 'Manages sprints and tasks'),
                    ('ci_agent', 'CI/CD Agent', 'Handles testing and deployment'),
                ]
                
                for agent_id, name, description in agents:
                    session.run("""
                        MERGE (a:Agent {name: $name})
                        SET a.id = $id,
                            a.description = $description,
                            a.active = true
                    """, id=agent_id, name=name, description=description)
                
                # Link agents to system
                session.run("""
                    MATCH (s:System {id: 'agent-context-system'})
                    MATCH (a:Agent)
                    MERGE (s)-[:HAS_AGENT]->(a)
                """)
                
                # Create document type hierarchy
                doc_types = [
                    ('design', 'Design Document', 'DEFINES_ARCHITECTURE'),
                    ('decision', 'Decision Record', 'RECORDS_DECISION'),
                    ('sprint', 'Sprint Plan', 'TRACKS_PROGRESS'),
                ]
                
                for type_id, type_name, rel_type in doc_types:
                    session.run(f"""
                        MERGE (dt:DocumentType {{id: '{type_id}'}})
                        SET dt.name = '{type_name}'
                        WITH dt
                        MATCH (s:System {{id: 'agent-context-system'}})
                        MERGE (s)-[:{rel_type}]->(dt)
                    """)
                
                click.echo("✓ Graph schema initialized")
                return True
                
        except Exception as e:
            click.echo(f"✗ Failed to setup schema: {e}", err=True)
            return False
    
    def verify_setup(self) -> bool:
        """Verify the Neo4j setup"""
        try:
            with self.driver.session(database=self.database) as session:
                # Count nodes by label
                result = session.run("""
                    CALL db.labels() YIELD label
                    CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {})
                    YIELD value
                    RETURN label, value.count as count
                    ORDER BY label
                """)
                
                click.echo("\nNode counts by label:")
                for record in result:
                    click.echo(f"  {record['label']}: {record['count']}")
                
                # Count relationships
                result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as type, count(r) as count
                    ORDER BY type
                """)
                
                click.echo("\nRelationship counts by type:")
                for record in result:
                    click.echo(f"  {record['type']}: {record['count']}")
                    
                return True
                
        except Exception as e:
            # APOC might not be installed, try simpler query
            try:
                with self.driver.session(database=self.database) as session:
                    result = session.run("MATCH (n) RETURN count(n) as total")
                    total = result.single()['total']
                    click.echo(f"\nTotal nodes: {total}")
                    
                    result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
                    total = result.single()['total']
                    click.echo(f"Total relationships: {total}")
                    
                return True
            except Exception as e2:
                click.echo(f"✗ Failed to verify setup: {e2}", err=True)
                return False
    
    def close(self):
        """Close the driver connection"""
        if self.driver:
            self.driver.close()


@click.command()
@click.option('--username', default='neo4j', help='Neo4j username')
@click.option('--password', help='Neo4j password (will prompt if not provided)')
@click.option('--skip-constraints', is_flag=True, help='Skip constraint creation')
@click.option('--skip-indexes', is_flag=True, help='Skip index creation')
@click.option('--skip-schema', is_flag=True, help='Skip schema initialization')
def main(username: str, password: Optional[str], skip_constraints: bool, 
         skip_indexes: bool, skip_schema: bool):
    """Initialize Neo4j graph database for the Agent-First Context System"""
    
    click.echo("=== Neo4j Graph Database Initialization ===\n")
    
    initializer = Neo4jInitializer()
    
    try:
        # Connect to Neo4j
        if not initializer.connect(username=username, password=password):
            sys.exit(1)
        
        # Create database if needed
        with initializer.driver.session(database="system") as session:
            db_name = initializer.database
            result = session.run("SHOW DATABASES WHERE name = $name", name=db_name)
            if not result.single():
                click.echo(f"Creating database '{db_name}'...")
                session.run(f"CREATE DATABASE {db_name}")
        
        # Create constraints
        if not skip_constraints:
            click.echo("\nCreating constraints...")
            if not initializer.create_constraints():
                sys.exit(1)
        
        # Create indexes
        if not skip_indexes:
            click.echo("\nCreating indexes...")
            if not initializer.create_indexes():
                sys.exit(1)
        
        # Setup schema
        if not skip_schema:
            click.echo("\nSetting up graph schema...")
            if not initializer.setup_graph_schema():
                sys.exit(1)
        
        # Verify
        click.echo("\nVerifying setup...")
        initializer.verify_setup()
        
        click.echo("\n✓ Neo4j initialization complete!")
        
    finally:
        initializer.close()


if __name__ == "__main__":
    main()