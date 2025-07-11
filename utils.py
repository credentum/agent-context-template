#!/usr/bin/env python3
"""
utils.py: Common utility functions for the Agent-First Context System
"""

import re
from typing import Optional, List


def sanitize_error_message(error_msg: str, sensitive_values: Optional[List[str]] = None) -> str:
    """
    Sanitize error messages to remove sensitive information
    
    Args:
        error_msg: The error message to sanitize
        sensitive_values: List of sensitive values to remove (passwords, tokens, etc.)
    
    Returns:
        Sanitized error message
    """
    if not sensitive_values:
        return error_msg
    
    sanitized = error_msg
    
    for value in sensitive_values:
        if not value:
            continue
            
        # Don't sanitize very short values to avoid breaking messages
        if len(value) < 3:
            continue
        
        # Replace the value with asterisks
        # Use word boundaries to avoid partial replacements
        pattern = re.escape(value)
        sanitized = re.sub(pattern, "***", sanitized)
        
        # Also sanitize URL-encoded versions
        import urllib.parse
        encoded_value = urllib.parse.quote(value)
        if encoded_value != value:
            sanitized = re.sub(re.escape(encoded_value), "***", sanitized)
    
    # Remove connection strings that might contain passwords
    # Match patterns like username:password@host
    sanitized = re.sub(r'://[^:]+:[^@]+@', '://***:***@', sanitized)
    
    # Remove auth headers
    sanitized = re.sub(r'(authorization|auth|password|api[_-]key)[\'":\s]+[^\s\'"]+', r'\1: ***', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def get_secure_connection_config(config: dict, service: str) -> dict:
    """
    Get secure connection configuration with SSL/TLS options
    
    Args:
        config: Configuration dictionary
        service: Service name ('neo4j' or 'qdrant')
    
    Returns:
        Connection configuration with security options
    """
    service_config = config.get(service, {})
    
    # Default to secure connections in production
    default_ssl = service_config.get('environment', 'development') == 'production'
    
    secure_config = {
        'host': service_config.get('host', 'localhost'),
        'port': service_config.get('port'),
        'ssl': service_config.get('ssl', default_ssl),
        'verify_ssl': service_config.get('verify_ssl', True),
        'timeout': service_config.get('timeout', 30),
    }
    
    # Add SSL certificate paths if provided
    if service_config.get('ssl_cert_path'):
        secure_config['ssl_cert_path'] = service_config['ssl_cert_path']
    if service_config.get('ssl_key_path'):
        secure_config['ssl_key_path'] = service_config['ssl_key_path']
    if service_config.get('ssl_ca_path'):
        secure_config['ssl_ca_path'] = service_config['ssl_ca_path']
    
    return secure_config