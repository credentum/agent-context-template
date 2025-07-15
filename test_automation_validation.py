#!/usr/bin/env python3
"""
Test file designed to trigger ARC-Reviewer automation issues.
This file intentionally contains issues that Claude should flag.
"""

import sys

import requests

# ISSUE 1: Hard-coded API key (security issue)
API_KEY = "sk-test-12345-hardcoded-key-never-do-this"


# ISSUE 2: Missing type hints
def process_data(data):
    # ISSUE 3: No docstring
    result = []
    for item in data:
        # ISSUE 4: Potential security issue - eval usage
        processed = eval(f"'{item}'.upper()")
        result.append(processed)
    return result


# ISSUE 5: Missing error handling
def fetch_external_data(url):
    response = requests.get(url)
    return response.json()


# ISSUE 6: No input validation
def divide_numbers(a, b):
    return a / b  # Division by zero risk


class DataProcessor:
    # ISSUE 7: Missing constructor

    # ISSUE 8: Method without type hints or docstring
    def transform(self, input_data):
        # ISSUE 9: Hardcoded file path
        with open("/tmp/hardcoded_path.txt", "w") as f:
            f.write(str(input_data))

        # ISSUE 10: SQL injection vulnerability simulation
        query = f"SELECT * FROM users WHERE name = '{input_data}'"
        return query


if __name__ == "__main__":
    # ISSUE 11: No command line argument validation
    data = sys.argv[1]
    processor = DataProcessor()
    result = processor.transform(data)
    print(result)
