# Requirements Document

## Introduction

Ticket-Triage is an autonomous bug triage agent that analyzes bugs, identifies exact code locations, calculates true code ownership from git history, and drafts fixes—all before a human looks at it. The system combines a headless triage engine with a visual command center dashboard to provide both automated notifications and organizational intelligence.

## Glossary

- **Triage_Engine**: The core backend service that processes GitHub webhooks and performs autonomous bug analysis
- **Command_Center**: The React-based dashboard that visualizes team health and triage decisions
- **Expertise_Score**: A weighted calculation of code ownership based on git history, commit frequency, and recency
- **Confidence_Threshold**: A numerical score (0-100) that determines whether to auto-assign or route to human triage
- **Draft_PR_Mode**: AI-generated code fixes for high-confidence bugs (>85% confidence)
- **Bus_Factor**: Risk assessment of knowledge concentration (files with single owners)
- **Triage_Decision**: The complete analysis result including assignee, confidence, and reasoning

## Requirements

### Requirement 1: Bug Ingestion and Processing

**User Story:** As a development team, I want bugs to be automatically ingested from GitHub, so that no manual ticket creation is required.

#### Acceptance Criteria

1. WHEN a GitHub issue is created with a stack trace, THE Triage_Engine SHALL receive the webhook within 30 seconds
2. WHEN a bug report contains a stack trace, THE Triage_Engine SHALL parse file paths and line numbers from the trace
3. WHEN duplicate issues arrive within 10 minutes, THE Triage_Engine SHALL detect and consolidate them
4. WHEN a bug report lacks a stack trace, THE Triage_Engine SHALL extract error keywords and severity signals from the description

### Requirement 2: Code Ownership Analysis

**User Story:** As a developer, I want to be assigned bugs based on actual code expertise, so that I receive relevant work I can effectively handle.

#### Acceptance Criteria

1. WHEN analyzing code ownership, THE Triage_Engine SHALL execute git blame with rename and move tracking (-C -C -M flags)
2. WHEN calculating expertise scores, THE Triage_Engine SHALL weight recent commits higher than older ones
3. WHEN processing git history, THE Triage_Engine SHALL filter out bot accounts and automated merge commits
4. WHEN the primary author is inactive, THE Triage_Engine SHALL identify secondary contributors as fallback assignees
5. WHEN no active contributors exist for a file, THE Triage_Engine SHALL route to human triage queue

### Requirement 3: Intelligent Assignment Engine

**User Story:** As an engineering manager, I want confident assignments to be automated and uncertain ones to be escalated, so that developers receive appropriate work without false assignments.

#### Acceptance Criteria

1. WHEN calculating assignment confidence, THE Triage_Engine SHALL generate a score from 0-100 based on code ownership and bug clarity
2. WHEN confidence is below 60%, THE Triage_Engine SHALL route to human triage queue instead of auto-assigning
3. WHEN an assignment is made, THE Triage_Engine SHALL record the decision to prevent reassignment loops
4. WHEN multiple developers have similar expertise scores, THE Triage_Engine SHALL select based on current workload

### Requirement 4: User Management and Mapping

**User Story:** As a system administrator, I want to manage developer profiles and activity status, so that assignments go to active team members.

#### Acceptance Criteria

1. THE Command_Center SHALL provide an interface to map git author emails to Slack user IDs
2. THE Command_Center SHALL allow marking users as active or inactive
3. WHEN looking up assignees, THE Triage_Engine SHALL exclude inactive users from consideration
4. THE Command_Center SHALL display current user mappings in a searchable table

### Requirement 5: Real-time Notifications

**User Story:** As a developer, I want to receive immediate notification when assigned a bug with full context, so that I can start working without investigation.

#### Acceptance Criteria

1. WHEN a bug is assigned, THE Triage_Engine SHALL send a Slack DM within 5 seconds
2. WHEN sending notifications, THE Triage_Engine SHALL include file path, line number, expertise reason, and confidence score
3. WHEN confidence is low, THE Triage_Engine SHALL notify the on-call engineer for manual triage
4. WHEN a Draft PR is generated, THE notification SHALL include a link to the proposed fix

### Requirement 6: AI-Powered Analysis

**User Story:** As a developer, I want the system to understand the bug context and explain it in plain English, so that I can quickly grasp the problem.

#### Acceptance Criteria

1. WHEN analyzing a bug report, THE Triage_Engine SHALL use Gemini 3 to identify likely affected files beyond the stack trace
2. WHEN code context is available, THE Triage_Engine SHALL generate plain English explanations of the likely issue
3. WHEN stack traces are complex, THE Triage_Engine SHALL identify the most relevant frames for human attention
4. WHEN error messages are cryptic, THE Triage_Engine SHALL translate them into actionable descriptions

### Requirement 7: Draft PR Generation

**User Story:** As a developer, I want high-confidence bugs to come with suggested fixes, so that I can review and merge instead of investigating from scratch.

#### Acceptance Criteria

1. WHEN confidence exceeds 85%, THE Triage_Engine SHALL generate a draft code fix
2. WHEN creating draft fixes, THE Triage_Engine SHALL limit changes to single files with fewer than 20 lines modified
3. WHEN a draft PR is created, THE Triage_Engine SHALL label it clearly as "DRAFT - Review Required"
4. WHEN generating fixes, THE Triage_Engine SHALL include explanatory comments describing the change reasoning
5. THE Command_Center SHALL display draft PRs with approval/rejection options

### Requirement 8: Team Health Dashboard

**User Story:** As an engineering manager, I want to visualize team workload and knowledge risks, so that I can prevent burnout and knowledge silos.

#### Acceptance Criteria

1. THE Command_Center SHALL display real-time bug counts per developer in a bar chart format
2. WHEN a developer has more than 5 active bugs, THE Command_Center SHALL highlight them with a warning indicator
3. THE Command_Center SHALL show a live feed of recent triage decisions with confidence scores
4. THE Command_Center SHALL refresh automatically every 30 seconds to show current state

### Requirement 9: Bus Factor Monitoring

**User Story:** As an engineering manager, I want to identify knowledge concentration risks, so that I can plan knowledge sharing and prevent single points of failure.

#### Acceptance Criteria

1. THE Command_Center SHALL analyze git history to identify files with single active contributors
2. WHEN critical files have only one owner, THE Command_Center SHALL display them in a "Knowledge Risk" section
3. THE Command_Center SHALL calculate and display the percentage of files each developer uniquely owns
4. WHEN bus factor risks are detected, THE Command_Center SHALL suggest junior developers for knowledge transfer assignments

### Requirement 10: System Health and Persistence

**User Story:** As a system administrator, I want the system to be reliable and maintain state across restarts, so that triage history and configuration persist.

#### Acceptance Criteria

1. THE Triage_Engine SHALL respond to health check requests within 1 second
2. THE Triage_Engine SHALL persist assignment history, user mappings, and expertise cache in SQLite
3. WHEN the system restarts, THE Triage_Engine SHALL restore all configuration and historical data
4. THE Triage_Engine SHALL log all triage decisions with reasoning for debugging and audit purposes
5. WHEN API dependencies fail, THE Triage_Engine SHALL degrade gracefully and notify administrators

### Requirement 11: Configuration Management

**User Story:** As a system administrator, I want to configure system behavior through the dashboard, so that I can adjust thresholds and settings without code changes.

#### Acceptance Criteria

1. THE Command_Center SHALL provide controls to adjust the confidence threshold (default 60%)
2. THE Command_Center SHALL allow enabling/disabling Draft PR Mode
3. THE Command_Center SHALL provide settings for duplicate detection time window (default 10 minutes)
4. WHEN configuration changes are made, THE Command_Center SHALL apply them immediately without restart

### Requirement 12: Performance and Integration

**User Story:** As a development team, I want the triage system to be fast and integrate seamlessly with our existing tools, so that it enhances rather than disrupts our workflow.

#### Acceptance Criteria

1. WHEN processing a bug report, THE Triage_Engine SHALL complete end-to-end triage within 10 seconds
2. WHEN executing git blame operations, THE Triage_Engine SHALL complete analysis within 5 seconds for repositories under 10,000 commits
3. WHEN calling external APIs (GitHub, Slack, Gemini), THE Triage_Engine SHALL implement timeout and retry logic
4. THE Command_Center SHALL load initial data within 2 seconds and update in real-time
5. WHEN GitHub webhooks are received, THE Triage_Engine SHALL verify signatures before processing