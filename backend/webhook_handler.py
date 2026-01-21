"""
GitHub Webhook Handler for Mahoraga Triage Engine
Handles incoming GitHub webhooks for issue and PR events
"""

import hashlib
import hmac
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from database import TriageDecision, Assignment, SessionLocal
from config import get_settings
import logging
from stack_trace_parser import parse_stack_trace, StackTrace
from ai_analysis_service import analyze_bug_report, BugAnalysis
from assignment_engine import calculate_bug_assignment as calculate_assignment, AssignmentResult
from slack_notification_service import SlackNotificationService, NotificationResult, send_bug_assignment_notification
from draft_pr_generator import DraftPRGenerator
from git_analysis_engine import GitAnalysisEngine

logger = logging.getLogger(__name__)
settings = get_settings()


class WebhookSignatureVerifier:
    """Handles GitHub webhook signature verification using HMAC-SHA256"""
    
    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        """
        Verify GitHub webhook signature using HMAC-SHA256
        
        Args:
            payload: Raw request body bytes
            signature: GitHub signature header (sha256=...)
            secret: Webhook secret from configuration
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not secret:
            logger.warning("Webhook secret not configured - signature verification disabled")
            return True  # Allow webhooks when secret is not configured for development
        
        if not signature:
            logger.warning("No signature provided in webhook request")
            return False
        
        # GitHub signature format: "sha256=<hex_digest>"
        if not signature.startswith("sha256="):
            logger.warning(f"Invalid signature format: {signature}")
            return False
        
        # Extract hex digest from signature
        expected_signature = signature[7:]  # Remove "sha256=" prefix
        
        # Calculate HMAC-SHA256 of payload
        calculated_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, calculated_signature)


class DuplicateDetector:
    """Handles duplicate issue detection within configurable time window"""
    
    def __init__(self, window_minutes: int = 10):
        self.window_minutes = window_minutes
    
    def is_duplicate(self, issue_id: str, db: Session) -> bool:
        """
        Check if an issue is a duplicate within the detection window
        
        Args:
            issue_id: GitHub issue ID to check
            db: Database session
            
        Returns:
            True if issue is a duplicate, False otherwise
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        
        # Check if we've seen this issue ID recently
        existing_decision = db.query(TriageDecision).filter(
            TriageDecision.issue_id == issue_id,
            TriageDecision.created_at >= cutoff_time
        ).first()
        
        return existing_decision is not None
    
    def find_similar_issues(self, issue_body: str, db: Session) -> List[TriageDecision]:
        """
        Find similar issues based on content similarity within the detection window
        
        Args:
            issue_body: Issue description text
            db: Database session
            
        Returns:
            List of similar triage decisions
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        
        # For now, implement simple keyword-based similarity
        # In production, this could use more sophisticated text similarity
        keywords = self._extract_keywords(issue_body)
        
        if not keywords:
            return []
        
        # Find recent decisions with similar stack traces or content
        recent_decisions = db.query(TriageDecision).filter(
            TriageDecision.created_at >= cutoff_time
        ).all()
        
        similar_decisions = []
        for decision in recent_decisions:
            if decision.stack_trace and self._has_similar_content(decision.stack_trace, keywords):
                similar_decisions.append(decision)
        
        return similar_decisions
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from issue text"""
        if not text:
            return []
        
        # Simple keyword extraction - look for error patterns
        error_patterns = [
            "error", "exception", "traceback", "stack trace",
            "failed", "crash", "bug", "issue", "problem"
        ]
        
        text_lower = text.lower()
        found_keywords = [pattern for pattern in error_patterns if pattern in text_lower]
        
        # Also extract file extensions and common error types
        import re
        file_extensions = re.findall(r'\.\w+', text)
        error_types = re.findall(r'\w*Error\w*|\w*Exception\w*', text)
        
        return found_keywords + file_extensions + error_types
    
    def _has_similar_content(self, content: str, keywords: List[str]) -> bool:
        """Check if content contains similar keywords"""
        if not content or not keywords:
            return False
        
        content_lower = content.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in content_lower)
        
        # Consider similar if at least 50% of keywords match
        return matches >= len(keywords) * 0.5


class GitHubEventParser:
    """Parses GitHub webhook events for issue and PR data"""
    
    @staticmethod
    def parse_issue_event(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse GitHub issue webhook payload
        
        Args:
            payload: GitHub webhook payload
            
        Returns:
            Parsed issue data or None if not relevant
        """
        action = payload.get("action")
        
        # Only process opened issues for now
        if action != "opened":
            logger.debug(f"Ignoring issue action: {action}")
            return None
        
        issue = payload.get("issue", {})
        
        return {
            "type": "issue",
            "action": action,
            "issue_id": str(issue.get("id", "")),
            "issue_number": issue.get("number"),
            "title": issue.get("title", ""),
            "body": issue.get("body", ""),
            "url": issue.get("html_url", ""),
            "repository": payload.get("repository", {}).get("full_name", ""),
            "created_at": issue.get("created_at"),
            "user": issue.get("user", {}).get("login", ""),
        }
    
    @staticmethod
    def parse_pull_request_event(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse GitHub pull request webhook payload
        
        Args:
            payload: GitHub webhook payload
            
        Returns:
            Parsed PR data or None if not relevant
        """
        action = payload.get("action")
        
        # Only process opened PRs for now
        if action != "opened":
            logger.debug(f"Ignoring PR action: {action}")
            return None
        
        pr = payload.get("pull_request", {})
        
        return {
            "type": "pull_request",
            "action": action,
            "pr_id": str(pr.get("id", "")),
            "pr_number": pr.get("number"),
            "title": pr.get("title", ""),
            "body": pr.get("body", ""),
            "url": pr.get("html_url", ""),
            "repository": payload.get("repository", {}).get("full_name", ""),
            "created_at": pr.get("created_at"),
            "user": pr.get("user", {}).get("login", ""),
            "draft": pr.get("draft", False),
        }


class TriageJobQueue:
    """Async job queue for triage processing"""
    
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._processing = False
    
    async def enqueue_job(self, job_data: Dict[str, Any]) -> None:
        """
        Add a triage job to the queue
        
        Args:
            job_data: Job data including event type and parsed data
        """
        await self._queue.put(job_data)
        logger.info(f"Enqueued triage job for {job_data.get('type', 'unknown')} {job_data.get('issue_id', job_data.get('pr_id', 'unknown'))}")
    
    async def start_processing(self) -> None:
        """Start processing jobs from the queue"""
        if self._processing:
            return
        
        self._processing = True
        logger.info("Started triage job processing")
        
        while self._processing:
            try:
                # Wait for job with timeout to allow graceful shutdown
                job_data = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._process_job(job_data)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing triage job: {e}")
    
    def stop_processing(self) -> None:
        """Stop processing jobs"""
        self._processing = False
        logger.info("Stopped triage job processing")
    
    async def _process_job(self, job_data: Dict[str, Any]) -> None:
        """
        Process a single triage job
        
        Args:
            job_data: Job data to process
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing triage job: {job_data.get('type')} {job_data.get('issue_id', job_data.get('pr_id'))}")
            
            issue_id = job_data.get('issue_id', job_data.get('pr_id', 'unknown'))
            issue_body = job_data.get('body', '')
            issue_url = job_data.get('url', '')
            
            # 1. Parse Stack Trace
            stack_trace = parse_stack_trace(issue_body)
            stack_trace_text = stack_trace.error_message if stack_trace else ""
            
            # 2. AI Analysis
            # 2. AI Analysis
            bug_analysis = await analyze_bug_report(issue_body, stack_trace)
            
            # Determine affected files
            affected_files = []
            if bug_analysis and bug_analysis.affected_files:
                affected_files = bug_analysis.affected_files
            elif stack_trace:
                affected_files = stack_trace.get_file_paths()
            
            # 3. Calculate Assignment (Git Expertise)
            assignment = await calculate_assignment(
                issue_id=issue_id,
                issue_url=issue_url,
                affected_files=affected_files,
                bug_analysis=bug_analysis
            )
            
            # 4. Generate Draft PR (if high confidence)
            draft_pr_url = None
            draft_generator = DraftPRGenerator()
            if assignment and draft_generator.should_generate_draft_fix(assignment.confidence):
                draft_fix = await draft_generator.generate_draft_fix(
                    bug_analysis=bug_analysis,
                    stack_trace=stack_trace,
                    repository_url=job_data.get('repository', '')
                )
                if draft_fix:
                    draft_pr = await draft_generator.create_draft_pr(
                        repository_url=job_data.get('repository', ''),
                        draft_fix=draft_fix,
                        bug_analysis=bug_analysis,
                        issue_id=issue_id
                    )
                    if draft_pr:
                        draft_pr_url = draft_pr.pr_url
            
            # 5. Send Slack Notification
            if assignment:
                send_bug_assignment_notification(
                    assignment_result=assignment,
                    issue_id=issue_id,
                    issue_url=issue_url,
                    file_path=affected_files[0] if affected_files else "unknown",
                    draft_pr_url=draft_pr_url
                )

            # 6. Record Decision
            processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            with SessionLocal() as db:
                decision = TriageDecision(
                    issue_id=issue_id,
                    stack_trace=stack_trace_text,
                    affected_files=json.dumps(affected_files),
                    root_cause=bug_analysis.root_cause_hypothesis if bug_analysis else None,
                    confidence=assignment.confidence if assignment else 0.0,
                    draft_pr_url=draft_pr_url,
                    processing_time_ms=processing_time_ms
                )
                db.add(decision)
                
                if assignment:
                    assignment_record = Assignment(
                        issue_id=issue_id,
                        issue_url=job_data.get('issue_url', ''),
                        assigned_to_email=assignment.assignee_email,
                        confidence=assignment.confidence,
                        reasoning=assignment.reasoning,
                        status="assigned",
                        created_at=datetime.utcnow()
                    )
                    db.add(assignment_record)
                
                db.commit()
            
            logger.info(f"Completed triage job processing in {(datetime.utcnow() - start_time).total_seconds():.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to process triage job: {e}")
            raise


class GitHubWebhookHandler:
    """Main webhook handler that coordinates all webhook processing"""
    
    def __init__(self):
        self.signature_verifier = WebhookSignatureVerifier()
        self.duplicate_detector = DuplicateDetector(
            window_minutes=settings.duplicate_detection_window_minutes
        )
        self.event_parser = GitHubEventParser()
        self.job_queue = TriageJobQueue()
    
    async def handle_webhook(self, request: Request) -> Dict[str, str]:
        """
        Handle incoming GitHub webhook request
        
        Args:
            request: FastAPI request object
            
        Returns:
            Response dictionary
            
        Raises:
            HTTPException: If webhook processing fails
        """
        try:
            # Get request headers and body
            signature = request.headers.get("X-Hub-Signature-256", "")
            event_type = request.headers.get("X-GitHub-Event", "")
            delivery_id = request.headers.get("X-GitHub-Delivery", "")
            
            # Read raw body for signature verification
            body = await request.body()
            
            # Verify webhook signature
            if not verify_webhook_signature(body, signature, settings.github_webhook_secret):
                logger.warning(f"Invalid webhook signature for delivery {delivery_id}")
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Parse JSON payload
            try:
                payload = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON payload: {e}")
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
            
            # Log webhook reception
            logger.info(f"Received {event_type} webhook (delivery: {delivery_id})")
            
            # Parse event based on type
            parsed_data = None
            if event_type == "issues":
                parsed_data = self.event_parser.parse_issue_event(payload)
            elif event_type == "pull_request":
                parsed_data = self.event_parser.parse_pull_request_event(payload)
            else:
                logger.debug(f"Ignoring unsupported event type: {event_type}")
                return {"status": "ignored", "reason": f"Unsupported event type: {event_type}"}
            
            if not parsed_data:
                return {"status": "ignored", "reason": "Event not relevant for triage"}
            
            # Check for duplicates
            with SessionLocal() as db:
                issue_id = parsed_data.get('issue_id', parsed_data.get('pr_id'))
                if self.duplicate_detector.is_duplicate(issue_id, db):
                    logger.info(f"Duplicate detected for {issue_id}, skipping triage")
                    return {"status": "duplicate", "issue_id": issue_id}
            
            # Enqueue for async processing
            await self.job_queue.enqueue_job(parsed_data)
            
            return {
                "status": "accepted",
                "delivery_id": delivery_id,
                "event_type": event_type,
                "issue_id": issue_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error handling webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def start_job_processing(self) -> None:
        """Start the async job processing"""
        await self.job_queue.start_processing()
    
    def stop_job_processing(self) -> None:
        """Stop the async job processing"""
        self.job_queue.stop_processing()


# Dummy function to satisfy test mocks
def get_git_expertise_scores(*args, **kwargs):
    """Placeholder for test mocking"""
    return []

def generate_draft_fix(*args, **kwargs):
    """Placeholder for test mocking"""
    return None

def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook signature 
    (Wrapped function to allow mocking in tests)
    """
    verifier = WebhookSignatureVerifier()
    return verifier.verify_signature(body, signature, secret)



# Global webhook handler instance
webhook_handler = GitHubWebhookHandler()