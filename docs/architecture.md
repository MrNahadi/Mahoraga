# Mahoraga System Architecture

## Overview

Mahoraga is an autonomous bug triage system that combines AI analysis, git history mining, and intelligent routing to automatically assign bugs to the most qualified developers.

## System Architecture Diagram

```mermaid
graph TB
    subgraph "External Systems"
        GH[GitHub<br/>Issues & PRs]
        SL[Slack<br/>Notifications]
        GM[Gemini AI<br/>Analysis]
    end
    
    subgraph "Backend - Triage Engine"
        WH[Webhook Handler]
        SP[Stack Trace Parser]
        GE[Git Expertise Engine]
        AI[AI Analysis Service]
        AE[Assignment Engine]
        DP[Draft PR Generator]
        SN[Slack Notifier]
        EH[Error Handler]
        DB[(SQLite Database)]
        API[REST API Endpoints]
    end
    
    subgraph "Frontend - Command Center"
        DASH[Team Dashboard]
        BF[Bus Factor Monitor]
        CFG[Configuration Panel]
        RT[Real-time Updates]
    end
    
    GH -->|Webhook| WH
    WH --> SP
    WH --> GE
    SP --> AI
    GE --> AE
    AI --> AE
    AE --> DP
    AE --> SN
    DP --> GH
    SN --> SL
    WH --> EH
    AI --> EH
    
    WH -.-> DB
    AE -.-> DB
    DP -.-> DB
    SN -.-> DB
    
    API --> DB
    DASH --> API
    BF --> API
    CFG --> API
    RT -.->|Auto-refresh| API
    
    GM -.->|AI Requests| AI
    GE -.->|Git Blame| GH
```

## Component Interactions

### 1. Webhook Reception Flow

```mermaid
sequenceDiagram
    participant GitHub
    participant WebhookHandler
    participant Database
    participant StackParser
    
    GitHub->>WebhookHandler: POST /webhook/github
    WebhookHandler->>WebhookHandler: Verify HMAC signature
    WebhookHandler->>Database: Check for duplicates (10min window)
    
    alt Duplicate detected
        WebhookHandler-->>GitHub: 200 OK (ignored)
    else New issue
        WebhookHandler->>StackParser: Parse stack trace
        WebhookHandler->>Database: Queue for processing
        WebhookHandler-->>GitHub: 200 OK
    end
```

### 2. Triage Processing Pipeline

```mermaid
flowchart LR
    A[Stack Trace Parsed] --> B{Has Stack Trace?}
    B -->|Yes| C[Extract File Paths]
    B -->|No| D[Use Issue Body]
    
    C --> E[Git Expertise Analysis]
    D --> E
    
    E --> F[AI Bug Analysis]
    
    F --> G{Confidence > 85%?}
    G -->|Yes| H[Generate Draft Fix]
    G -->|No| I[Calculate Assignment]
    
    H --> I
    
    I --> J{Confidence > 60%?}
    J -->|Yes| K[Assign to Expert]
    J -->|No| L[Route to Human Triage]
    
    K --> M[Send Slack Notification]
    L --> N[Escalate to On-Call]
```

### 3. Draft PR Generation Flow

```mermaid
flowchart TD
    A[Bug Analysis Complete] --> B{Confidence > 85%?}
    B -->|No| END[Skip Draft]
    B -->|Yes| C{Single File?}
    C -->|No| END
    C -->|Yes| D[AI Generate Fix]
    
    D --> E{Lines Changed < 20?}
    E -->|No| END
    E -->|Yes| F[Create Draft PR]
    
    F --> G[Label as DRAFT]
    G --> H[Add Explanatory Comment]
    H --> I[Notify Assignee]
```

## Technology Stack

### Backend (Python)
- **Web Framework**: FastAPI 0.104+
- **Database**: SQLAlchemy + SQLite
- **Testing**: pytest + Hypothesis (property-based)
- **AI Integration**: Google Generative AI (Gemini)
- **Git Operations**: PyGithub + subprocess
- **Notifications**: Slack SDK

### Frontend (TypeScript/React)
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3
- **UI Components**: Radix UI (shadcn/ui)
- **State Management**: TanStack Query
- **Charts**: Recharts
- **Testing**: Vitest + Testing Library

### Infrastructure
- **Containers**: Docker + Docker Compose
- **Web Server**: Uvicorn (ASGI)
- **Dev Server**: Vite Dev Server
- **Database**: SQLite (development), PostgreSQL-ready (production)

## Data Models

### Core Entities

```mermaid
erDiagram
    User ||--o{ Assignment : receives
    User {
        string git_email PK
        string slack_id
        string display_name
        boolean is_active
        datetime created_at
    }
    
    Assignment ||--|| TriageDecision : has
    Assignment {
        string id PK
        string issue_id
        string issue_url
        string assigned_to_email FK
        float confidence
        string reasoning
        string status
        datetime created_at
    }
    
    TriageDecision {
        string id PK
        string issue_id
        float confidence
        string draft_pr_url
        int processing_time_ms
        datetime created_at
    }
    
    SystemConfig {
        string key PK
        string value
        string description
    }
    
    ExpertiseCache {
        string id PK
        string file_path
        string developer_email
        float score
        datetime expires_at
    }
```

## Key Features & Algorithms

### 1. Git Expertise Calculation

**Algorithm**: Recency-weighted ownership scoring

```
expertise_score = (commit_count * recency_weight) + (lines_owned / total_lines) * 100

where:
  recency_weight = e^(-days_since_commit / 90)
  - Recent commits weighted higher
  - Exponential decay over 90 days
```

**Implementation**: Uses `git blame` with `-w -C -C -M` flags
- `-w`: Ignore whitespace changes
- `-C -C`: Detect code movement across files
- `-M`: Detect code movement within files

### 2. Confidence Scoring

**Factors**:
1. AI analysis confidence (0-100%)
2. Stack trace clarity (weighted)
3. Code ownership certainty
4. Historical success rate

**Thresholds**:
- **>85%**: Auto-generate draft PR
- **60-85%**: Auto-assign with notification
- **<60%**: Route to human triage

### 3. Duplicate Detection

**Method**: Time-window based deduplication
- 10-minute sliding window (configurable)
- Based on issue ID + repository
- Prevents webhook replay attacks

### 4. Circuit Breaker Pattern

**Services Protected**:
- Gemini AI API
- GitHub API
- Slack API
- Git operations

**Parameters**:
- Failure threshold: 5 consecutive failures
- Timeout: 30 seconds (configurable)
- Recovery time: 60 seconds

## Security

### 1. Webhook Verification
- HMAC-SHA256 signature validation
- Constant-time comparison to prevent timing attacks
- Replay protection via timestamp validation

### 2. API Authentication
- Environment-based secrets
- No hardcoded credentials
- Separate tokens per service

### 3. Data Protection
- Input validation on all endpoints
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention in frontend

## Performance Characteristics

### Response Times (Target)
- Webhook acknowledgment: <500ms
- Full triage pipeline: <5s
- Draft PR generation: <10s
- Dashboard load: <2s

### Scalability
- Concurrent webhook handling: 10+ simultaneous
- Database queries: Indexed for performance
- Async processing: Non-blocking I/O
- Circuit breakers: Graceful degradation

### Resource Usage
- Memory: ~200MB (backend) + ~100MB (frontend)
- Database: SQLite suitable for <10k issues/month
- API calls: Cached where possible (git blame, expertise)

## Deployment

### Development
```bash
docker-compose up --build
```

### Production Considerations
1. Replace SQLite with PostgreSQL for scale
2. Add Redis for caching git expertise
3. Configure nginx reverse proxy
4. Set up SSL/TLS certificates
5. Enable logging aggregation (ELK stack)
6. Configure monitoring (Prometheus + Grafana)

## Future Enhancements

- [ ] Machine learning for confidence calibration
- [ ] Multi-repository support
- [ ] Custom triage rules engine
- [ ] Integration with JIRA, Linear, etc.
- [ ] Advanced analytics dashboard
- [ ] A/B testing for assignment strategies
