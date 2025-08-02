"""Utility helper functions."""


def get_greeting(name: str) -> str:
    """Generate a greeting message for the given name.
    
    Args:
        name: The name to include in the greeting
        
    Returns:
        A greeting string in the format "Hello, {name}!"
    """
    return f"Hello, {name}!"