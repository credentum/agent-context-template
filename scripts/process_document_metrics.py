#!/usr/bin/env python3
"""
Process document metrics for KV store
Used by GitHub Actions workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
from pathlib import Path
from datetime import datetime
from context_kv import ContextKV, MetricEvent


def process_file(file_path: str, kv: ContextKV) -> bool:
    """Process a single YAML file and record metrics"""
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data or not isinstance(data, dict):
            return False
            
        doc_id = data.get('id', Path(file_path).stem)
        doc_type = data.get('document_type', 'unknown')
        
        # Record document access
        metric = MetricEvent(
            timestamp=datetime.utcnow(),
            metric_name='document.accessed',
            value=1.0,
            tags={'type': doc_type, 'source': 'workflow'},
            document_id=doc_id
        )
        
        # Record in both stores
        redis_success = kv.redis.record_metric(metric)
        duckdb_success = kv.duckdb.insert_metrics([metric])
        
        if redis_success and duckdb_success:
            print(f"✓ Processed {file_path} (ID: {doc_id}, Type: {doc_type})")
            return True
        else:
            print(f"✗ Failed to record metrics for {file_path}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}", file=sys.stderr)
        return False


def main():
    """Process all document metrics"""
    if len(sys.argv) < 2:
        print("Usage: process_document_metrics.py <yaml_file> ...", file=sys.stderr)
        return 1
    
    kv = ContextKV()
    if not kv.connect():
        print("✗ Failed to connect to KV store", file=sys.stderr)
        return 1
    
    try:
        success_count = 0
        total_count = len(sys.argv) - 1
        
        for file_path in sys.argv[1:]:
            if process_file(file_path, kv):
                success_count += 1
        
        print(f"\nProcessed {success_count}/{total_count} files successfully")
        return 0 if success_count == total_count else 1
        
    finally:
        kv.close()


if __name__ == "__main__":
    sys.exit(main())