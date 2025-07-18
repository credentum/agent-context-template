# AI-Monitored PR Process - Production Monitoring & Metrics Plan

**Issue**: #173 - Replace brittle multi-workflow automation with AI-monitored PR process
**Date**: 2025-07-17
**Phase**: 4 - Production Migration
**Purpose**: Define comprehensive monitoring strategy for validating migration success

## 🎯 Success Metrics Overview

### **Primary Success Criteria**

| Metric Category | Legacy Baseline | Target Improvement | Measurement Method |
|----------------|-----------------|-------------------|-------------------|
| **Response Time** | 30 minutes (polling) | <2 minutes (real-time) | Workflow execution logs |
| **Reliability** | ~85% success rate | >95% success rate | PR completion tracking |
| **Code Complexity** | 2,063 lines (5 workflows) | 589 lines (1 workflow) | Static analysis |
| **Maintenance Burden** | Multi-workflow coordination | Single workflow management | Developer survey |
| **Error Recovery** | Manual intervention | Intelligent fallbacks | Incident tracking |

### **Quantitative Metrics**

#### **Performance Metrics**
```yaml
response_time_metrics:
  pr_opened_to_first_response:
    legacy: "~30 minutes (first polling cycle)"
    target: "<30 seconds (event-driven)"
    measurement: "GitHub Actions workflow logs"

  ci_completion_to_auto_merge:
    legacy: "~30 minutes (next polling cycle)"
    target: "<60 seconds (real-time processing)"
    measurement: "Auto-merge enablement timestamps"

  conflict_detection_to_resolution:
    legacy: "Manual detection, hours to resolve"
    target: "<5 minutes (automated branch updating)"
    measurement: "Conflict resolution workflow logs"

reliability_metrics:
  auto_merge_success_rate:
    legacy: "~85% (coordination failures)"
    target: ">95% (intelligent fallbacks)"
    measurement: "PR completion vs auto-merge request ratio"

  workflow_execution_success:
    legacy: "~90% (multi-workflow coordination issues)"
    target: ">98% (single workflow reliability)"
    measurement: "GitHub Actions success/failure rates"

  error_recovery_rate:
    legacy: "~60% (manual intervention required)"
    target: ">90% (intelligent fallbacks + clear guidance)"
    measurement: "Automated resolution vs manual intervention ratio"
```

#### **Complexity Reduction Metrics**
```yaml
code_metrics:
  total_workflow_lines:
    before: 2063
    after: 589
    reduction: "71%"

  workflow_count_auto_merge:
    before: 5
    after: 1
    reduction: "80%"

  coordination_points:
    before: "15+ (inter-workflow dependencies)"
    after: "1 (single intelligent agent)"
    reduction: "93%"

maintainability_metrics:
  debugging_complexity:
    before: "Scattered logs across 5 workflows"
    after: "Unified logging in single workflow"
    measurement: "Developer feedback survey"

  feature_addition_time:
    before: "Multi-workflow coordination required"
    after: "Single workflow modification"
    measurement: "Development time tracking"
```

## 📊 Monitoring Implementation

### **Phase 1: Real-Time Workflow Monitoring**

#### **GitHub Actions Metrics Collection**
```bash
# Workflow success rate tracking
gh api /repos/$REPO/actions/workflows/ai-pr-monitor.yml/runs \
  --jq '.workflow_runs[] | {id, status, conclusion, created_at, updated_at}'

# Compare with legacy workflow historical data
gh api /repos/$REPO/actions/workflows/auto-merge.yml/runs \
  --jq '.workflow_runs[] | {id, status, conclusion, created_at, updated_at}'
```

#### **Custom Metrics Collection Script**
```python
#!/usr/bin/env python3
"""
AI PR Monitor Metrics Collector

Tracks success metrics for AI-monitored PR process migration.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List

import requests


class AIPRMonitorMetrics:
    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = f"https://api.github.com/repos/{repo}"

    def collect_workflow_metrics(self, workflow_file: str, days: int = 7) -> Dict:
        """Collect workflow execution metrics for specified timeframe"""
        since = (datetime.now() - timedelta(days=days)).isoformat()

        url = f"{self.base_url}/actions/workflows/{workflow_file}/runs"
        params = {"created": f">{since}", "per_page": 100}

        response = requests.get(url, headers=self.headers, params=params)
        runs = response.json().get("workflow_runs", [])

        total_runs = len(runs)
        successful_runs = len([r for r in runs if r["conclusion"] == "success"])
        failed_runs = len([r for r in runs if r["conclusion"] == "failure"])

        # Calculate average execution time
        execution_times = []
        for run in runs:
            if run["updated_at"] and run["created_at"]:
                start = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                execution_times.append((end - start).total_seconds())

        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        return {
            "workflow": workflow_file,
            "period_days": days,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": successful_runs / total_runs if total_runs > 0 else 0,
            "avg_execution_time_seconds": avg_execution_time,
            "collected_at": datetime.now().isoformat()
        }

    def collect_pr_metrics(self, days: int = 7) -> Dict:
        """Collect PR processing metrics"""
        since = (datetime.now() - timedelta(days=days)).isoformat()

        # Get PRs from timeframe
        url = f"{self.base_url}/pulls"
        params = {"state": "all", "sort": "updated", "direction": "desc", "per_page": 100}

        response = requests.get(url, headers=self.headers, params=params)
        prs = response.json()

        # Filter PRs within timeframe
        recent_prs = [
            pr for pr in prs
            if pr["updated_at"] > since
        ]

        auto_merge_requested = 0
        auto_merge_successful = 0

        for pr in recent_prs:
            # Check for auto-merge indicators
            has_auto_merge = (
                pr["body"] and ("auto-merge" in pr["body"].lower() or "auto_merge" in pr["body"]) or
                any(label["name"] == "auto-merge" for label in pr.get("labels", []))
            )

            if has_auto_merge:
                auto_merge_requested += 1
                if pr["merged"]:
                    auto_merge_successful += 1

        return {
            "period_days": days,
            "total_prs": len(recent_prs),
            "auto_merge_requested": auto_merge_requested,
            "auto_merge_successful": auto_merge_successful,
            "auto_merge_success_rate": auto_merge_successful / auto_merge_requested if auto_merge_requested > 0 else 0,
            "collected_at": datetime.now().isoformat()
        }

    def generate_report(self) -> Dict:
        """Generate comprehensive metrics report"""
        return {
            "ai_pr_monitor": self.collect_workflow_metrics("ai-pr-monitor.yml"),
            "legacy_auto_merge": self.collect_workflow_metrics("auto-merge.yml"),
            "pr_processing": self.collect_pr_metrics(),
            "report_generated_at": datetime.now().isoformat()
        }


if __name__ == "__main__":
    import os

    repo = os.getenv("GITHUB_REPOSITORY", "your-org/your-repo")
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("Error: GITHUB_TOKEN environment variable required")
        exit(1)

    collector = AIPRMonitorMetrics(repo, token)
    report = collector.generate_report()

    print(json.dumps(report, indent=2))
```

### **Phase 2: Developer Experience Monitoring**

#### **Developer Feedback Survey**
```yaml
survey_questions:
  pr_workflow_experience:
    - "How would you rate the new AI-monitored PR process vs the old system? (1-10)"
    - "How quickly do you get feedback on PR status? (Much faster/Faster/Same/Slower)"
    - "How clear are error messages when auto-merge fails? (Very clear/Clear/Unclear/Very unclear)"
    - "How easy is it to debug issues with the new workflow? (Much easier/Easier/Same/Harder)"

  reliability_perception:
    - "How often does auto-merge work when expected? (Always/Usually/Sometimes/Rarely)"
    - "How confident are you in the new system's reliability? (Very confident/Confident/Uncertain/Not confident)"
    - "Have you experienced fewer workflow coordination issues? (Yes/No/Unsure)"

  productivity_impact:
    - "Has the new workflow improved your development productivity? (Significantly/Somewhat/No change/Worsened)"
    - "Do you spend less time managing PR automation? (Much less/Less/Same/More)"
    - "Would you recommend keeping the new system? (Definitely/Probably/Maybe/No)"
```

#### **Automated Developer Experience Metrics**
```bash
# Track comment response times
gh api /repos/$REPO/issues/comments --jq '
  .[] | select(.body | contains("@claude")) |
  {comment_id, created_at, user: .user.login}'

# Track issue resolution times
gh api /repos/$REPO/issues --jq '
  .[] | select(.state == "closed" and (.labels[] | .name == "ai-pr-monitor")) |
  {issue_id, created_at, closed_at, resolution_time: (.closed_at | strptime("%Y-%m-%dT%H:%M:%SZ") | mktime) - (.created_at | strptime("%Y-%m-%dT%H:%M:%SZ") | mktime)}'
```

### **Phase 3: Error and Incident Tracking**

#### **Error Classification System**
```yaml
error_categories:
  ai_workflow_errors:
    - "Claude API rate limiting"
    - "YAML parsing failures"
    - "GitHub API integration issues"
    - "Workflow syntax errors"

  pr_processing_errors:
    - "Auto-merge condition failures"
    - "CI status detection issues"
    - "ARC-Reviewer integration failures"
    - "Conflict resolution failures"

  coordination_errors:
    - "Event trigger misses"
    - "Status update delays"
    - "Notification delivery failures"
    - "Permission/authentication issues"

error_tracking_metrics:
  error_frequency:
    measurement: "Errors per day/week"
    target: "<5 errors per week"

  error_resolution_time:
    measurement: "Time from error detection to resolution"
    target: "<2 hours for critical, <24 hours for non-critical"

  error_recurrence_rate:
    measurement: "Percentage of errors that reoccur"
    target: "<10% recurrence rate"
```

#### **Incident Response Plan**
```markdown
## Incident Response Levels

### **Level 1: Critical (Auto-merge completely broken)**
- **Response Time**: <30 minutes
- **Action**: Immediate rollback to legacy workflows
- **Escalation**: Team lead + immediate investigation
- **Communication**: Team notification + status page update

### **Level 2: Major (Degraded auto-merge functionality)**
- **Response Time**: <2 hours
- **Action**: Investigate + apply hotfix if possible
- **Escalation**: Scheduled rollback if not resolved in 4 hours
- **Communication**: Team notification

### **Level 3: Minor (Individual PR issues)**
- **Response Time**: <24 hours
- **Action**: Manual intervention + investigate root cause
- **Escalation**: Document issue for next sprint
- **Communication**: Internal tracking only
```

## 📈 Success Validation Timeline

### **Week 1: Baseline Establishment**
- [ ] Deploy ai-pr-monitor.yml to production
- [ ] Begin parallel monitoring with legacy workflows
- [ ] Collect initial performance metrics
- [ ] Document any immediate issues

### **Week 2: Performance Validation**
- [ ] Compare response times vs legacy system
- [ ] Validate reliability improvements
- [ ] Conduct developer feedback survey (initial)
- [ ] Identify any performance regressions

### **Week 3: Reliability Assessment**
- [ ] Analyze error rates and resolution effectiveness
- [ ] Validate intelligent fallback mechanisms
- [ ] Test edge cases and failure scenarios
- [ ] Document system behavior patterns

### **Week 4: Migration Decision**
- [ ] Compile comprehensive metrics report
- [ ] Conduct final developer feedback survey
- [ ] Make go/no-go decision for legacy workflow deprecation
- [ ] Plan either full migration or rollback

## 🎯 Success Thresholds

### **Go/No-Go Criteria for Legacy Deprecation**

#### **Must-Have (Hard Requirements):**
- ✅ **Response time**: <2 minutes average (vs 30-minute legacy)
- ✅ **Success rate**: >95% auto-merge success (vs ~85% legacy)
- ✅ **Error recovery**: >90% automated resolution (vs ~60% legacy)
- ✅ **Zero critical incidents**: No Level 1 incidents during validation period

#### **Should-Have (Strong Preferences):**
- ✅ **Developer satisfaction**: >80% positive feedback
- ✅ **Debugging improvement**: Faster issue resolution reported
- ✅ **Maintenance reduction**: Lower operational overhead
- ✅ **Feature development**: Easier to add new functionality

#### **Nice-to-Have (Additional Benefits):**
- ✅ **Cost reduction**: Lower GitHub Actions usage
- ✅ **Code quality**: Fewer workflow-related bugs
- ✅ **Team confidence**: High confidence in system reliability
- ✅ **Future readiness**: Foundation for additional AI automation

---

**Implementation**: Deploy metrics collection immediately upon production rollout to ensure comprehensive validation of migration success.
