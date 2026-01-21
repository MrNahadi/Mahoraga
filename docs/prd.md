---

stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']

inputDocuments: ['_bmad-output/analysis/brainstorming-session-2026-01-19.md']

workflowType: 'prd'

documentCounts:

  briefs: 0

  research: 0

  brainstorming: 1

  projectDocs: 0

projectType: 'greenfield'

classification:

  projectType: 'Backend Service + Integrations'

  primaryInterface: 'Headless (Slack/GitHub/Jira webhooks & notifications)'

  secondaryInterface: 'Dashboard (Tier 2/Post-MVP)'

  domain: 'Developer Tools / DevOps Productivity'

  targetMarket: 'B2B SaaS - Internal Engineering Teams'

  complexity: 'Medium-High'

  projectContext: 'greenfield'

  scopeTiers:

    tier1_mvp: ['Core triage engine', 'Expertise scoring', 'Stack trace parsing', 'Bot ignore list', 'git blame -C -C -M', 'Confidence threshold', 'Inactive user check', 'Basic Slack/GitHub integration']

    tier2_wow: ['Pre-Flight Code Locator', 'Draft PR Mode', 'Mental Bisect', 'Diff-to-English Translator', 'Revenue-at-Risk Calculator', 'Bus Factor Monitor']

    tier3_production: ['PII Scrubber', 'Cost Controls', 'Health Dashboard', 'Lobotomy Fallback', 'Vector Deduplication', 'Rate Limiter']

    tier4_delightful: ['Tilt Protection', 'Squad Pairing', 'File Elo Ratings', 'Good Samaritan Immunity']

---

# Product Requirements Document - Ticket-Triage

**Author:** Nahadi  

**Date:** 2026-01-19  

**Project:** Mahoraga

## Executive Summary

**Product:** Ticket-Triage — An autonomous bug triage agent for engineering teams.

**Positioning:** *"Jira routes tickets. Ticket-Triage solves them."*

**Core Innovation:** Unlike traditional triage tools that simply route bugs to developers, Ticket-Triage analyzes the bug, identifies the exact code location, calculates true code ownership from git history, and drafts a fix—all before a human looks at it.

**Target Users:** Internal engineering teams at software companies (B2B SaaS).

**MVP Scope (Hackathon):**

- Core triage pipeline: GitHub webhook → Stack trace parsing → Expertise scoring → Slack notification

- Wow Factor: Draft PR Mode — AI-generated code fixes for high-confidence bugs

**Key Differentiators:**

1. **Expertise Scoring** — Weighted ownership from git history, not just "last commit"

2. **Confidence Threshold** — Routes uncertain bugs to humans instead of hallucinating

3. **Draft PR Mode** — Generates actual code fixes, not just diagnosis

**Technology:** Python (FastAPI) + Gemini 3 + GitHub API + Slack SDK + SQLite

## Success Criteria

### User Success

**The "Worth It" Moment:** A developer receives a bug assignment with full context—the exact file, the suspected line of code, and *why* they were chosen—within seconds of the ticket being created. No detective work required.

| User Outcome | Measurable Target | Validation |

|--------------|-------------------|------------|

| **Time to Assignment** | < 10 seconds (Ingest → Notify) | Stopwatch during demo |

| **Assignment Confidence** | > 60% confidence score | Confidence displayed in Slack notification |

| **Context Completeness** | File path + line number + expertise reason | All three present in notification |

| **Correct Routing** | Human override < 40% of assignments | Track reassignments in demo |

**Emotional Success:**

- Junior Dev: *"It told me exactly where to look and why I was chosen"*

- On-Call Engineer: *"I didn't have to play detective at 3am"*

- Engineering Manager: *"I can see who owns what without asking"*

### Business Success

| Horizon | Success Definition | Measurable Target |

|---------|-------------------|-------------------|

| **Hackathon (Weekend)** | Differentiation from Jira/competitors | Demo showcases Draft PR Mode + Mental Bisect |

| **Hackathon (Judges)** | "Wow Factor" reaction | Judges say "I've never seen that before" |

| **3-Month Post-Hack** | Production-viable prototype | Tier 3 features complete (PII, Cost Controls) |

| **12-Month Vision** | B2B SaaS with paying customers | First enterprise pilot deployment |

**Positioning Validation:** *"Jira routes tickets. Ticket-Triage solves them."* — Demo must prove the "solves" claim.

### Technical Success

| Metric | MVP Target (Weekend) | North Star (Production) |

|--------|---------------------|------------------------|

| **Triage Latency** | < 10 seconds (Ingest → Notify) | < 2 seconds (Real-time) |

| **Assignment Confidence** | > 60% confidence score | > 90% (with learning loop) |

| **"Pre-Solving" Rate** | 100% demo tickets get Draft PR or Bisect | 30% of real tickets get Draft PR |

| **Reliability** | Handles demo scenarios (bot, tsunami) | 99.9% uptime with Lobotomy fallback |

| **Graceful Degradation** | Not required (Tier 3) | Full circuit breaker pattern |

## Product Scope

### MVP — Minimum Viable Product (Weekend Build)

**Definition of Done:** End-to-end demo that proves autonomous triage works.

| Feature | Priority | Hours | Why MVP |

|---------|----------|-------|---------|

| GitHub webhook listener | P0 | 0-2 | Entry point for tickets |

| Stack trace parser | P0 | 2-3 | Accuracy—find the RIGHT file |

| `git blame -C -C -M` wrapper | P0 | 2-3 | Handle renames/moves |

| Expertise Score calculation | P0 | 3-4 | Core differentiator |

| Bot/merge commit ignore list | P0 | 3-4 | Prevent CTO spam |

| Confidence threshold + human fallback | P0 | 4-5 | Safety net |

| Inactive user check | P1 | 4-5 | No ghost assignments |

| Slack notification with context | P0 | 5-6 | Visible output |

### Growth Features — Wow Factor (Hours 6-8)

**Definition of Done:** At least 1-2 "judge-impressing" features working in demo.

| Feature | Judge Impact | Demo Potential |

|---------|--------------|----------------|

| **Pre-Flight Code Locator** | 🤯 "It shows the exact bug line?!" | Visual diff highlight |

| **Draft PR Mode** | 🤯 "It WRITES the fix?!" | Live PR creation |

| **Mental Bisect** | 🤯 "It found the breaking commit?!" | Timeline visualization |

**Pick 1-2 for hackathon.** Draft PR Mode recommended for maximum impact.

### Vision — Future Roadmap (Post-Hackathon)

**Tier 3: Production-Ready**

- PII Scrubber (GDPR/SOC2 compliance)

- Spam Loop Detection (prevent infinite tickets)

- Cost Controls (tiered model: regex → cheap LLM → GPT-4)

- Health Check Dashboard

- Lobotomy Fallback Mode (graceful AI degradation)

- Vector Deduplication (ticket tsunami handling)

**Tier 4: Delightful**

- Tilt Protection (easy win after hard bugs)

- Squad Pairing (senior + junior matching)

- File Elo Ratings (codebase difficulty ladder)

- Good Samaritan Immunity (encourage refactoring)

## User Journeys

### Personas

| Persona | Role | Key Pain Points | Core Need |

|---------|------|-----------------|-----------|

| **Alex** | Junior Developer | Ramp-up time, impostor syndrome, unfamiliar code | Empowerment & guidance |

| **Priya** | Engineering Manager | Visibility, load balancing, burnout prevention | Organizational intelligence |

| **Jordan** | On-Call Engineer | 3am pages, incident context, misdirected alerts | Efficiency & sleep protection |

| **Sam** | Product Manager | Customer impact, SLA tracking, communication | Business intelligence |

| **Chris** | Developer Who Quit | (System must handle absence) | Knowledge continuity |

---

### Journey 1: The "Don't Panic" Protocol (Alex - Junior Developer)

**Premise:** The system doesn't just "dump" the bug; it "onboards" Alex to the problem.

**Scene 1: The Notification (The Hook)**

- **Trigger:** Alex receives a Slack DM from Ticket-Triage

- **The Fear:** "Payment calculation? I'll break the checkout."

- **The Calm (Feature: Expertise Explanation):** The bot adds a specific footer: *"Assigned because: You modified the currency_formatter utility 3 days ago, which is where the stack trace terminates."*

- **Impact:** Alex realizes, "Oh, this isn't deep financial logic. It's just that formatting function I wrote." **Fear → Recognition**

**Scene 2: The Deep Dive (The Context)**

- **Action:** Alex clicks "View Analysis"

- **The Context (Feature: Pre-Flight Code Locator):** Instead of a generic file link, the screen highlights Line 42 in `utils.js`

- **Feature: Diff-to-English Translator:** A sidebar says: *"This code attempts to split the currency string but fails on integers. It likely needs a .toString() check before splitting."*

- **Impact:** The problem is demystified. The AI has done the "senior dev" work. **Recognition → Understanding**

**Scene 3: The Resolution (The Action)**

- **Action:** Alex feels confident enough to fix it

- **The Safety Net (Feature: Draft PR Mode):** The interface offers: *"Confidence: 85%. View Draft Fix?"*

- Alex reviews the AI's suggested one-line change. It matches their intuition.

- **Impact:** Alex commits the fix with confidence. **Understanding → Pride**

**Features Validated:** Expertise Explanation, Pre-Flight Code Locator, Diff-to-English Translator, Draft PR Mode

---

### Journey 2: The "Visibility" Protocol (Priya - Engineering Manager)

**Premise:** The system surfaces *organizational intelligence* that was previously invisible.

**Scene 1: The Morning Check-In (The Dashboard)**

- **Trigger:** Priya opens Slack during morning coffee. She sees a digest notification.

- **The Old Pain:** Previously, she'd have to ask each dev "what are you working on?"

- **The Clarity (Feature: Team Dashboard + Weekly Digest):**

  > *"📊 Daily Triage Summary:*

  > - *Alex: 2 bugs (1 resolved, 1 in-progress)*

  > - *Jordan: 0 bugs (on-call, quiet night)*

  > - *Marcus: 5 bugs ⚠️ (3 P1s, load warning)*

  > - *Team avg resolution: 2.1 days"*

- **Impact:** Priya spots Marcus is overloaded without asking. **Confusion → Clarity**

**Scene 2: The Intervention (The Alert)**

- **Trigger:** The digest includes a warning icon next to Marcus

- **The Context (Feature: Load Balancer + Burnout Detection):**

  > *"⚠️ Marcus has received 3 P1 bugs in 48 hours. Suggest redistribution?"*

  > *[Redistribute to Sarah] [Override: Keep] [View Queue]*

- **Impact:** Priya prevents burnout before it happens. **Clarity → Control**

**Scene 3: The Strategic Insight (The Bus Factor)**

- **Trigger:** At the bottom of the digest, a warning appears

- **The Warning (Feature: Bus Factor Monitor):**

  > *"🚨 Knowledge Risk: Sarah is sole contributor to billing-engine/ (47 files). No backup identified."*

  > *[View Ownership Map] [Assign Stretch Bug to Junior]*

- **The Action (Feature: Skill-Building Assignments):** Priya clicks "Assign Stretch Bug to Junior"—the next non-critical billing bug goes to Alex with extended deadline

- **Impact:** Reactive tool becomes proactive org-health system. **Control → Strategic Confidence**

**Features Validated:** Team Dashboard, Weekly Digest, Load Balancer, Burnout Detection, Bus Factor Monitor, Skill-Building Assignments

---

### Journey 3: The "Cold Case" Protocol (Jordan - On-Call + System)

**Premise:** What happens when the AI can't find a clear answer? It degrades gracefully instead of hallucinating.

**Scene 1: The Mystery (Ghost Owner)**

- **Trigger:** A bug report arrives for `legacy_auth.c`

- **The Problem:** Git blame reveals primary author is "Chris," who left 2 years ago

- **The Intelligence (Feature: Legacy Fallback Protocol):** System detects Chris is "Inactive" via directory check. It traverses git history to find secondary contributor or team lead.

**Scene 2: The Ambiguity (Low Confidence)**

- **Trigger:** Another bug arrives: "System feels slow today"

- **The Problem:** No stack trace, no file reference, vague sentiment

- **The Safety Net (Feature: Confidence Threshold):** AI calculates Confidence Score of 0.3 (below 0.6 threshold). It refuses to auto-assign.

**Scene 3: The Human Handoff (The Resolution)**

- **Action:** Jordan (On-Call) gets a "Triage Required" notification

- **The Context (Feature: Context Bundle):**

  > *"Low Confidence (30%). Possible database latency based on keyword 'slow', but no files detected."*

  > *"Owner 'Chris' is inactive. Proposed Assignee: Sarah (Secondary Contributor). Confirm?"*

- **Impact:** Jordan doesn't investigate who Chris was or why the bug is vague. System presents Best Guess and asks for Verification. Jordan clicks "Assign to Sarah."

**Features Validated:** Legacy Fallback Protocol, Confidence Threshold, Human-in-the-Loop, Context Bundle

---

### Journey 4: The "Revenue Shield" Protocol (Sam - Product Manager)

**Premise:** The system surfaces *business intelligence* that helps PMs protect customer relationships.

**Scene 1: The Escalation Trigger (Customer Pain)**

- **Trigger:** Sam gets a Slack alert with a special 💰 icon

- **The Old Pain:** Previously, Sam only learned about customer-impacting bugs after direct complaints

- **The Intelligence (Feature: Escalation Trigger + Customer Impact Flag):**

  > *"💰 Customer Escalation Alert:*

  > - *Bug: 'Checkout timeout on large orders'*

  > - *Mentioned by: Acme Corp (Enterprise Tier) — 3 times in 48 hours*

  > - *Customer Tier: Enterprise ($50K ARR)*

  > - *Auto-escalated from P2 → P1"*

- **Impact:** Sam knows *before* the angry email. **Blindsided → Prepared**

**Scene 2: The Business Context (The Numbers)**

- **Action:** Sam clicks "View Impact Analysis"

- **The Context (Feature: Revenue-at-Risk Calculator):**

  > *"⚠️ Potential Revenue Impact:*

  > - *Affected Flow: Checkout (Enterprise)*

  > - *Error Rate: 12% of large orders failing*

  > - *Estimated Loss: $4,200/hour*

  > - *Time in Queue: 6 hours"*

- **Impact:** Sam can tell CTO: "This is a $25K/day problem." **Prepared → Armed with Data**

**Scene 3: The Customer Communication (The Resolution)**

- **Action:** Sam needs to update Acme Corp's account manager

- **The Assist (Feature: Changelog Auto-Drafter + ETA Prediction):**

  > *"📝 Suggested Customer Update:*

  > - *'We've identified the checkout timeout issue affecting large orders.'*

  > - *'Root cause: Database connection pooling under high load.'*

  > - *'ETA: Fix deploying within 4-6 hours.'*

  > - *'Status page updated: [Link]'"*

- **Impact:** Professional customer update in 2 minutes instead of 2 hours. **Armed with Data → Customer Hero**

**Features Validated:** Customer Impact Flag, Escalation Trigger, Revenue-at-Risk Calculator, ETA Prediction, Changelog Auto-Drafter

---

### Journey Requirements Summary

| Capability Area | Journey 1 (Alex) | Journey 2 (Priya) | Journey 3 (Jordan) | Journey 4 (Sam) |

|-----------------|------------------|-------------------|--------------------|-----------------| 

| **Core Triage Engine** | ✅ | ✅ | ✅ | ✅ |

| **Expertise Scoring** | ✅ | | ✅ | |

| **Confidence Threshold** | | | ✅ | |

| **Slack Integration** | ✅ | ✅ | ✅ | ✅ |

| **Pre-Flight Code Locator** | ✅ | | | |

| **Draft PR Mode** | ✅ | | | |

| **Team Dashboard** | | ✅ | | |

| **Load Balancer** | | ✅ | | |

| **Bus Factor Monitor** | | ✅ | | |

| **Legacy Fallback** | | | ✅ | |

| **Human-in-the-Loop** | | | ✅ | |

| **Customer Impact Flag** | | | | ✅ |

| **Revenue Calculator** | | | | ✅ |

| **ETA Prediction** | | | | ✅ |

## Innovation & Novel Patterns

### Primary Innovation: The "Pre-Solver" Paradigm

**What exists today:** Bug triage tools route tickets to humans who then investigate, diagnose, and fix.

**What we're building:** An autonomous agent that identifies the bug location, understands the code, and drafts a fix — *before a human even looks at it.*

**The paradigm shift:**

| Traditional Triage | Ticket-Triage |

|-------------------|---------------|

| Route to human | Route + Diagnose + Draft Fix |

| Information broker | Action-taker |

| "Here's who should look" | "Here's the fix, please review" |

**Positioning Statement:** *"Jira routes tickets. Ticket-Triage solves them."*

### Innovation Validation

| Risk | Validation Approach | Fallback |

|------|--------------------| ---------|

| AI generates wrong fix | Confidence threshold (>85% to show draft) | Show diagnosis only, no draft |

| Fix breaks more code | Human review required before merge | Clear "Draft - Review Required" labeling |

| Scope creep (AI tries to fix everything) | Limit to single-file, <20 line changes | Route complex fixes to human |

### Competitive Moat

**Why this is hard to copy:**

1. **Multi-capability chain:** Requires deep git history analysis (expertise scoring) + LLM code understanding + PR generation

2. **Trust calibration:** Confidence threshold tuning requires real-world feedback loops

3. **Integration depth:** GitHub API + Slack + git blame creates switching costs

### Secondary Innovation: Cross-Pollinated Intelligence

Novel patterns borrowed from other domains (identified in brainstorming):

| Source Industry | Concept | Application |

|----------------|---------|-------------|

| 🏥 ER Triage | Color-coded severity | Lightweight "nurse" LLM tags before routing |

| 🎮 Game Matchmaking | Tilt Protection | Easy win after hard bugs (burnout prevention) |

| ✈️ Air Traffic Control | Holding Pattern | Dev at capacity → ticket "holds," manager notified |

### Demo "Wow" Moment

**The pitch climax (1:45-2:15):**

> *"But we don't just assign. We PRE-SOLVE. Watch it draft a fix."*

**Judge reaction target:** "I've never seen a triage tool write code before."

## Backend Service Requirements

### Technology Stack

| Component | Technology | Role |

|-----------|------------|------|

| **Ingestion** | Python (FastAPI/Flask) | Receives GitHub Webhooks |

| **Analysis** | Google Gemini 3 | Stack trace parsing, code logic analysis |

| **Git Ops** | `gitpython` / GitHub API | `git blame -w -C -C -M`, PR creation |

| **Storage** | SQLite | User mapping, assignment history, simple caching |

| **Notification** | Slack SDK | Alerts and interactive buttons |

### Architecture: Simplified Pipeline

```

┌─────────────────────────────────────────────────────────────────────────┐

│                           MVP PIPELINE                                   │

├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤

│   INGEST    │   ANALYZE   │   ASSIGN    │   NOTIFY    │   ACTION        │

│             │             │             │             │                 │

│ • GitHub    │ • Parse     │ • Expertise │ • Slack DM  │ • Draft PR      │

│   Webhook   │   stack     │   Score     │ • Context   │   (if >85%     │

│ • Dedup     │   trace     │ • Fallback  │   Bundle    │   confidence)  │

│   (SQLite)  │ • Gemini 3  │   chain     │             │                 │

│             │   analysis  │             │             │                 │

└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘

```

### Integration Points

| Integration | Protocol | MVP Scope |

|-------------|----------|-----------|

| **GitHub → Ticket-Triage** | Webhook (Issues, PRs) | ✅ MVP |

| **Ticket-Triage → GitHub** | REST API (git blame, create PR) | ✅ MVP |

| **Ticket-Triage → Slack** | Bot API (messages, buttons) | ✅ MVP |

| **Ticket-Triage → Gemini** | REST API (Gemini 3) | ✅ MVP |

| **Jira → Ticket-Triage** | Webhook | ❌ Post-MVP |

### Data Model (SQLite)

```sql

-- Assignment History (Loop Detection)

CREATE TABLE assignments (

    id INTEGER PRIMARY KEY,

    issue_id TEXT NOT NULL,

    assigned_to TEXT NOT NULL,

    confidence REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

-- User Mapping (Git Email → Slack ID)

CREATE TABLE users (

    git_email TEXT PRIMARY KEY,

    slack_id TEXT NOT NULL,

    display_name TEXT,

    is_active BOOLEAN DEFAULT TRUE

);

-- Expertise Cache (Avoid repeated git blame)

CREATE TABLE expertise_cache (

    file_path TEXT NOT NULL,

    git_email TEXT NOT NULL,

    score REAL NOT NULL,

    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (file_path, git_email)

);

```

### Authentication Model

| Credential | Purpose | Storage |

|------------|---------|---------|

| GitHub App Private Key | Webhook verification, API calls, PR creation | Environment variable |

| Slack Bot Token | Post messages, interactive buttons | Environment variable |

| Gemini API Key | Gemini 3 calls | Environment variable |

**Note:** No user authentication needed — service-account model. GitHub App acts on behalf of installation.

### API Endpoints (FastAPI)

| Endpoint | Method | Purpose |

|----------|--------|---------|

| `/webhook/github` | POST | Receive GitHub issue/PR events |

| `/health` | GET | Basic health check for demo |

| `/api/users` | GET/POST | Manage user mappings (manual for MVP) |

### MVP Simplifications (Deferred to Tier 3)

| Feature | MVP Approach | Production Approach |

|---------|--------------|---------------------|

| **Deduplication** | SQLite check (last 10 min) | Vector similarity + parent-child linking |

| **PII Scrubbing** | Assume demo data is safe | Regex + LLM scrubber before API calls |

| **Cost Control** | Manual monitoring | Tiered model (regex → cheap LLM → GPT-4) |

| **Rate Limiting** | None | Per-user, per-org limits |

| **Circuit Breakers** | None | Lobotomy fallback mode |

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-Solving + Demo MVP (Balanced)

**Core Premise:** Deliver a working triage pipeline AND one "category-defining" feature that proves the positioning statement: *"Jira routes tickets. Ticket-Triage solves them."*

**Resource Requirements:**

- Solo developer (Nahadi)

- 10-hour hackathon window

- External dependencies: GitHub API, Gemini API, Slack API

### MVP Feature Set (Phase 1 — Hours 0-8)

**Definition of Done:** End-to-end demo showing bug → triage → assignment → Draft PR

#### Core Pipeline (Hours 0-6)

| Feature | Priority | Est. Hours | Journey Supported |

|---------|----------|------------|-------------------|

| GitHub webhook listener | P0 | 0-1 | All |

| Stack trace parser | P0 | 1-2 | Journey 1 (Alex) |

| `git blame -C -C -M` wrapper | P0 | 2-3 | Journey 1, 3 |

| Expertise Score calculation | P0 | 3-4 | Journey 1, 3 |

| Bot/merge commit ignore list | P0 | 4-4.5 | All |

| Confidence threshold + routing | P0 | 4.5-5 | Journey 3 (Jordan) |

| SQLite setup (users, history) | P0 | 5-5.5 | All |

| Slack notification with context | P0 | 5.5-6 | All |

#### Wow Factor (Hours 6-8)

| Feature | Priority | Est. Hours | Judge Impact |

|---------|----------|------------|--------------|

| **Draft PR Mode** | P1 | 6-8 | 🤯 "It WRITES the fix?!" |

**Scope Constraint:** Draft PR limited to:

- Single-file changes only

- < 20 lines modified

- Confidence > 85% to show draft

- Clear "DRAFT - Review Required" labeling

#### Demo Polish (Hours 8-10)

| Activity | Est. Hours |

|----------|------------|

| Error handling & edge cases | 8-9 |

| Demo script rehearsal | 9-9.5 |

| README & architecture diagram | 9.5-10 |

### Post-MVP Features

#### Phase 2: Growth (Post-Hackathon, Week 1-4)

| Feature | Business Value | Dependency |

|---------|---------------|------------|

| Mental Bisect | "Found the breaking commit" | Core pipeline |

| Pre-Flight Code Locator | Visual diff highlight | Core pipeline |

| Team Dashboard | Manager visibility | SQLite + frontend |

| Jira Integration | Expand market | Webhook abstraction |

#### Phase 3: Production (Month 2-3)

| Feature | Enterprise Requirement |

|---------|----------------------|

| PII Scrubber | GDPR/SOC2 compliance |

| Cost Controls | Budget management |

| Lobotomy Fallback | AI downtime resilience |

| Vector Deduplication | Ticket tsunami handling |

| Health Dashboard | Ops visibility |

#### Phase 4: Delightful (Month 4+)

| Feature | User Delight |

|---------|-------------|

| Tilt Protection | Burnout prevention |

| Squad Pairing | Mentorship enablement |

| File Elo Ratings | Gamification |

| Good Samaritan Immunity | Encourage refactoring |

### Risk Mitigation Strategy

| Risk | Likelihood | Impact | Mitigation |

|------|------------|--------|------------|

| **Gemini down during demo** | Low | Critical | Pre-record backup video |

| **Draft PR generates bad code** | Medium | High | 85% confidence threshold, clear "Draft" label |

| **Wrong file detected** | Medium | Medium | Stack trace parsing + human fallback |

| **Time overrun on Tier 1** | Medium | High | Cut Slack buttons, skip SQLite cache |

| **GitHub API rate limit** | Low | Medium | Use test repo with limited history |

### Contingency Plan

**If behind schedule at Hour 6:**

1. Drop: Slack interactive buttons (use text-only notifications)

2. Drop: Expertise caching (recalculate each time)

3. Keep: Draft PR Mode (this IS the demo)

**If ahead of schedule:**

1. Add: Pre-Flight Code Locator (show exact line in Slack)

2. Add: Slack interactive buttons ("Approve Assignment" / "Reassign")

## Functional Requirements

### Bug Ingestion

- **FR1:** System can receive GitHub issue webhook events in real-time

- **FR2:** System can parse stack traces from bug report body to extract file paths and line numbers

- **FR3:** System can detect duplicate issues within a configurable time window (default: 10 minutes)

- **FR4:** System can extract error messages, keywords, and severity signals from bug descriptions

### Code Ownership Analysis

- **FR5:** System can execute `git blame -w -C -C -M` to identify code authors with rename/move tracking

- **FR6:** System can calculate expertise scores based on commit frequency, recency, and line ownership

- **FR7:** System can filter out bot accounts and automated commits from ownership calculations

- **FR8:** System can filter out merge commits to identify actual code authors

- **FR9:** System can identify secondary contributors when primary author is unavailable

- **FR10:** System can detect inactive users (left company) and exclude from assignment

### Assignment Engine

- **FR11:** System can calculate confidence scores for proposed assignments

- **FR12:** System can route low-confidence assignments (< 60%) to human triage queue

- **FR13:** System can record assignment history to prevent reassignment loops

- **FR14:** System can select assignee based on expertise score ranking

### User Management

- **FR15:** Admin can map git author emails to Slack user IDs

- **FR16:** Admin can mark users as active/inactive

- **FR17:** System can lookup Slack ID from git email for notifications

### Notifications

- **FR18:** System can send Slack DM to assigned developer with bug context

- **FR19:** Notification can include: file path, line number, expertise reason, confidence score

- **FR20:** System can send "Triage Required" notification for low-confidence assignments

- **FR21:** On-Call Engineer can confirm or override proposed assignment via Slack

### AI Analysis (Gemini 3)

- **FR22:** System can analyze bug description to identify likely affected files

- **FR23:** System can explain code context in plain English (Diff-to-English)

- **FR24:** System can identify the likely root cause from stack trace and code

### Draft PR Generation (Wow Factor)

- **FR25:** System can generate a draft code fix for high-confidence bugs (> 85%)

- **FR26:** Draft PR can only modify single files with < 20 lines changed

- **FR27:** System can create GitHub Pull Request with draft fix and explanation

- **FR28:** Draft PR can include clear "DRAFT - Review Required" labeling

- **FR29:** Developer can view suggested fix before accepting/rejecting

### Persistence

- **FR30:** System can store assignment history for loop detection

- **FR31:** System can cache expertise scores to avoid repeated git blame operations

- **FR32:** System can store user mappings (git email → Slack ID)

### System Health

- **FR33:** System can respond to health check requests

- **FR34:** System can log all triage decisions with reasoning for debugging

## Non-Functional Requirements

### Performance

| NFR | Requirement | Measurement |

|-----|-------------|-------------|

| **NFR1** | End-to-end triage latency < 10 seconds | Timestamp from webhook receipt to Slack notification |

| **NFR2** | Stack trace parsing completes < 1 second | Local processing time |

| **NFR3** | Git blame operation completes < 5 seconds | For repos with < 10,000 commits |

| **NFR4** | Gemini API call completes < 8 seconds | Including retry on first timeout |

| **NFR5** | Draft PR generation (if triggered) completes < 15 seconds | File analysis + PR creation |

### Security

| NFR | Requirement | Measurement |

|-----|-------------|-------------|

| **NFR6** | API keys (GitHub, Slack, OpenAI) stored in environment variables | No hardcoded secrets in codebase |

| **NFR7** | GitHub webhook signature verified before processing | HMAC validation on every request |

| **NFR8** | No PII logged in plaintext | Log sanitization for email addresses |

### Reliability

| NFR | Requirement | Measurement |

|-----|-------------|-------------|

| **NFR9** | System recovers from Gemini timeout without crashing | Graceful error handling |

| **NFR10** | Demo completes successfully 3 times in rehearsal | Pre-demo validation |

| **NFR11** | SQLite database persists across server restarts | Data survives reboot |

### Integration

| NFR | Requirement | Measurement |

|-----|-------------|-------------|

| **NFR12** | GitHub webhook events processed within 30 seconds of receipt | GitHub's timeout threshold |

| **NFR13** | Slack messages delivered within 5 seconds of decision | Slack API response time |

| **NFR14** | GitHub PR created successfully when confidence > 85% | PR appears in repository |

### Constraints (MVP-Specific)

| Constraint | Description |

|------------|-------------|

| **C1** | Single repository support only (no multi-repo) |

| **C2** | English language bug reports only |

| **C3** | Google Gemini 3 model only (no model fallback) |

| **C4** | Maximum 10 concurrent webhook events |