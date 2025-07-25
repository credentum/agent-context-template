# Claude CI Pipeline Flow Diagrams

Visual representations of the CI pipeline architecture and execution flow.

## Main Pipeline Architecture

```mermaid
graph TB
    subgraph "Entry Points"
        A[claude-ci.sh] --> B{Command Router}
        B --> C[check]
        B --> D[test]
        B --> E[pre-commit]
        B --> F[review]
        B --> G[fix-all]
        B --> H[all]
    end

    subgraph "Validation Stages"
        C --> I[Single File Validator]
        D --> J[Test Runner]
        E --> K[Pre-commit Hooks]
        F --> L[ARC Reviewer]
        G --> M[Auto-Fixer]
        H --> N[Full Pipeline]
    end

    subgraph "Core Components"
        I --> O[Black Formatter]
        I --> P[isort Imports]
        I --> Q[Flake8 Linter]
        I --> R[MyPy Type Checker]

        J --> S{Smart Selection?}
        S -->|Yes| T[Changed Tests Only]
        S -->|No| U[All Tests]
        T --> V[Coverage Report]
        U --> V

        K --> W[16 Pre-commit Hooks]

        L --> X[Coverage Check]
        L --> Y[Security Scan]
        L --> Z[Code Quality]
        L --> AA[Context Validation]

        M --> AB[Format Python]
        M --> AC[Fix YAML]
        M --> AD[Fix Types]
        M --> AE[Run Hooks]
    end

    subgraph "Output"
        N --> AF{All Pass?}
        AF -->|Yes| AG[✅ Success JSON]
        AF -->|No| AH[❌ Failure JSON]
        AH --> AI[Create GitHub Issues?]
    end

    style A fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style AG fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
    style AH fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px
```

## Detailed Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as claude-ci.sh
    participant Lint as Linting
    participant Type as Type Check
    participant Test as Tests
    participant ARC as ARC Review
    participant Git as Git/GitHub

    User->>CLI: ./scripts/claude-ci.sh all
    activate CLI

    CLI->>CLI: Parse arguments & options
    CLI->>CLI: Check git branch (not main)

    CLI->>Lint: Run pre-commit hooks
    activate Lint
    Lint->>Lint: black --check
    Lint->>Lint: isort --check
    Lint->>Lint: flake8
    Lint->>Lint: yamllint
    Lint->>Lint: custom validators
    Lint-->>CLI: Pass/Fail status
    deactivate Lint

    CLI->>Type: Run MyPy
    activate Type
    Type->>Type: Check src/
    Type->>Type: Check tests/
    Type-->>CLI: Type errors or success
    deactivate Type

    CLI->>Test: Run pytest
    activate Test
    Test->>Test: Collect tests
    Test->>Test: Execute tests
    Test->>Test: Generate coverage
    Test-->>CLI: Test results + coverage
    deactivate Test

    CLI->>ARC: Run ARC Reviewer
    activate ARC
    ARC->>Git: Get changed files
    ARC->>ARC: Analyze changes
    ARC->>ARC: Check coverage
    ARC->>ARC: Security scan
    ARC->>ARC: Quality checks
    ARC-->>CLI: Review verdict
    deactivate ARC

    CLI->>CLI: Generate JSON report
    CLI-->>User: Final status

    opt If --create-issues
        CLI->>Git: Create GitHub issues
    end

    deactivate CLI
```

## Progressive Validation Strategy

```mermaid
graph LR
    subgraph "Quick Mode (30s)"
        Q1[Essential Checks]
        Q2[Smart Tests]
        Q3[Fast Review]
    end

    subgraph "Standard Mode (3-5m)"
        S1[Full Linting]
        S2[Type Checking]
        S3[Test Suite]
        S4[ARC Review]
    end

    subgraph "Comprehensive Mode (10m+)"
        C1[Everything in Standard]
        C2[Integration Tests]
        C3[Performance Tests]
        C4[Full Coverage Analysis]
        C5[Security Deep Scan]
    end

    Q1 --> Q2 --> Q3
    S1 --> S2 --> S3 --> S4
    C1 --> C2 --> C3 --> C4 --> C5

    Q3 -.->|Escalate if issues| S1
    S4 -.->|Deep dive if needed| C1
```

## Auto-Fix Flow

```mermaid
graph TD
    A[Start fix-all] --> B[Scan for Issues]

    B --> C{Python Format?}
    C -->|Yes| D[Run Black]
    C -->|No| E{Import Order?}

    D --> E
    E -->|Yes| F[Run isort]
    E -->|No| G{YAML Issues?}

    F --> G
    G -->|Yes| H[Fix YAML]
    G -->|No| I{Type Errors?}

    H --> I
    I -->|Yes| J[Add type: ignore]
    I -->|No| K{Pre-commit?}

    J --> K
    K -->|Yes| L[Run hooks --fix]
    K -->|No| M{Security?}

    L --> M
    M -->|Yes| N[Create Issues]
    M -->|No| O[Final Validation]

    N --> O
    O --> P{All Fixed?}
    P -->|Yes| Q[✅ Success]
    P -->|No| R[Report Unfixable]

    style A fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style Q fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
    style R fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px
```

## Test Selection Strategy

```mermaid
graph TD
    A[Git Diff Analysis] --> B{Files Changed?}

    B -->|Python Files| C[Map to Test Files]
    B -->|Test Files| D[Run Directly]
    B -->|Config Files| E[Run All Tests]

    C --> F[Find Direct Tests]
    F --> G[Find Import Tests]
    G --> H[Check Coverage Impact]

    D --> I[Add to Test Set]
    E --> J[Flag Full Suite]

    H --> K{Coverage Risk?}
    K -->|High| L[Add Integration Tests]
    K -->|Low| M[Minimal Test Set]

    L --> N[Execute Tests]
    M --> N
    I --> N
    J --> O[Run Full Suite]

    N --> P[Generate Report]
    O --> P

    style A fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px
    style P fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
```

## CI Decision Tree

```mermaid
graph TD
    A[CI Pipeline Start] --> B{On main branch?}
    B -->|Yes| C[❌ Error: Switch branch]
    B -->|No| D{Quick mode?}

    D -->|Yes| E[Run essential checks]
    D -->|No| F{Comprehensive?}

    F -->|Yes| G[Run all checks + integration]
    F -->|No| H[Run standard checks]

    E --> I{Issues found?}
    H --> I
    G --> I

    I -->|Yes| J{Auto-fix enabled?}
    I -->|No| K[✅ Ready for PR]

    J -->|Yes| L[Apply fixes]
    J -->|No| M{Create issues?}

    L --> N{Fixes successful?}
    N -->|Yes| O[Re-run validation]
    N -->|No| P[Report unfixable]

    M -->|Yes| Q[Create GitHub issues]
    M -->|No| R[❌ Manual fix required]

    O --> I

    style C fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px
    style K fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px
    style R fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px
```

## Error Handling Flow

```mermaid
stateDiagram-v2
    [*] --> Running: Start CI
    Running --> LintCheck: Check Linting

    LintCheck --> TypeCheck: Lint Pass
    LintCheck --> HandleLintError: Lint Fail

    TypeCheck --> TestRun: Type Pass
    TypeCheck --> HandleTypeError: Type Fail

    TestRun --> ARCReview: Tests Pass
    TestRun --> HandleTestError: Tests Fail

    ARCReview --> Success: Review Pass
    ARCReview --> HandleReviewError: Review Fail

    HandleLintError --> AutoFix: If --fix
    HandleTypeError --> AutoFix: If fixable
    HandleTestError --> ReportFailure: Not fixable
    HandleReviewError --> AutoFix: If fixable

    AutoFix --> Running: Retry
    AutoFix --> ReportFailure: Can't fix

    Success --> [*]: Exit 0
    ReportFailure --> [*]: Exit 1
```

## Integration Points

```mermaid
graph LR
    subgraph "Local Development"
        A[VS Code]
        B[Terminal]
        C[Git Hooks]
    end

    subgraph "CI Scripts"
        D[claude-ci.sh]
        E[Support Scripts]
        F[Config Files]
    end

    subgraph "External Tools"
        G[Python Tools]
        H[Pre-commit]
        I[Docker]
    end

    subgraph "GitHub"
        J[Actions]
        K[Issues]
        L[PRs]
    end

    A --> D
    B --> D
    C --> D

    D --> E
    D --> F

    E --> G
    E --> H
    E --> I

    D --> K
    D --> L
    J --> D

    style D fill:#ffd54f,stroke:#f57f17,stroke-width:3px
```

## Performance Optimization

```mermaid
gantt
    title CI Pipeline Execution Timeline
    dateFormat mm:ss
    axisFormat %M:%S

    section Quick Mode
    Branch Check      :done, q1, 00:00, 1s
    Essential Lint    :done, q2, after q1, 2s
    Type Check        :done, q3, after q2, 2s
    Smart Tests       :done, q4, after q3, 12s
    Quick Review      :done, q5, after q4, 11s
    Total 28s         :milestone, after q5, 0s

    section Standard Mode
    Branch Check      :done, s1, 00:00, 1s
    Full Linting      :done, s2, after s1, 7s
    Type Check        :done, s3, after s2, 3s
    Test Suite        :done, s4, after s3, 40s
    Coverage          :active, s5, after s4, 5s
    ARC Review        :done, s6, after s5, 6s
    Total 62s         :milestone, after s6, 0s

    section Comprehensive
    Everything Std    :done, c1, 00:00, 62s
    Integration Tests :active, c2, after c1, 120s
    Perf Benchmarks   :active, c3, after c2, 180s
    Security Scan     :active, c4, after c3, 60s
    Total 7m          :milestone, after c4, 0s
```

---

*These diagrams represent the actual CI pipeline architecture implemented in the agent-context-template project.*
