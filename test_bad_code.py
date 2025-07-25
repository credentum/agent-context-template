"""Test file with intentional issues for ARC reviewer to catch"""

def bad_function():
    """Function with multiple issues"""
    # No type hints
    # Poor variable naming
    x = 1
    y = 2
    z = x + y
    
    # No error handling
    result = 10 / 0  # Division by zero
    
    # Hardcoded values
    api_key = "sk-1234567890abcdef"  # Security issue!
    
    # No return type
    return z

# Missing tests
# No docstrings for parameters
# Coverage would be 0%