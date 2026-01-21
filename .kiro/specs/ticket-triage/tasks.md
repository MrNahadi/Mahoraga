# Implementation Plan: Mahoraga

## Overview

This implementation plan breaks down the Mahoraga autonomous bug triage system into discrete coding tasks. The approach follows a backend-first strategy to establish the core triage pipeline, then adds the React Command Center for visualization and configuration. Each task builds incrementally toward a working demo system.

## Tasks

- [x] 1. Project Setup and Core Infrastructure
  - Create monorepo structure with backend/ and frontend/ directories
  - Set up FastAPI project with SQLite database
  - Configure environment variables for API keys (GitHub, Slack, Gemini)
  - Initialize React project with Vite, TypeScript, and Tailwind CSS
  - Set up basic CI/CD configuration
  - _Requirements: 10.2, 12.5_

- [x] 1.1 Write property test for environment configuration
  - **Property 31: Restart Data Recovery**
  - **Validates: Requirements 10.3**

- [x] 2. Database Schema and Models
  - Create SQLite database schema (users, assignments, expertise_cache, triage_decisions, system_config)
  - Implement SQLAlchemy models for all entities
  - Create database migration system
  - Add database connection management with connection pooling
  - _Requirements: 10.2, 10.3_

- [x] 2.1 Write property test for data persistence
  - **Property 30: Data Persistence Round Trip**
  - **Validates: Requirements 10.2**

- [x] 3. GitHub Webhook Handler
  - Implement FastAPI endpoint for GitHub webhook reception
  - Add webhook signature verification using HMAC-SHA256
  - Create issue and PR event parsing logic
  - Implement duplicate detection within 10-minute window
  - Add async job queuing for triage processing
  - _Requirements: 1.1, 1.3, 12.5_

- [x] 3.1 Write property test for webhook signature verification
  - **Property 36: Webhook Signature Verification**
  - **Validates: Requirements 12.5**

- [x] 3.2 Write property test for duplicate detection
  - **Property 2: Duplicate Detection Consistency**
  - **Validates: Requirements 1.3**

- [x] 4. Stack Trace Parser
  - Implement multi-language stack trace parsing (Python, JavaScript, Java)
  - Create file path and line number extraction logic
  - Add error message and exception type identification
  - Implement stack frame relevance ranking algorithm
  - Handle edge cases (malformed traces, missing files)
  - _Requirements: 1.2, 6.3_

- [x] 4.1 Write property test for stack trace parsing
  - **Property 1: Stack Trace Parsing Completeness**
  - **Validates: Requirements 1.2**

- [x] 4.2 Write property test for stack frame ranking
  - **Property 19: Stack Frame Relevance Ranking**
  - **Validates: Requirements 6.3**

- [x] 5. Git Analysis Engine
  - Implement git blame execution with -w -C -C -M flags
  - Create expertise score calculation algorithm with recency weighting
  - Add bot account and merge commit filtering
  - Implement inactive user detection and fallback logic
  - Create expertise caching system to avoid repeated git operations
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 5.1 Write property test for git blame command correctness
  - **Property 4: Git Blame Command Correctness**
  - **Validates: Requirements 2.1**

- [x] 5.2 Write property test for expertise score recency weighting
  - **Property 5: Expertise Score Recency Weighting**
  - **Validates: Requirements 2.2**

- [x] 5.3 Write property test for bot account filtering
  - **Property 6: Bot Account Filtering**
  - **Validates: Requirements 2.3**

- [x] 6. Checkpoint - Core Backend Pipeline
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. AI Analysis Service
  - Integrate Google Gemini 3 API for bug analysis
  - Implement code context analysis and plain English explanation generation
  - Add error message translation for cryptic errors
  - Create affected file identification beyond stack traces
  - Implement timeout and retry logic for API calls
  - _Requirements: 6.1, 6.2, 6.4, 12.3_

- [x] 7.1 Write property test for AI analysis invocation
  - **Property 17: AI Analysis Invocation**
  - **Validates: Requirements 6.1**

- [x] 7.2 Write property test for API timeout and retry
  - **Property 35: API Timeout and Retry Implementation**
  - **Validates: Requirements 12.3**

- [x] 8. Assignment Engine
  - Implement confidence score calculation (0-100 range)
  - Create assignment logic combining AI analysis with git expertise
  - Add workload-based tie-breaking for similar expertise scores
  - Implement low confidence routing to human triage queue
  - Create assignment loop prevention system
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 8.1 Write property test for confidence score bounds
  - **Property 9: Confidence Score Bounds**
  - **Validates: Requirements 3.1**

- [x] 8.2 Write property test for low confidence routing
  - **Property 10: Low Confidence Routing**
  - **Validates: Requirements 3.2**

- [x] 8.3 Write property test for assignment loop prevention
  - **Property 11: Assignment Loop Prevention**
  - **Validates: Requirements 3.3**

- [x] 9. Draft PR Generator
  - Implement high-confidence draft fix generation (>85% confidence)
  - Create single-file, <20 lines change constraint enforcement
  - Add GitHub PR creation with draft labeling
  - Implement explanatory comment generation for fixes
  - Handle edge cases and error conditions gracefully
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 9.1 Write property test for high confidence draft generation
  - **Property 21: High Confidence Draft Generation**
  - **Validates: Requirements 7.1**

- [x] 9.2 Write property test for draft fix constraints
  - **Property 22: Draft Fix Constraints**
  - **Validates: Requirements 7.2**

- [x] 9.3 Write property test for draft PR labeling
  - **Property 23: Draft PR Labeling**
  - **Validates: Requirements 7.3**

- [x] 10. Slack Notification Service
  - Implement Slack SDK integration for DM notifications
  - Create notification content with file path, line number, expertise reason, confidence
  - Add draft PR link inclusion when available
  - Implement low confidence escalation to on-call engineer
  - Add retry logic with exponential backoff for failed deliveries
  - _Requirements: 5.2, 5.3, 5.4_

- [x] 10.1 Write property test for notification content completeness
  - **Property 14: Notification Content Completeness**
  - **Validates: Requirements 5.2**

- [x] 10.2 Write property test for low confidence escalation
  - **Property 15: Low Confidence Escalation**
  - **Validates: Requirements 5.3**

- [x] 11. Backend API Endpoints
  - Create dashboard data endpoints (team stats, bus factor analysis, health metrics)
  - Implement user management endpoints (CRUD for git email ↔ Slack ID mappings)
  - Add configuration endpoints for system settings
  - Create assignment history and management endpoints
  - Add proper error handling and validation for all endpoints
  - _Requirements: 4.1, 4.2, 11.1, 11.2, 11.3_

- [x] 11.1 Write unit tests for API endpoints
  - Test all CRUD operations and error conditions
  - _Requirements: 4.1, 4.2, 11.1, 11.2, 11.3_

- [x] 12. Checkpoint - Backend Complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. React Frontend Setup
  - Initialize React project with TypeScript and Vite
  - Set up Tailwind CSS with custom design system from branding.json
  - Install and configure shadcn/ui components
  - Set up TanStack Query for API state management
  - Configure Recharts for data visualization
  - Create routing structure and layout components
  - _Requirements: 8.1, 8.3, 8.4_

- [x] 13.1 Write unit tests for React setup
  - Test component rendering and basic functionality
  - _Requirements: 8.1, 8.3, 8.4_

- [x] 14. Team Dashboard Component
  - Create real-time bug count visualization with bar charts
  - Implement warning indicators for overloaded developers (>5 bugs)
  - Add live feed of recent triage decisions with confidence scores
  - Implement auto-refresh functionality every 30 seconds
  - Apply branding.json color scheme and typography
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 14.1 Write property test for overload warning threshold
  - **Property 25: Overload Warning Threshold**
  - **Validates: Requirements 8.2**

- [x] 14.2 Write unit tests for dashboard components
  - Test chart rendering, auto-refresh, and warning indicators
  - _Requirements: 8.1, 8.3, 8.4_

- [x] 15. Bus Factor Monitor Component
  - Implement git history analysis for single contributor detection
  - Create knowledge risk visualization with warning sections
  - Add ownership percentage calculations and display
  - Implement knowledge transfer suggestions for junior developers
  - Style with branding.json design system
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 15.1 Write property test for single contributor detection
  - **Property 26: Single Contributor Detection**
  - **Validates: Requirements 9.1**

- [x] 15.2 Write property test for ownership percentage calculation
  - **Property 28: Ownership Percentage Calculation**
  - **Validates: Requirements 9.3**

- [x] 16. Configuration Panel Component
  - Create user mapping management interface (searchable table)
  - Implement confidence threshold adjustment controls
  - Add Draft PR mode toggle functionality
  - Create duplicate detection window settings
  - Ensure immediate configuration application without restart
  - _Requirements: 4.1, 4.2, 11.1, 11.2, 11.3, 11.4_

- [x] 16.1 Write property test for immediate configuration application
  - **Property 34: Immediate Configuration Application**
  - **Validates: Requirements 11.4**

- [x] 16.2 Write unit tests for configuration panel
  - Test form validation, settings updates, and user management
  - _Requirements: 4.1, 4.2, 11.1, 11.2, 11.3_

- [x] 17. Error Handling and Graceful Degradation
  - Implement circuit breaker pattern for external API calls
  - Add graceful degradation for AI service failures
  - Create administrator notification system for API failures
  - Implement comprehensive logging for all triage decisions
  - Add health check endpoints and monitoring
  - _Requirements: 10.4, 10.5_

- [x] 17.1 Write property test for graceful API failure handling
  - **Property 33: Graceful API Failure Handling**
  - **Validates: Requirements 10.5**

- [x] 17.2 Write property test for decision logging completeness
  - **Property 32: Decision Logging Completeness**
  - **Validates: Requirements 10.4**

- [x] 18. Integration and System Testing
  - Create end-to-end test scenarios (webhook → assignment → notification)
  - Test high confidence bug → draft PR generation flow
  - Verify configuration changes apply immediately across system
  - Test API failure scenarios and graceful degradation
  - Validate real-time dashboard updates and auto-refresh
  - _Requirements: All integrated requirements_

- [x] 18.1 Write integration tests for complete triage pipeline
  - Test full workflow from GitHub webhook to Slack notification
  - _Requirements: 1.1, 1.2, 2.1, 3.1, 5.2_

- [x] 18.2 Write integration tests for draft PR generation
  - Test high confidence bug analysis → draft PR creation
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 19. Demo Preparation and Documentation
  - Create demo script with test scenarios
  - Set up demo GitHub repository with controlled history
  - Configure test Slack workspace for notifications
  - Create README with setup and deployment instructions
  - Prepare architecture diagrams and system overview
  - Test complete demo flow multiple times
  - _Requirements: System demonstration_

- [x] 20. Final Checkpoint - System Complete
  - Ensure all tests pass, ask the user if questions arise.
  - Verify demo readiness and system stability
  - Confirm all requirements are implemented and tested

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and user feedback
- Property tests validate universal correctness properties with 100+ iterations each
- Unit tests validate specific examples, edge cases, and UI functionality
- Integration tests ensure end-to-end system functionality
- The implementation prioritizes backend stability before frontend features
- Demo preparation ensures hackathon readiness with rehearsed scenarios
- All testing tasks are required to ensure comprehensive validation and system robustness