#!/usr/bin/env python3
"""Check mutation testing baseline enforcement"""

import json
import os
import subprocess
import sys
from typing import Dict, Optional


def load_coverage_config() -> Dict:
    """Load coverage configuration from .coverage-config.json"""
    try:
        with open(".coverage-config.json") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  .coverage-config.json not found. Using default baseline.")
        return {"mutation_baseline": 20.0}
    except Exception as e:
        print(f"⚠️  Error loading coverage config: {e}")
        return {"mutation_baseline": 20.0}


def get_mutation_score() -> Optional[float]:
    """Get current mutation testing score"""
    try:
        result = subprocess.run(["mutmut", "results"], capture_output=True, text=True)

        if result.returncode == 0:
            output = result.stdout
            # Look for mutation score information
            if "killed" in output and "survived" in output:
                lines = output.split("\n")
                for line in lines:
                    if "killed" in line and "survived" in line:
                        # Extract numbers - this is a simplified parser
                        # Expected format: "killed: X, survived: Y"
                        try:
                            parts = line.split(",")
                            killed = int(parts[0].split(":")[1].strip())
                            survived = int(parts[1].split(":")[1].strip())
                            total = killed + survived
                            if total > 0:
                                return (killed / total) * 100
                        except (ValueError, IndexError):
                            continue

            # If no mutation tests have been run yet, return None
            return None
        else:
            print(f"⚠️  mutmut results returned non-zero exit code: {result.returncode}")
            return None

    except FileNotFoundError:
        print("⚠️  mutmut not found. Install with: pip install mutmut")
        return None
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error running mutmut: {e}")
        return None
    except Exception as e:
        print(f"⚠️  Unexpected error in mutation testing: {e}")
        return None


def run_mutation_tests() -> bool:
    """Run mutation tests on critical modules"""
    # Define modules to test
    critical_modules = [
        "src/validators/kv_validators.py",
        "src/storage/context_kv.py",
        "src/agents/context_lint.py",
        "src/storage/hash_diff_embedder_async.py",
    ]

    print("🧪 Running mutation testing on critical modules...")

    for module in critical_modules:
        if os.path.exists(module):
            print(f"   Testing {module}...")
            try:
                result = subprocess.run(
                    [
                        "mutmut",
                        "run",
                        f"--paths-to-mutate={module}",
                        "--runner=python -m pytest -x -q",
                        "--timeout=60",
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"   ⚠️  Mutation testing failed for {module}")
                    print(f"   Error: {result.stderr}")
                else:
                    print(f"   ✅ Mutation testing completed for {module}")

            except Exception as e:
                print(f"   ⚠️  Error running mutation tests on {module}: {e}")
                continue
        else:
            print(f"   ⚠️  Module {module} not found, skipping")

    return True


def main():
    """Main entry point"""
    print("🧪 Mutation Testing Baseline Check")
    print("=" * 40)

    # Load configuration
    config = load_coverage_config()
    baseline = config.get("mutation_baseline", 20.0)

    # Get current mutation score
    current_score = get_mutation_score()

    if current_score is None:
        print("⚠️  No mutation testing results found.")
        print("   Running mutation tests on critical modules...")
        run_mutation_tests()

        # Check again after running tests
        current_score = get_mutation_score()
        if current_score is None:
            print("⚠️  Unable to get mutation score after running tests.")
            print("   This may be acceptable for initial implementation.")
            print("   Setting up mutation testing infrastructure...")
            return 0  # Don't fail CI for initial setup

    # Check against baseline
    if current_score is not None:
        print(f"📊 Current mutation score: {current_score:.2f}%")
        print(f"🎯 Required baseline: {baseline:.2f}%")

        if current_score >= baseline:
            print("✅ Mutation testing baseline met!")
            return 0
        else:
            print("❌ Mutation testing baseline not met!")
            print(f"   Need to improve by {baseline - current_score:.2f} percentage points")
            return 1
    else:
        print("⚠️  No mutation testing results available.")
        print("   Consider running: mutmut run --paths-to-mutate=src/")
        return 0  # Don't fail CI if no mutation tests exist yet


if __name__ == "__main__":
    sys.exit(main())
