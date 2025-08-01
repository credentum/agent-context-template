# Modal OAuth Architecture

## Overview
This document describes the OAuth token flow, Modal function orchestration, and agent communication patterns for the autonomous pipeline.

## OAuth Token Flow

```mermaid
sequenceDiagram
    participant User
    participant GitHub
    participant Webhook
    participant Modal
    participant KeyChain
    participant Claude
    participant Redis

    User->>GitHub: @claude mention in issue
    GitHub->>Webhook: Webhook event
    Webhook->>Modal: Trigger orchestrator

    Note over Modal: OAuth Token Retrieval
    Modal->>KeyChain: Get OAuth credentials
    KeyChain-->>Modal: Encrypted tokens
    Modal->>Modal: Check token validity

    alt Token Expired
        Modal->>Claude: Refresh OAuth token
        Claude-->>Modal: New tokens
        Modal->>KeyChain: Store new tokens
    end

    Modal->>Claude: API request with Bearer token
    Claude-->>Modal: Response

    Note over Modal: State Persistence
    Modal->>Redis: Store workflow state
    Redis-->>Modal: State stored
```

## Agent Communication Architecture

```mermaid
graph TB
    subgraph "GitHub Layer"
        GH[GitHub Issue/PR]
        GHApp[GitHub App]
    end

    subgraph "Modal Orchestration Layer"
        Orch[Pipeline Orchestrator]
        Queue[Task Queue]
        State[State Manager - Redis]
    end

    subgraph "Autonomous Agents"
        Class[Issue Classifier]
        Inv[Investigator]
        Impl[Implementation Engine]
        Test[Test Validator]
        PR[PR Manager]
    end

    subgraph "Learning Layer"
        VDB[Vector Database]
        ML[ML Models]
        Learn[Learning Pipeline]
    end

    subgraph "Security Layer"
        OAuth[OAuth Manager]
        Keys[KeyChain]
        Audit[Audit Logger]
    end

    GH -->|Webhook| Orch
    Orch -->|Spawn| Queue
    Queue -->|Distribute| Class
    Queue -->|Distribute| Inv
    Queue -->|Distribute| Impl
    Queue -->|Distribute| Test
    Queue -->|Distribute| PR

    Class -->|Classify| State
    Inv -->|Investigate| State
    Impl -->|Implement| State
    Test -->|Validate| State
    PR -->|Create PR| GHApp

    State <-->|Persist| Redis

    Class -->|Query| VDB
    Inv -->|Query| VDB
    Learn -->|Update| VDB
    Learn -->|Retrain| ML

    OAuth -->|Provide Tokens| Orch
    OAuth <-->|Store/Retrieve| Keys
    OAuth -->|Log Access| Audit

    style OAuth fill:#f9f,stroke:#333,stroke-width:4px
    style Keys fill:#f9f,stroke:#333,stroke-width:4px
```

## Modal Function Orchestration

```mermaid
stateDiagram-v2
    [*] --> IssueReceived
    IssueReceived --> Classification

    Classification --> AutonomousPath: Eligible
    Classification --> HumanEscalation: Not Eligible

    AutonomousPath --> Investigation
    Investigation --> Implementation: Confident
    Investigation --> HumanEscalation: Low Confidence

    Implementation --> Testing
    Testing --> PRCreation: Tests Pass
    Testing --> SelfHealing: Tests Fail

    SelfHealing --> Testing: Fixed
    SelfHealing --> HumanEscalation: Can't Fix

    PRCreation --> AutoMerge: High Confidence
    PRCreation --> ReviewWait: Low Confidence

    AutoMerge --> Monitoring
    ReviewWait --> Monitoring: Approved

    Monitoring --> [*]: Complete
    HumanEscalation --> [*]: Escalated
```

## OAuth Error Handling and Recovery

```mermaid
flowchart TB
    Start([API Call with OAuth]) --> CheckToken{Token Valid?}

    CheckToken -->|Yes| MakeRequest[Make API Request]
    CheckToken -->|No| RefreshToken[Refresh Token]

    RefreshToken --> RefreshSuccess{Refresh Success?}
    RefreshSuccess -->|Yes| UpdateKeychain[Update Keychain]
    RefreshSuccess -->|No| CheckRetries{Retries < 3?}

    UpdateKeychain --> MakeRequest

    CheckRetries -->|Yes| RefreshToken
    CheckRetries -->|No| FallbackAuth[Try Fallback Auth]

    FallbackAuth --> FallbackSuccess{Success?}
    FallbackSuccess -->|Yes| MakeRequest
    FallbackSuccess -->|No| EscalateError[Escalate to Human]

    MakeRequest --> RequestSuccess{Request Success?}
    RequestSuccess -->|Yes| ProcessResponse[Process Response]
    RequestSuccess -->|No| CheckError{Auth Error?}

    CheckError -->|Yes| RefreshToken
    CheckError -->|No| HandleError[Handle Other Error]

    ProcessResponse --> End([Complete])
    EscalateError --> End
    HandleError --> End
```

## Security Constraints

### OAuth Token Security
1. **Storage**: All OAuth tokens stored in OS keychain (never in files)
2. **Encryption**: Additional encryption layer before keychain storage
3. **Rotation**: Automatic rotation every 4 hours
4. **Audit**: All token access logged with timestamp and purpose
5. **Scope**: Minimal required scopes for Claude API access

### Modal Secrets Management
```yaml
# Example Modal secret configuration (with placeholders)
secrets:
  claude-oauth-tokens:
    CLAUDE_CLIENT_ID: "PLACEHOLDER_CLIENT_ID"  # TODO: Replace with actual
    CLAUDE_CLIENT_SECRET: "PLACEHOLDER_SECRET"  # TODO: Replace with actual
    ENCRYPTION_KEY: "PLACEHOLDER_KEY"          # TODO: Generate secure key

  github-app-credentials:
    GITHUB_APP_ID: "PLACEHOLDER_APP_ID"        # TODO: Replace with actual
    GITHUB_APP_PRIVATE_KEY: |                  # TODO: Replace with actual
      -----BEGIN RSA PRIVATE KEY-----
      PLACEHOLDER_PRIVATE_KEY
      -----END RSA PRIVATE KEY-----
```

### Network Security
- All API calls use HTTPS
- Certificate pinning for Claude API endpoints
- Request signing for webhook validation
- IP allowlisting for Modal endpoints

## State Management Architecture

```mermaid
graph LR
    subgraph "Modal Function"
        Func[Function Instance]
        Local[Local State]
    end

    subgraph "Redis Cluster"
        State[Workflow State]
        Lock[Distributed Locks]
        Queue[Task Queue]
    end

    subgraph "Persistent Storage"
        S3[S3 Bucket]
        DB[PostgreSQL]
    end

    Func -->|Read/Write| Local
    Local <-->|Sync| State
    State -->|Backup| S3
    State -->|Analytics| DB

    Func -->|Acquire| Lock
    Lock -->|Coordinate| Queue
```

## Monitoring and Observability

```mermaid
graph TB
    subgraph "Modal Functions"
        F1[Function 1]
        F2[Function 2]
        F3[Function N]
    end

    subgraph "Telemetry"
        OT[OpenTelemetry Collector]
        Metrics[Prometheus]
        Traces[Jaeger]
        Logs[CloudWatch]
    end

    subgraph "Dashboards"
        Grafana[Grafana]
        Custom[Custom Dashboard]
        Alerts[AlertManager]
    end

    F1 -->|Emit| OT
    F2 -->|Emit| OT
    F3 -->|Emit| OT

    OT -->|Metrics| Metrics
    OT -->|Traces| Traces
    OT -->|Logs| Logs

    Metrics --> Grafana
    Traces --> Grafana
    Logs --> Custom

    Metrics --> Alerts
    Alerts -->|Notify| PagerDuty
```

## Cost Optimization Strategy

### Modal Compute Costs
- CPU: $0.00001 per millisecond
- Memory: $0.0000015 per GB-millisecond
- GPU (T4): $0.000076 per second

### Optimization Techniques
1. **Function Pooling**: Reuse warm instances
2. **Batch Processing**: Group similar tasks
3. **Early Termination**: Stop on low confidence
4. **Resource Scaling**: Right-size CPU/memory
5. **Caching**: Cache Claude responses

### Example Cost Calculation
```python
# Average issue resolution
cpu_time = 120  # seconds
memory_gb = 2
gpu_time = 30  # seconds for ML ops

cpu_cost = cpu_time * 1000 * 0.00001  # $1.20
memory_cost = cpu_time * 1000 * memory_gb * 0.0000015  # $0.36
gpu_cost = gpu_time * 0.000076  # $0.00228

total_modal_cost = cpu_cost + memory_cost + gpu_cost  # ~$1.56

# Claude API costs (example)
input_tokens = 5000
output_tokens = 2000
claude_cost = (input_tokens * 0.015 + output_tokens * 0.075) / 1000  # $0.225

total_cost_per_issue = total_modal_cost + claude_cost  # ~$1.79
```

With optimization and volume, targeting <$0.50 per issue.
