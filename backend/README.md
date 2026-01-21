# Mahoraga Backend - Triage Engine

<div align="center">

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg)](https://www.sqlalchemy.org)

**The intelligent core powering autonomous bug triage**

</div>

---

## Overview

The backend is a FastAPI-powered triage engine that orchestrates the entire bug analysis pipeline. It processes GitHub webhooks, mines git history for expertise, leverages AI for bug analysis, and intelligently routes issues to the right developers.

---

## Architecture

```mermaid

graph TD
    subgraph Entry["Entry Points"]
        WH["webhook_handler.py<br/>GitHub Webhooks"]
        API["api_endpoints.py<br/>REST API"]
    end
    
    subgraph Processing["Processing Layer"]
        SP["stack_trace_parser.py<br/>Multi-language Parser"]
        GE["git_analysis_engine.py<br/>Expertise Mining"]
        AI["ai_analysis_service.py<br/>Gemini Integration"]
    end
    
    subgraph Decision["Decision Layer"]
        AE["assignment_engine.py<br/>Developer Matching"]
        DP["draft_pr_generator.py<br/>Auto-fix Generation"]
    end
    
    subgraph Output["Output Layer"]
        SN["slack_notification_service.py<br/>Notifications"]
        EH["error_handling.py<br/>Circuit Breakers"]
    end
    
    subgraph Data["Data Layer"]
        DB["database.py<br/>SQLAlchemy Models"]
        CFG["config.py<br/>Configuration"]
    end
    
    WH --> SP
    WH --> GE
    SP --> AI
    GE --> AE
    AI --> AE
    AE --> DP
    AE --> SN
    
    API --> DB
    WH --> DB
    AE --> DB
    
    EH -.-> AI
    EH -.-> SN
    EH -.-> DP
    
    CFG --> WH
    CFG --> AE
```

---

## File Structure

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application entry point |
| `config.py` | Environment configuration via Pydantic |
| `database.py` | SQLAlchemy models and session management |
| `webhook_handler.py` | GitHub webhook processing with HMAC verification |
| `stack_trace_parser.py` | Multi-language stack trace parsing |
| `git_analysis_engine.py` | Git blame expertise scoring |
| `ai_analysis_service.py` | Google Gemini AI integration |
| `assignment_engine.py` | Intelligent developer matching |
| `draft_pr_generator.py` | Automated fix generation |
| `slack_notification_service.py` | Slack notifications with retry |
| `error_handling.py` | Circuit breakers and error management |
| `api_endpoints.py` | Dashboard and configuration REST APIs |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Git

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

### Configuration

Edit `.env` with your credentials:

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=your_webhook_secret
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxx
```

### Running

```bash
# Development
python main.py

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server available at: `http://localhost:8000`  
API docs at: `http://localhost:8000/docs`

---

## Core Components

### Stack Trace Parser

Extracts file paths and line numbers from stack traces in multiple languages:

```mermaid

flowchart LR
    A[Raw Stack Trace] --> B{Language?}
    B -->|Python| C["Extract .py files"]
    B -->|JavaScript| D["Extract .js/.ts files"]
    B -->|Java| E["Extract .java files"]
    C --> F[File Path + Line Number]
    D --> F
    E --> F
```

**Supported Languages:**
- Python (`File "path", line N`)
- JavaScript/TypeScript (`at file:line:col`)
- Java (`at Class.method(File.java:N)`)

### Git Expertise Engine

Calculates developer expertise using recency-weighted scoring:

```
expertise_score = (commit_count × recency_weight) + (lines_owned / total_lines) × 100
```

Where:
- `recency_weight = e^(-days_since_commit / 90)`
- Recent commits weighted higher with 90-day decay

**Git Blame Flags:**
- `-w`: Ignore whitespace
- `-C -C`: Detect code movement across files
- `-M`: Detect code movement within files

### Assignment Engine

Confidence-based routing:

| Confidence | Action |
|------------|--------|
| **>85%** | Generate draft PR + assign |
| **60-85%** | Auto-assign with notification |
| **<60%** | Route to human triage |

### Circuit Breakers

Protects external services with graceful degradation:

```mermaid

stateDiagram-v2
    [*] --> Closed
    Closed --> Open : 5 failures
    Open --> HalfOpen : 60s timeout
    HalfOpen --> Closed : Success
    HalfOpen --> Open : Failure
```

**Protected Services:**
- Gemini AI API
- GitHub API
- Slack API
- Git operations

---

## Testing

```bash
# Activate virtual environment first
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run all tests
pytest -v

# Run with hypothesis statistics
pytest --hypothesis-show-statistics

# Run specific test files
pytest test_integration.py -v
pytest test_draft_pr_generator.py -v
pytest test_config.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Test Suites

| Test File | Coverage |
|-----------|----------|
| `test_config.py` | Property-based config tests |
| `test_integration.py` | End-to-end pipeline tests |
| `test_draft_pr_generator.py` | PR generation tests |
| `test_webhook_handler.py` | Webhook processing tests |

---

## API Reference

### Health

```http
GET /health
GET /health/detailed
```

### Webhook

```http
POST /webhook/github
```

### Dashboard

```http
GET /api/dashboard/stats
GET /api/dashboard/bus-factor
```

### Configuration

```http
GET /api/config/settings
PUT /api/config/settings
GET /api/config/users
POST /api/config/users
PUT /api/config/users/{email}
DELETE /api/config/users/{email}
```

---

## Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Webhook acknowledgment | <500ms |
| Full triage pipeline | <5s |
| Draft PR generation | <10s |
| Memory usage | ~200MB |

---

## Dependencies

Key dependencies from `requirements.txt`:

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | Database ORM |
| `pydantic` | Data validation |
| `google-generativeai` | Gemini AI |
| `PyGithub` | GitHub API |
| `slack-sdk` | Slack integration |
| `pytest` | Testing |
| `hypothesis` | Property-based testing |

---

<div align="center">

**Part of the [Mahoraga](../README.md) Autonomous Bug Triage System**

</div>
