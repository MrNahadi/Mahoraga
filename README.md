# Mahoraga - Autonomous Bug Triage System

Mahoraga is an autonomous bug triage agent that analyzes bugs, identifies exact code locations, calculates true ownership from git history, and drafts fixes before humans even see the ticket.

## Project Structure

```
├── backend/                 # FastAPI triage engine
│   ├── main.py             # FastAPI application entry point
│   ├── config.py           # Environment configuration management
│   ├── database.py         # SQLAlchemy models and database setup
│   ├── requirements.txt    # Python dependencies
│   └── test_config.py      # Property-based tests for configuration
├── frontend/               # React Command Center dashboard
│   ├── src/                # React source code
│   ├── package.json        # Node.js dependencies
│   └── vite.config.ts      # Vite configuration
├── .github/workflows/      # CI/CD pipeline
└── docker-compose.yml      # Container orchestration
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Git

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` file with your API keys:
   - `GITHUB_TOKEN`: GitHub personal access token
   - `GITHUB_WEBHOOK_SECRET`: Webhook secret for signature verification
   - `SLACK_BOT_TOKEN`: Slack bot token for notifications
   - `GEMINI_API_KEY`: Google Gemini API key for AI analysis

6. Start the FastAPI server:
   ```bash
   python main.py
   ```

   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

### Virtual Environment Management

To deactivate the Python virtual environment when you're done:
```bash
deactivate
```

To reactivate it later:
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Docker Setup

Run the entire system with Docker Compose:

```bash
docker-compose up --build
```

## Environment Variables

| Variable                             | Description                                     | Required |
| ------------------------------------ | ----------------------------------------------- | -------- |
| `GITHUB_TOKEN`                       | GitHub personal access token                    | Yes      |
| `GITHUB_WEBHOOK_SECRET`              | Webhook signature verification secret           | Yes      |
| `SLACK_BOT_TOKEN`                    | Slack bot token for notifications               | Yes      |
| `GEMINI_API_KEY`                     | Google Gemini API key for AI analysis           | Yes      |
| `CONFIDENCE_THRESHOLD`               | Assignment confidence threshold (default: 60.0) | No       |
| `DRAFT_PR_ENABLED`                   | Enable draft PR generation (default: true)      | No       |
| `DUPLICATE_DETECTION_WINDOW_MINUTES` | Duplicate detection window (default: 10)        | No       |

## API Endpoints

- `GET /` - Health check
- `GET /health` - System health status
- `POST /webhook/github` - GitHub webhook handler (to be implemented)

## Testing

Run backend tests (make sure virtual environment is activated):
```bash
cd backend
# Activate virtual environment first
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate

python -m pytest -v
```

Run frontend tests:
```bash
cd frontend
npm run test
```

## Architecture

For detailed system architecture, component interactions, and technical stack information, see [Architecture Documentation](docs/architecture.md).

## Demo

For a complete demo walkthrough with test scenarios, see [Demo Script](demo/demo_script.md).

## Testing

### Backend Tests

Run all backend tests (integration, unit, and property-based):
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pytest -v
```

Run specific test suites:
```bash
# Integration tests (Tasks 18 & 18.2)
pytest test_integration.py -v

# Draft PR generation tests
pytest test_draft_pr_generator.py -v

# All property-based tests
pytest test_*.py -v --hypothesis-show-statistics
```

### Frontend Tests

Run frontend component and unit tests:
```bash
cd frontend
npm run test
```

## Development Status

✅ **System Complete** - All core features implemented and tested:

- ✅ Project setup and infrastructure
- ✅ Database schema and models with SQLAlchemy
- ✅ GitHub webhook handler with signature verification
- ✅ Multi-language stack trace parser (Python, JavaScript, Java)
- ✅ Git expertise analysis engine with recency weighting
- ✅ AI-powered bug analysis with Gemini 
- ✅ Intelligent assignment engine with confidence scoring
- ✅ Draft PR generator for high-confidence bugs
- ✅ Slack notification service with retry logic
- ✅ React Command Center dashboard
- ✅ Real-time team health monitoring
- ✅ Bus factor analysis and warnings
- ✅ Configuration management panel
- ✅ Error handling and circuit breakers
- ✅ Comprehensive test suite (13 test files, 100+ tests)
- ✅ Integration and system testing complete
- ✅ Demo materials and documentation

## API Documentation

### Webhook Endpoints
- `POST /webhook/github` - GitHub webhook receiver
  - Validates HMAC signature
  - Processes issue events
  - Queues triage job

### Dashboard Endpoints
- `GET /api/dashboard/stats` - Team statistics and metrics
  - Active assignments per developer
  - Recent triage decisions
  - Processing metrics

- `GET /api/dashboard/bus-factor` - Code ownership analysis
  - Single-contributor warnings
  - Knowledge distribution
  - Ownership percentages

### Configuration Endpoints
- `GET /api/config/settings` - Current system settings
- `PUT /api/config/settings` - Update configuration
  - Confidence threshold
  - Draft PR mode toggle
  - Duplicate detection window

- `GET /api/config/users` - User mappings list  
- `POST /api/config/users` - Create user mapping
- `PUT /api/config/users/{email}` - Update user mapping
- `DELETE /api/config/users/{email}` - Remove user mapping

### Health Endpoints
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed status with circuit breaker metrics

## Contributing

This project follows spec-driven development methodology. See `.kiro/specs/ticket-triage/` for detailed requirements, design decisions, and implementation tasks.