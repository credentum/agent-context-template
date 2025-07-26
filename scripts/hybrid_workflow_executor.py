#!/usr/bin/env python3
"""
Hybrid Workflow Executor - Enhances WorkflowExecutor with specialist sub-agents.

This module provides a hybrid approach that combines the persistence and orchestration
capabilities of WorkflowExecutor with the analytical expertise of specialist sub-agents.
Sub-agents act as consultants providing insights without handling any persistence.
"""

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import Any, Dict

import yaml
from workflow_executor import WorkflowExecutor


class HybridWorkflowExecutor(WorkflowExecutor):
    """Enhances WorkflowExecutor with specialist sub-agent consultants."""

    def __init__(self, issue_number: int, enable_specialists: bool = True):
        """
        Initialize hybrid executor.

        Args:
            issue_number: GitHub issue number
            enable_specialists: Whether to use specialist sub-agents (default: True)
        """
        super().__init__(issue_number)
        self.enable_specialists = enable_specialists
        self.specialist_timeout = 300  # 5 minutes max per specialist
        self.parallel_limit = 3  # Max parallel specialists
        self._load_specialist_config()

    def _load_specialist_config(self) -> None:
        """Load specialist agent configuration."""
        config_path = Path(".claude/config/specialist-agents.yaml")

        # Default specialist configuration
        default_config = {
            "investigation": {
                "agents": ["issue-investigator"],
                "threshold": "complex",
                "parallel": False,
            },
            "planning": {
                "agents": ["general-purpose"],
                "threshold": "large_codebase",
                "parallel": False,
            },
            "validation": {
                "agents": ["test-runner", "security-analyzer"],
                "threshold": "always",
                "parallel": True,
            },
        }

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    full_config = yaml.safe_load(f)
                    self.specialist_config = full_config.get("specialist_agents", default_config)
                    self.global_config = full_config.get("global_settings", {})
                    print(f"  📋 Loaded specialist configuration from {config_path}")
            except Exception as e:
                print(f"  ⚠️  Failed to load specialist config: {e}")
                self.specialist_config = default_config
                self.global_config = {}
        else:
            self.specialist_config = default_config
            self.global_config = {}

    def execute_investigation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute investigation phase with optional specialist consultation."""
        print("🔍 Executing investigation phase (hybrid mode)...")

        # Check if we should use specialist
        if self.enable_specialists and self._should_use_specialist("investigation", context):
            print("  🤖 Consulting issue-investigator specialist...")
            try:
                specialist_insights = self._consult_specialist(
                    agent_type="issue-investigator",
                    prompt=self._build_investigation_prompt(context),
                    context=context,
                )
                if specialist_insights:
                    print("  ✅ Specialist provided additional insights")
                    # Merge insights into context
                    context.update(specialist_insights)
            except Exception as e:
                print(f"  ⚠️  Specialist consultation failed: {e}")
                print("  📌 Continuing with basic investigation...")

        # Base class handles actual investigation and persistence
        return super().execute_investigation(context)

    def execute_planning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planning phase with optional codebase research."""
        print("📝 Executing planning phase (hybrid mode)...")

        # Check if we should use specialist for codebase research
        if self.enable_specialists and self._should_use_specialist("planning", context):
            print("  🤖 Consulting general-purpose agent for codebase research...")
            try:
                research_prompt = self._build_research_prompt(context)
                research_insights = self._consult_specialist(
                    agent_type="general-purpose",
                    prompt=research_prompt,
                    context=context,
                )
                if research_insights:
                    print("  ✅ Specialist found relevant patterns and files")
                    context["codebase_insights"] = research_insights
            except Exception as e:
                print(f"  ⚠️  Research specialist failed: {e}")
                print("  📌 Continuing with standard planning...")

        # Base class handles actual planning and persistence
        return super().execute_planning(context)

    def execute_validation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation phase with parallel specialist validation."""
        print("🧪 Executing validation phase (hybrid mode)...")

        # Run base validation first
        base_results = super().execute_validation(context)

        # Enhance with specialist validation if enabled
        if self.enable_specialists and self._should_use_specialist("validation", context):
            print("  🤖 Running parallel specialist validation...")
            try:
                specialist_results = self._parallel_specialist_validation(context)
                if specialist_results:
                    print("  ✅ Specialists completed additional validation")
                    # Merge specialist results
                    base_results["specialist_validation"] = specialist_results
                    # Update overall validation status based on specialists
                    if any(r.get("issues_found") for r in specialist_results.values()):
                        base_results["quality_checks_passed"] = False
                        print("  ⚠️  Specialists found issues requiring attention")
            except Exception as e:
                print(f"  ⚠️  Specialist validation failed: {e}")
                print("  📌 Using base validation results only")

        return base_results

    def _should_use_specialist(self, phase: str, context: Dict[str, Any]) -> bool:
        """Determine if specialist should be used for this phase."""
        if not self.enable_specialists:
            return False

        config = self.specialist_config.get(phase, {})
        threshold = config.get("threshold", "never")

        if threshold == "always":
            return True
        elif threshold == "never":
            return False
        elif threshold == "complex":
            # Check if issue indicates complexity
            return context.get("complexity", "medium") in ["high", "complex"]
        elif threshold == "large_codebase":
            # Check if many files are involved
            return context.get("files_affected", 0) > 10

        return False

    def _consult_specialist(
        self, agent_type: str, prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Consult a specialist sub-agent for insights.

        Args:
            agent_type: Type of specialist agent
            prompt: Prompt for the specialist
            context: Current execution context

        Returns:
            Insights from the specialist (not persisted state)
        """
        # In a real implementation, this would use the Task tool
        # For now, we'll simulate the specialist consultation
        print(f"    📤 Sending request to {agent_type}...")

        # Simulate specialist execution with timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._simulate_specialist, agent_type, prompt, context)
            try:
                result = future.result(timeout=self.specialist_timeout)
                return result
            except TimeoutError:
                print(f"    ⏱️  Specialist {agent_type} timed out")
                return {}

    def _simulate_specialist(
        self, agent_type: str, prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate specialist agent execution."""
        # In production, this would use the Task tool to delegate to actual agents
        # For demonstration, we'll return meaningful insights

        time.sleep(1)  # Simulate processing time

        if agent_type == "issue-investigator":
            return {
                "root_cause_analysis": {
                    "complexity": "medium-high",
                    "key_components": ["workflow_executor.py", "hybrid_workflow_executor.py"],
                    "potential_risks": ["State persistence during parallel execution"],
                    "recommended_approach": "Inheritance pattern with graceful fallback",
                }
            }
        elif agent_type == "general-purpose":
            return {
                "relevant_patterns": ["WorkflowExecutor inheritance", "Task tool usage"],
                "similar_implementations": ["workflow_cli.py delegation pattern"],
                "suggested_structure": "Override specific phase methods, call super()",
            }
        elif agent_type == "test-runner":
            return {
                "test_coverage": "73.5%",
                "new_tests_needed": [
                    "test_hybrid_specialist_integration",
                    "test_parallel_execution",
                ],
                "edge_cases": ["Specialist timeout handling", "Fallback behavior"],
            }
        elif agent_type == "security-analyzer":
            return {"security_issues": [], "best_practices_followed": True, "issues_found": False}

        return {}

    def _parallel_specialist_validation(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Run multiple validation specialists in parallel."""
        config = self.specialist_config.get("validation", {})
        agents = config.get("agents", [])

        if not agents:
            return {}

        results = {}
        with ThreadPoolExecutor(max_workers=min(len(agents), self.parallel_limit)) as executor:
            # Submit all specialist tasks
            futures = {}
            for agent in agents:
                prompt = self._build_validation_prompt(agent, context)
                future = executor.submit(self._consult_specialist, agent, prompt, context)
                futures[future] = agent

            # Collect results with timeout
            for future in futures:
                agent = futures[future]
                try:
                    result = future.result(timeout=self.specialist_timeout)
                    results[agent] = result
                    print(f"    ✅ {agent} completed")
                except Exception as e:
                    print(f"    ❌ {agent} failed: {e}")
                    results[agent] = {"error": str(e)}

        return results

    def _build_investigation_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for investigation specialist."""
        issue_number = context.get("issue_number", "unknown")
        return f"""Analyze GitHub issue #{issue_number} for root cause and complexity.

Provide insights on:
1. Root cause analysis
2. Component dependencies
3. Implementation complexity
4. Potential risks
5. Recommended approach

Focus on technical analysis without implementing solutions."""

    def _build_research_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for codebase research specialist."""
        issue_number = context.get("issue_number", "unknown")
        return f"""Research the codebase for patterns relevant to issue #{issue_number}.

Find and analyze:
1. Similar implementations or patterns
2. Relevant files and components
3. Best practices from existing code
4. Potential integration points

Return file paths and patterns, not implementations."""

    def _build_validation_prompt(self, agent_type: str, context: Dict[str, Any]) -> str:
        """Build prompt for validation specialist."""
        if agent_type == "test-runner":
            return """Analyze the test coverage and identify:
1. Missing test cases
2. Edge cases to consider
3. Integration test requirements
4. Performance test needs

Focus on test strategy, not implementation."""

        elif agent_type == "security-analyzer":
            return """Perform security analysis on the changes:
1. Check for security vulnerabilities
2. Validate authentication/authorization
3. Review data handling practices
4. Identify potential attack vectors

Report findings without fixing issues."""

        return "Perform validation analysis"

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get statistics about the hybrid execution."""
        stats = {
            "hybrid_mode": self.enable_specialists,
            "specialists_consulted": getattr(self, "_specialists_used", 0),
            "specialist_failures": getattr(self, "_specialist_failures", 0),
            "parallel_executions": getattr(self, "_parallel_runs", 0),
        }
        return stats
