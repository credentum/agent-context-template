# This file intentionally has formatting issues for testing claude-post-edit.sh
# flake8: noqa - This file is meant to have issues for testing purposes
import json
import os
import sys
from typing import Dict, List, Optional


# Bad spacing and line length
def badly_formatted_function(x, y, z):
    """This is a function with poor formatting that should trigger multiple formatters including Black for spacing issues and line length violations"""
    result = x + y * z  # No spaces around operators
    return result


import asyncio

# Import order issues
from pathlib import Path


class PoorlyFormattedClass:
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value

    def calculate(self, multiplier):
        # Flake8 should catch unused variable
        unused_variable = 42
        return self.value * multiplier

    # Line too long
    def very_long_method_name_that_exceeds_the_maximum_line_length_limit_and_should_be_flagged_by_black_formatter(
        self,
    ):
        pass


# Missing type hints
def function_without_type_hints(param1, param2):
    return param1 + param2
