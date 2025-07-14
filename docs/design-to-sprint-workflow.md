# Design → Decisions → Sprints Workflow Guide

This guide documents the complete workflow from high-level system design through architectural decisions to actionable sprint implementation in the Agent-First Project Context System.

## Table of Contents

1. [Workflow Overview](#workflow-overview)
2. [Phase 1: Design Documents](#phase-1-design-documents)
3. [Phase 2: Decision Records](#phase-2-decision-records)
4. [Phase 3: Sprint Planning](#phase-3-sprint-planning)
5. [Automation & Tools](#automation--tools)
6. [Relationship Mapping](#relationship-mapping)
7. [Feedback Loops](#feedback-loops)
8. [Agent Workflows](#agent-workflows)
9. [Best Practices](#best-practices)

## Workflow Overview

The system follows a **structured progression** from abstract concepts to concrete implementation:

```
Design Documents → Architectural Decisions → Sprint Planning → GitHub Issues → Implementation
       ↓                    ↓                      ↓              ↓              ↓
  High-level arch      Technology choices     Detailed tasks   Work tracking   Code changes
  System components    Constraints/impacts    Team assignments  Progress       Pull requests
```

### Flow Characteristics

- **Implicit Connections**: Documents reference each other via graph metadata
- **Automated Validation**: Schema compliance and cross-reference checking
- **Bidirectional Sync**: Changes flow both up and down the hierarchy
- **Agent Integration**: AI agents can understand and act on any level

## Phase 1: Design Documents

### Location & Schema
- **Directory**: `context/design/`
- **Schema**: `context/schemas/design.yaml`
- **Purpose**: High-level system architecture and design specifications

### Structure Example

```yaml
# context/design/001-system-architecture.yaml
schema_version: 1.0.0
document_type: design
id: system-architecture-v1
title: "Agent-First Context System Architecture"
status: approved
created_date: '2025-07-11'

overview: |
  Comprehensive system for managing AI agent context with vector search,
  graph relationships, and automated workflow integration.

components:
  context_store:
    description: "Centralized YAML-based context management"
    responsibilities:
      - "Schema validation and enforcement"
      - "Document lifecycle management"
      - "Cross-reference integrity"

  vector_database:
    description: "Qdrant-based semantic search"
    responsibilities:
      - "Embedding storage and retrieval"
      - "Similarity search operations"
      - "Vector-based context ranking"

# References to other system parts
references:
  - type: config
    path: ".ctxrc.yaml"
    description: "Main configuration file"

  - type: implementation
    path: "src/core/"
    description: "Core system components"

# Graph relationships
graph_metadata:
  node_type: design_document
  relationships:
    - type: defines
      target: system_components
    - type: requires
      target: infrastructure_decisions
```

### Creating Design Documents

```bash
# 1. Copy design template
cp context/schemas/design.yaml context/design/002-new-feature.yaml

# 2. Edit with your design
vim context/design/002-new-feature.yaml

# 3. Validate schema compliance
python -m src.agents.context_lint validate context/design/ --verbose

# 4. Commit to trigger graph updates
git add context/design/002-new-feature.yaml
git commit -m "docs(design): add new feature architecture"
```

## Phase 2: Decision Records

### Location & Schema
- **Directory**: `context/decisions/`
- **Schema**: `context/schemas/decision.yaml`
- **Purpose**: Architectural Decision Records (ADRs) documenting technology choices

### Structure Example

```yaml
# context/decisions/001-technology-stack.yaml
schema_version: 1.0.0
document_type: decision
id: technology-stack-v1
title: "Core Technology Stack Selection"
status: accepted
decision_date: '2025-07-11'

context: |
  Need to select primary technologies for vector storage, graph database,
  and key-value caching based on design requirements.

decision: |
  Selected Qdrant for vectors, Neo4j for graphs, Redis for caching.

alternatives_considered:
  - alternative: "Pinecone for vector storage"
    pros: ["Managed service", "Easy scaling"]
    cons: ["Vendor lock-in", "Cost at scale"]
    reason_rejected: "Need self-hosted solution for data sovereignty"

  - alternative: "Weaviate for vector storage"
    pros: ["Open source", "GraphQL API"]
    cons: ["Less mature", "Complex setup"]
    reason_rejected: "Qdrant has better Python integration"

consequences:
  positive:
    - "Self-hosted solutions provide data control"
    - "All technologies have strong Python ecosystems"

  negative:
    - "Need to manage infrastructure deployment"
    - "Requires Docker Compose orchestration"

impacts:
  - area: infrastructure
    description: "Requires Docker services for Qdrant, Neo4j, Redis"

  - area: development
    description: "Need client libraries: qdrant-client, neo4j, redis-py"

# Links to implementing sprints
graph_metadata:
  node_type: decision_document
  relationships:
    - type: implements
      target: system-architecture-v1
    - type: constrains
      target: infrastructure_sprints
```

### Creating Decision Records

```bash
# 1. Identify decision points from design documents
grep -r "alternatives\|options\|choices" context/design/

# 2. Create decision record
cp context/schemas/decision.yaml context/decisions/003-auth-strategy.yaml

# 3. Document alternatives and rationale
vim context/decisions/003-auth-strategy.yaml

# 4. Validate and commit
python -m src.agents.context_lint validate context/decisions/ --verbose
git add context/decisions/003-auth-strategy.yaml
git commit -m "docs(decision): add authentication strategy ADR"
```

## Phase 3: Sprint Planning

### Location & Schema
- **Directory**: `context/sprints/`
- **Schema**: `context/schemas/sprint.yaml`
- **Purpose**: Actionable sprint plans implementing designs and decisions

### Structure Example

```yaml
# context/sprints/sprint-5.1.yaml
schema_version: 1.0.0
document_type: sprint
id: sprint-5.1
title: "Sprint 5.1: Technology Stack Implementation"
status: planning
sprint_number: 5.1
start_date: '2025-07-15'
end_date: '2025-07-29'

goals:
  - "Implement core technology stack from Decision 001"
  - "Set up Qdrant vector storage with health checks"
  - "Deploy Neo4j with proper authentication"

phases:
  - phase: "5.1-1"
    name: "Infrastructure Setup"
    status: pending
    priority: blocking
    component: infra
    description: "Deploy technology stack per ADR-001"

    tasks:
      - title: "5.1-1 Deploy Qdrant v1.14.x with Docker"
        description: |
          Implement Qdrant deployment per Decision 001 technology stack.

          ## Acceptance Criteria
          - [ ] Qdrant container running on port 6333
          - [ ] Health check endpoint responding
          - [ ] Collections API accessible
          - [ ] Volume persistence configured

          ## Implementation Notes
          - Use qdrant/qdrant:v1.14.0 image
          - Configure named volume for data persistence
          - Follow Decision 001 requirements

          ## References
          - Design: system-architecture-v1
          - Decision: technology-stack-v1

        labels:
          - sprint-current
          - "phase:5.1"
          - "component:infra"
          - "priority:blocking"

        dependencies: []
        estimate: "4 hours"

# Explicit links to design and decisions
graph_metadata:
  node_type: sprint_document
  relationships:
    - type: implements
      target: system-architecture-v1
    - type: follows
      target: technology-stack-v1
```

### Creating Sprint Plans

```bash
# 1. Review design documents and decisions
ls context/design/ context/decisions/

# 2. Create sprint from template
cp context/sprints/sprint-template.yaml context/sprints/sprint-6.1.yaml

# 3. Map decisions to tasks
# Review each decision's impacts and create corresponding tasks

# 4. Validate sprint structure
python -m src.agents.context_lint validate context/sprints/ --verbose

# 5. Generate GitHub issues automatically
git add context/sprints/sprint-6.1.yaml
git commit -m "feat(sprint): add Sprint 6.1 implementing auth decisions"
git push origin main  # Triggers auto-issue-generation
```

## Automation & Tools

### Context Validation Agent

**Purpose**: Ensures document quality and relationship integrity

```bash
# Validate all documents
python -m src.agents.context_lint validate context/ --fix --verbose

# Check specific document type
python -m src.agents.context_lint validate context/design/ --verbose

# Auto-fix common issues
python -m src.agents.context_lint validate context/ --fix
```

**Features**:
- Schema compliance checking
- Cross-reference validation
- Timestamp management
- Stale document warnings

### Sprint Issue Linker

**Purpose**: Converts sprint tasks to GitHub issues with bidirectional sync

```bash
# Generate issues from sprint
python -m src.agents.sprint_issue_linker create --sprint sprint-6.1 --verbose

# Sync sprint changes to GitHub
python -m src.agents.sprint_issue_linker sync --sprint sprint-6.1 --verbose

# Preview sync changes
python -m src.agents.sprint_issue_linker sync --sprint sprint-6.1 --dry-run --verbose
```

### Sprint Update Agent

**Purpose**: Automatically updates sprint status based on GitHub activity

```bash
# Update sprint from GitHub issues
python -m src.agents.update_sprint update --verbose

# Generate progress report
python -m src.agents.update_sprint report --verbose

# Update specific sprint
python -m src.agents.update_sprint update --sprint sprint-6.1 --verbose
```

## Relationship Mapping

### Graph Metadata System

All documents include `graph_metadata` sections defining relationships:

```yaml
graph_metadata:
  node_type: document_type
  relationships:
    - type: implements|defines|requires|follows|constrains
      target: other_document_id
```

### Relationship Types

- **`implements`**: Sprint implements design/decision
- **`defines`**: Design defines system components
- **`requires`**: Design requires decisions
- **`follows`**: Sprint follows previous sprint
- **`constrains`**: Decision constrains implementation options
- **`references`**: General reference relationship

### Query Relationships

```bash
# Find what implements a design
python -c "
import yaml
from pathlib import Path

design_id = 'system-architecture-v1'
for sprint_file in Path('context/sprints').glob('*.yaml'):
    with open(sprint_file) as f:
        data = yaml.safe_load(f)
    relationships = data.get('graph_metadata', {}).get('relationships', [])
    for rel in relationships:
        if rel.get('target') == design_id and rel.get('type') == 'implements':
            print(f'{sprint_file.stem} implements {design_id}')
"
```

## Feedback Loops

### 1. Implementation → Sprint Status

```
GitHub Issues Closed → Sprint Tasks Completed → Phase Status Updated → Sprint Progress
```

**Automation**: `sprint-update.yml` workflow

### 2. Sprint Changes → GitHub Issues

```
Sprint YAML Updated → Issue Sync Triggered → GitHub Issues Updated → Team Notified
```

**Tool**: `python -m src.agents.sprint_issue_linker sync`

### 3. Document Access → Relevance Tracking

```
Document Read → last_referenced Updated → Relevance Score → Cleanup Decisions
```

**Automation**: Context lint agent

### 4. Validation Errors → Document Quality

```
Schema Violations → Validation Failures → Fix Suggestions → Document Improvements
```

**Tool**: `python -m src.agents.context_lint validate --fix`

## Agent Workflows

### Design Agent Workflow

```python
# Pseudo-code for design agent
def create_design_document(requirements):
    design = {
        'components': analyze_requirements(requirements),
        'constraints': identify_constraints(requirements),
        'references': find_related_configs(requirements)
    }
    validate_design(design)
    save_design_document(design)
    trigger_decision_analysis(design)
```

### Decision Agent Workflow

```python
# Pseudo-code for decision agent
def create_decision_record(design_requirements):
    alternatives = research_alternatives(design_requirements)
    analysis = {
        'alternatives_considered': alternatives,
        'decision': select_best_option(alternatives),
        'impacts': analyze_impacts(selected_option),
        'consequences': predict_outcomes(selected_option)
    }
    validate_decision(analysis)
    save_decision_record(analysis)
    trigger_sprint_planning(analysis)
```

### Sprint Planning Agent Workflow

```python
# Pseudo-code for sprint agent
def create_sprint_plan(decisions):
    sprint = {
        'goals': extract_goals_from_decisions(decisions),
        'phases': break_down_implementation(decisions),
        'tasks': create_detailed_tasks(phases),
        'dependencies': analyze_task_dependencies(tasks)
    }
    validate_sprint(sprint)
    save_sprint_document(sprint)
    generate_github_issues(sprint)
```

## Best Practices

### 1. Design Document Guidelines

- **Start broad, get specific**: Begin with system overview, drill down to components
- **Document assumptions**: Make implicit assumptions explicit
- **Link to constraints**: Reference existing limitations and requirements
- **Version control**: Use semantic versioning for major architectural changes

### 2. Decision Record Guidelines

- **One decision per record**: Don't combine multiple choices in one ADR
- **Document alternatives**: Show what was considered, not just what was chosen
- **Quantify impacts**: Be specific about consequences and constraints
- **Link to implementation**: Reference sprints that will implement the decision

### 3. Sprint Planning Guidelines

- **Map to decisions**: Each task should trace back to a design requirement or decision
- **Define acceptance criteria**: Make completion conditions measurable
- **Include references**: Link tasks to the design/decision they implement
- **Estimate realistically**: Use past sprint data to improve estimates

### 4. Automation Integration

- **Validate frequently**: Run context lint before commits
- **Sync bidirectionally**: Keep sprint YAML and GitHub issues in sync
- **Monitor relationships**: Check that implementations actually fulfill designs
- **Update timestamps**: Let tools manage document lifecycle metadata

## Example Complete Workflow

```bash
# === Phase 1: Design ===
# Create system design
cp context/schemas/design.yaml context/design/003-auth-system.yaml
vim context/design/003-auth-system.yaml
python -m src.agents.context_lint validate context/design/ --verbose
git add context/design/003-auth-system.yaml
git commit -m "docs(design): add authentication system architecture"

# === Phase 2: Decisions ===
# Document technology choices
cp context/schemas/decision.yaml context/decisions/004-auth-provider.yaml
vim context/decisions/004-auth-provider.yaml  # Choose OAuth vs JWT vs LDAP
python -m src.agents.context_lint validate context/decisions/ --verbose
git add context/decisions/004-auth-provider.yaml
git commit -m "docs(decision): select OAuth2 for authentication"

# === Phase 3: Sprint Planning ===
# Create implementation sprint
cp context/sprints/sprint-template.yaml context/sprints/sprint-7.1.yaml
vim context/sprints/sprint-7.1.yaml  # Map decisions to tasks
python -m src.agents.context_lint validate context/sprints/ --verbose
git add context/sprints/sprint-7.1.yaml
git commit -m "feat(sprint): add Sprint 7.1 implementing OAuth system"
git push origin main  # Auto-generates GitHub issues

# === Phase 4: Implementation ===
# Work on GitHub issues, automatic sprint tracking via workflows
gh issue list --label "sprint-7.1"
gh issue close 67 --comment "OAuth provider integration complete"

# === Phase 5: Feedback ===
# Sprint status automatically updated via GitHub Actions
# Generate final report
python -m src.agents.update_sprint report --sprint sprint-7.1 --verbose
```

This workflow provides **complete traceability** from high-level system design through specific technology decisions to actionable implementation tasks, with **automated synchronization** and **feedback loops** ensuring consistency across all levels.
