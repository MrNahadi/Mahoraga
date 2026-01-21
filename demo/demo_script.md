# Mahoraga Demo Script

## Overview
This demo script walks through the key features of Mahoraga, the autonomous bug triage system that analyzes bugs, calculates code ownership from git history, and automatically assigns issues to the right developers.

## Prerequisites

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables
Create `.env` file in `backend/` directory:
```bash
GITHUB_TOKEN=your_github_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret
SLACK_BOT_TOKEN=your_slack_bot_token
GEMINI_API_KEY=your_gemini_api_key
```

### Frontend Setup
```bash
cd frontend
npm install
```

## Demo Scenarios

### Scenario 1: High Confidence Bug Auto-Assignment

**Objective**: Demonstrate end-to-end triage of a clear bug with automatic assignment

**Steps**:
1. Start the backend server:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```

2. Start the frontend dashboard:
   ```bash
   cd frontend
   npm run dev
   ```

3. Trigger webhook with a Python FileNotFoundError:
   ```bash
   curl -X POST http://localhost:8000/webhook/github \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Event: issues" \
     -H "X-Hub-Signature-256: sha256=test" \
     -d '{
       "action": "opened",
       "issue": {
         "id": 12345,
         "number": 42,
         "title": "Bug: Config file not found",
         "body": "Traceback (most recent call last):\n  File \"app/config.py\", line 23, in load_config\n    return json.load(f)\nFileNotFoundError: config.json",
         "html_url": "https://github.com/demo/repo/issues/42"
       }
     }'
   ```

**Expected Result**:
- Stack trace parsed successfully
- AI analyzes root cause (missing config file)
- Git expertise calculated for `app/config.py`
- Developer with highest expertise receives assignment
- Slack notification sent with context
- Dashboard shows new assignment

---

### Scenario 2: High Confidence with Draft PR Generation

**Objective**: Show automatic draft fix generation for simple, clear bugs

**Setup**: Same as Scenario 1, but with a bug that has >85% confidence

**Steps**:
1. Trigger webhook with a simple off-by-one error:
   ```bash
   curl -X POST http://localhost:8000/webhook/github \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Event: issues" \
     -H "X-Hub-Signature-256: sha256=test" \
     -d '{
       "action": "opened",
       "issue": {
         "id": 12346,
         "number": 43,
         "title": "Bug: Array index out of bounds",
         "body": "IndexError: list index out of range\nFile: utils/parser.py, line 45"
       }
     }'
   ```

2. Check the dashboard for draft PR link

**Expected Result**:
- High confidence analysis (>85%)
- Draft PR created automatically
- PR labeled as "DRAFT - Review Required"
- Changes limited to single file, <20 lines
- Notification includes PR link

---

### Scenario 3: Low Confidence Human Escalation

**Objective**: Demonstrate routing ambiguous bugs to human triage

**Steps**:
1. Send unclear error without stack trace:
   ```bash
   curl -X POST http://localhost:8000/webhook/github \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Event: issues" \
     -H "X-Hub-Signature-256: sha256=test" \
     -d '{
       "action": "opened",
       "issue": {
         "id": 12347,
         "number": 44,
         "title": "Application behaves strangely",
         "body": "Sometimes the app crashes, but not always. No clear pattern."
       }
     }'
   ```

**Expected Result**:
- Low confidence score (<60%)
- Routed to on-call engineer for manual triage
- Notification includes "Low Confidence" warning
- Dashboard shows pending human review

---

### Scenario 4: Dashboard Monitoring

**Objective**: Show real-time team health visualization

**Steps**:
1. Open dashboard: `http://localhost:5173`
2. Navigate through tabs:
   - **Team Load**: View active assignments per developer
   - **Bus Factor**: See code ownership risks
   - **Recent Decisions**: Live feed of triage actions
   - **Configuration**: Adjust confidence threshold

**Key Features to Demonstrate**:
- Warning indicators for overloaded developers (>5 bugs)
- Auto-refresh every 30 seconds
- Confidence scores and reasoning for each assignment
- Single-contributor warnings in Bus Factor view

---

### Scenario 5: Configuration Management

**Objective**: Show immediate configuration changes without restart

**Steps**:
1. Open Configuration panel in dashboard
2. Adjust confidence threshold from 60% to 75%
3. Toggle Draft PR mode off
4. Send test webhook
5. Verify new settings apply immediately

**Expected Result**:
- Configuration updates persist to database
- Next webhook uses new threshold
- No server restart required

---

## Testing the System

### Run Integration Tests
```bash
cd backend
source venv/bin/activate
pytest test_integration.py -v
```

### Run Draft PR Tests
```bash
pytest test_draft_pr_generator.py -v
```

### Run All Tests
```bash
pytest -v
```

## Troubleshooting

### Webhook Signature Verification Fails
- Ensure `GITHUB_WEBHOOK SECRET` matches between GitHub settings and `.env`
- For demo purposes, you can disable verification in development

### Slack Notifications Not Sending
- Verify `SLACK_BOT_TOKEN` is valid
- Check bot has `chat:write` permission
- Ensure user mappings exist in database

### AI Analysis Times Out
- Verify `GEMINI_API_KEY` is set
- Check API quota limits
- Timeout set to 30s by default in `.env`

### Dashboard Not Loading
- Ensure backend is running on port 8000
- Check frontend proxy configuration in `vite.config.ts`
- Verify CORS settings allow localhost

## Success Metrics

After running the demo, verify:
- ✅ Webhooks processed within 5 seconds
- ✅ High confidence bugs (>85%) generate draft PRs
- ✅ Low confidence bugs (<60%) escalate to human
- ✅ Notifications delivered within 2 seconds
- ✅ Dashboard updates in real-time
- ✅ Configuration changes apply without restart
