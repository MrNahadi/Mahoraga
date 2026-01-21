"""
Slack Notification Service for Mahoraga Triage System

Implements Slack SDK integration for DM notifications with retry logic,
content formatting, and escalation handling.
"""

import logging
import asyncio
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from sqlalchemy.orm import Session
from database import User, SystemConfig, SessionLocal
from assignment_engine import AssignmentResult
from config import get_settings
from error_handling import get_circuit_breaker, execute_with_circuit_breaker, register_fallback_strategy

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class NotificationContent:
    """Structured notification content"""
    assignee_email: str
    assignee_slack_id: str
    assignee_name: str
    issue_id: str
    issue_url: str
    file_path: str
    line_number: Optional[int]
    expertise_reason: str
    confidence: float
    draft_pr_url: Optional[str]
    estimated_effort: str
    priority: str


@dataclass
class NotificationResult:
    """Result of notification attempt"""
    success: bool
    message_ts: Optional[str]
    error: Optional[str]
    retry_count: int
    total_time_ms: int


class SlackNotificationService:
    """
    Slack Notification Service with retry logic and escalation
    
    Features:
    - Slack SDK integration for DM notifications
    - Notification content with file path, line number, expertise reason, confidence
    - Draft PR link inclusion when available
    - Low confidence escalation to on-call engineer
    - Retry logic with exponential backoff for failed deliveries
    """
    
    def __init__(self, slack_token: Optional[str] = None):
        """
        Initialize Slack Notification Service
        
        Args:
            slack_token: Slack bot token (optional, will use from settings if None)
        """
        self.slack_token = slack_token or settings.slack_bot_token
        self.client = AsyncWebClient(token=self.slack_token) if self.slack_token else None
        self.circuit_breaker = get_circuit_breaker("slack_api")
        self.max_retry_attempts = 5
        self.base_retry_delay = 1.0  # seconds
        self.max_retry_delay = 60.0  # seconds
        
        if not self.slack_token:
            logger.warning("Slack bot token not configured - notifications will be disabled")
        
        self._register_fallback_strategy()
    
    def _register_fallback_strategy(self):
        """Register fallback strategy for when Slack API is unavailable"""
        async def slack_fallback_strategy(*args, **kwargs) -> NotificationResult:
            """
            Fallback notification strategy using local logging when Slack is unavailable
            """
            logger.info("Using fallback notification strategy (Slack API unavailable)")
            
            try:
                # Extract notification details from arguments
                if len(args) >= 2:
                    slack_id = args[0]
                    message = args[1]
                    
                    # Log the notification locally
                    logger.critical(
                        f"NOTIFICATION FALLBACK: Would have sent to {slack_id}: {message}",
                        extra={
                            "notification_type": "fallback",
                            "slack_id": slack_id,
                            "message": message,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    # Store in database for later retry
                    await self._store_failed_notification(slack_id, message)
                    
                    return NotificationResult(
                        success=True,  # Consider fallback as success
                        message_ts=None,
                        error="Used fallback logging (Slack unavailable)",
                        retry_count=0,
                        total_time_ms=0
                    )
                else:
                    return NotificationResult(
                        success=False,
                        message_ts=None,
                        error="Invalid arguments for fallback strategy",
                        retry_count=0,
                        total_time_ms=0
                    )
                    
            except Exception as e:
                logger.error(f"Fallback notification strategy failed: {e}")
                return NotificationResult(
                    success=False,
                    message_ts=None,
                    error=f"Fallback strategy failed: {str(e)}",
                    retry_count=0,
                    total_time_ms=0
                )
        
        register_fallback_strategy("slack_api", slack_fallback_strategy)
    
    async def _store_failed_notification(self, slack_id: str, message: str):
        """Store failed notification for later retry"""
        try:
            with SessionLocal() as db:
                notification_data = {
                    "slack_id": slack_id,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    "type": "failed_notification"
                }
                
                config_key = f"failed_notification_{slack_id}_{int(time.time())}"
                config = SystemConfig(
                    key=config_key,
                    value=json.dumps(notification_data),
                    description=f"Failed notification for retry"
                )
                
                db.add(config)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store failed notification: {e}")
    
    def _get_on_call_engineer_slack_id(self) -> Optional[str]:
        """
        Get the Slack ID of the current on-call engineer
        
        Returns:
            Slack ID of on-call engineer or None if not configured
        """
        try:
            with SessionLocal() as db:
                config = db.query(SystemConfig).filter(
                    SystemConfig.key == "on_call_engineer_slack_id"
                ).first()
                
                if config and config.value:
                    return config.value
                else:
                    logger.warning("On-call engineer Slack ID not configured")
                    return None
                    
        except Exception as e:
            logger.error(f"Could not get on-call engineer Slack ID: {e}")
            return None
    
    def _get_user_slack_id(self, git_email: str) -> Optional[str]:
        """
        Get Slack ID for a git email address
        
        Args:
            git_email: Git email address
            
        Returns:
            Slack ID or None if not found
        """
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(
                    User.git_email == git_email,
                    User.is_active == True
                ).first()
                
                if user:
                    return user.slack_id
                else:
                    logger.warning(f"No active Slack mapping found for {git_email}")
                    return None
                    
        except Exception as e:
            logger.error(f"Could not get Slack ID for {git_email}: {e}")
            return None
    
    def _format_notification_message(self, content: NotificationContent) -> str:
        """
        Format notification message content
        
        Args:
            content: Notification content structure
            
        Returns:
            Formatted Slack message
        """
        # Build the main message
        message_parts = [
            f"🐛 *New Bug Assignment*",
            f"",
            f"*Issue:* <{content.issue_url}|{content.issue_id}>",
            f"*File:* `{content.file_path}`"
        ]
        
        # Add line number if available
        if content.line_number:
            message_parts.append(f"*Line:* {content.line_number}")
        
        # Add assignment details
        message_parts.extend([
            f"*Confidence:* {content.confidence:.1f}%",
            f"*Priority:* {content.priority.title()}",
            f"*Estimated Effort:* {content.estimated_effort}",
            f"",
            f"*Why you?* {content.expertise_reason}"
        ])
        
        # Add draft PR link if available
        if content.draft_pr_url:
            message_parts.extend([
                f"",
                f"🔧 *Draft Fix Available:* <{content.draft_pr_url}|View Proposed Solution>"
            ])
        
        # Add footer
        message_parts.extend([
            f"",
            f"_Assigned by Mahoraga at {datetime.now().strftime('%H:%M:%S')}_"
        ])
        
        return "\n".join(message_parts)
    
    def _format_escalation_message(self, 
                                 content: NotificationContent,
                                 original_assignee: str) -> str:
        """
        Format escalation message for on-call engineer
        
        Args:
            content: Notification content structure
            original_assignee: Email of original assignee candidate
            
        Returns:
            Formatted escalation message
        """
        message_parts = [
            f"⚠️ *Manual Triage Required*",
            f"",
            f"*Issue:* <{content.issue_url}|{content.issue_id}>",
            f"*File:* `{content.file_path}`"
        ]
        
        if content.line_number:
            message_parts.append(f"*Line:* {content.line_number}")
        
        message_parts.extend([
            f"*Confidence:* {content.confidence:.1f}% (below threshold)",
            f"*Suggested Assignee:* {original_assignee}",
            f"",
            f"*Reason for Escalation:* {content.expertise_reason}",
            f"",
            f"_Please review and assign manually_"
        ])
        
        return "\n".join(message_parts)
    
    async def _send_slack_message(self, 
                                slack_id: str, 
                                message: str,
                                retry_count: int = 0) -> NotificationResult:
        """
        Send a Slack DM with retry logic
        
        Args:
            slack_id: Slack user ID
            message: Message content
            retry_count: Current retry attempt
            
        Returns:
            NotificationResult with success status and details
        """
        if not self.client:
            return NotificationResult(
                success=False,
                message_ts=None,
                error="Slack client not initialized (missing token)",
                retry_count=retry_count,
                total_time_ms=0
            )
        
        start_time = time.time()
        
        try:
            # Send the message
            response = await self.client.chat_postMessage(
                channel=slack_id,
                text=message,
                unfurl_links=False,
                unfurl_media=False
            )
            
            end_time = time.time()
            total_time_ms = int((end_time - start_time) * 1000)
            
            if response["ok"]:
                logger.info(f"Successfully sent Slack message to {slack_id}")
                return NotificationResult(
                    success=True,
                    message_ts=response["ts"],
                    error=None,
                    retry_count=retry_count,
                    total_time_ms=total_time_ms
                )
            else:
                error_msg = response.get("error", "Unknown Slack API error")
                logger.error(f"Slack API error: {error_msg}")
                return NotificationResult(
                    success=False,
                    message_ts=None,
                    error=error_msg,
                    retry_count=retry_count,
                    total_time_ms=total_time_ms
                )
                
        except SlackApiError as e:
            end_time = time.time()
            total_time_ms = int((end_time - start_time) * 1000)
            
            error_msg = f"Slack API error: {e.response['error']}"
            logger.error(f"Failed to send Slack message: {error_msg}")
            
            return NotificationResult(
                success=False,
                message_ts=None,
                error=error_msg,
                retry_count=retry_count,
                total_time_ms=total_time_ms
            )
            
        except Exception as e:
            end_time = time.time()
            total_time_ms = int((end_time - start_time) * 1000)
            
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to send Slack message: {error_msg}")
            
            return NotificationResult(
                success=False,
                message_ts=None,
                error=error_msg,
                retry_count=retry_count,
                total_time_ms=total_time_ms
            )
    
    async def _send_with_retry(self, 
                             slack_id: str, 
                             message: str) -> NotificationResult:
        """
        Send Slack message with circuit breaker and exponential backoff retry logic
        
        Args:
            slack_id: Slack user ID
            message: Message content
            
        Returns:
            Final NotificationResult after all retry attempts
        """
        try:
            return await execute_with_circuit_breaker(
                "slack_api",
                self._send_slack_message_with_retry,
                slack_id,
                message
            )
        except Exception as e:
            logger.error(f"Slack notification failed with circuit breaker: {e}")
            return NotificationResult(
                success=False,
                message_ts=None,
                error=f"Circuit breaker execution failed: {str(e)}",
                retry_count=0,
                total_time_ms=0
            )
    
    async def _send_slack_message_with_retry(self, 
                                           slack_id: str, 
                                           message: str) -> NotificationResult:
        """
        Internal method to send Slack message with retry logic (called by circuit breaker)
        
        Args:
            slack_id: Slack user ID
            message: Message content
            
        Returns:
            Final NotificationResult after all retry attempts
        """
        last_result = None
        
        for attempt in range(self.max_retry_attempts):
            result = await self._send_slack_message(slack_id, message, attempt)
            
            if result.success:
                return result
            
            last_result = result
            
            # Don't retry on certain errors
            if result.error and any(err in result.error.lower() for err in [
                "invalid_auth", "account_inactive", "user_not_found", "channel_not_found"
            ]):
                logger.warning(f"Non-retryable Slack error: {result.error}")
                break
            
            # Calculate delay for next attempt
            if attempt < self.max_retry_attempts - 1:
                delay = min(
                    self.base_retry_delay * (2 ** attempt),
                    self.max_retry_delay
                )
                logger.info(f"Retrying Slack message in {delay:.1f}s (attempt {attempt + 1}/{self.max_retry_attempts})")
                await asyncio.sleep(delay)
        
        return last_result or NotificationResult(
            success=False,
            message_ts=None,
            error="All retry attempts failed",
            retry_count=self.max_retry_attempts,
            total_time_ms=0
        )
    
    async def send_assignment_notification(self, 
                                         assignment_result: AssignmentResult,
                                         issue_id: str,
                                         issue_url: str,
                                         file_path: str,
                                         line_number: Optional[int] = None,
                                         draft_pr_url: Optional[str] = None) -> NotificationResult:
        """
        Send assignment notification to developer
        
        Args:
            assignment_result: Assignment calculation result
            issue_id: GitHub issue ID
            issue_url: GitHub issue URL
            file_path: Primary affected file path
            line_number: Line number if available
            draft_pr_url: Draft PR URL if available
            
        Returns:
            NotificationResult with delivery status
        """
        if assignment_result.should_route_to_human:
            logger.info(f"Assignment routed to human triage, not sending developer notification")
            return NotificationResult(
                success=True,
                message_ts=None,
                error="Routed to human triage",
                retry_count=0,
                total_time_ms=0
            )
        
        if not assignment_result.assignee_email:
            logger.error("No assignee email provided for notification")
            return NotificationResult(
                success=False,
                message_ts=None,
                error="No assignee email provided",
                retry_count=0,
                total_time_ms=0
            )
        
        # Get Slack ID for assignee
        slack_id = self._get_user_slack_id(assignment_result.assignee_email)
        if not slack_id:
            logger.error(f"No Slack ID found for {assignment_result.assignee_email}")
            return NotificationResult(
                success=False,
                message_ts=None,
                error=f"No Slack mapping for {assignment_result.assignee_email}",
                retry_count=0,
                total_time_ms=0
            )
        
        # Create notification content
        content = NotificationContent(
            assignee_email=assignment_result.assignee_email,
            assignee_slack_id=slack_id,
            assignee_name=assignment_result.assignee_name or assignment_result.assignee_email,
            issue_id=issue_id,
            issue_url=issue_url,
            file_path=file_path,
            line_number=line_number,
            expertise_reason=assignment_result.reasoning,
            confidence=assignment_result.confidence,
            draft_pr_url=draft_pr_url,
            estimated_effort=assignment_result.estimated_effort,
            priority=assignment_result.priority
        )
        
        # Format and send message
        message = self._format_notification_message(content)
        result = await self._send_with_retry(slack_id, message)
        
        if result.success:
            logger.info(f"Successfully notified {assignment_result.assignee_email} about {issue_id}")
        else:
            logger.error(f"Failed to notify {assignment_result.assignee_email}: {result.error}")
        
        return result
    
    async def send_escalation_notification(self,
                                         assignment_result: AssignmentResult,
                                         issue_id: str,
                                         issue_url: str,
                                         file_path: str,
                                         line_number: Optional[int] = None) -> NotificationResult:
        """
        Send escalation notification to on-call engineer for low confidence assignments
        
        Args:
            assignment_result: Assignment calculation result
            issue_id: GitHub issue ID
            issue_url: GitHub issue URL
            file_path: Primary affected file path
            line_number: Line number if available
            
        Returns:
            NotificationResult with delivery status
        """
        if not assignment_result.should_route_to_human:
            logger.info(f"Assignment has sufficient confidence, not escalating")
            return NotificationResult(
                success=True,
                message_ts=None,
                error="No escalation needed",
                retry_count=0,
                total_time_ms=0
            )
        
        # Get on-call engineer Slack ID
        on_call_slack_id = self._get_on_call_engineer_slack_id()
        if not on_call_slack_id:
            logger.error("No on-call engineer configured for escalation")
            return NotificationResult(
                success=False,
                message_ts=None,
                error="No on-call engineer configured",
                retry_count=0,
                total_time_ms=0
            )
        
        # Create escalation content
        original_assignee = (
            assignment_result.fallback_candidates[0].developer_email 
            if assignment_result.fallback_candidates 
            else "Unknown"
        )
        
        content = NotificationContent(
            assignee_email=original_assignee,
            assignee_slack_id=on_call_slack_id,
            assignee_name="On-Call Engineer",
            issue_id=issue_id,
            issue_url=issue_url,
            file_path=file_path,
            line_number=line_number,
            expertise_reason=assignment_result.reasoning,
            confidence=assignment_result.confidence,
            draft_pr_url=None,  # No draft PR for low confidence
            estimated_effort=assignment_result.estimated_effort,
            priority=assignment_result.priority
        )
        
        # Format and send escalation message
        message = self._format_escalation_message(content, original_assignee)
        result = await self._send_with_retry(on_call_slack_id, message)
        
        if result.success:
            logger.info(f"Successfully escalated {issue_id} to on-call engineer")
        else:
            logger.error(f"Failed to escalate {issue_id}: {result.error}")
        
        return result
    
    async def send_notification(self,
                              assignment_result: AssignmentResult,
                              issue_id: str,
                              issue_url: str,
                              file_path: str,
                              line_number: Optional[int] = None,
                              draft_pr_url: Optional[str] = None) -> NotificationResult:
        """
        Send appropriate notification based on assignment result
        
        Args:
            assignment_result: Assignment calculation result
            issue_id: GitHub issue ID
            issue_url: GitHub issue URL
            file_path: Primary affected file path
            line_number: Line number if available
            draft_pr_url: Draft PR URL if available
            
        Returns:
            NotificationResult with delivery status
        """
        if assignment_result.should_route_to_human:
            # Send escalation notification
            return await self.send_escalation_notification(
                assignment_result, issue_id, issue_url, file_path, line_number
            )
        else:
            # Send regular assignment notification
            return await self.send_assignment_notification(
                assignment_result, issue_id, issue_url, file_path, line_number, draft_pr_url
            )


# Global notification service instance
notification_service = SlackNotificationService()


async def send_bug_assignment_notification(assignment_result: AssignmentResult,
                                         issue_id: str,
                                         issue_url: str,
                                         file_path: str,
                                         line_number: Optional[int] = None,
                                         draft_pr_url: Optional[str] = None) -> NotificationResult:
    """
    Convenience function for sending bug assignment notifications
    
    Args:
        assignment_result: Assignment calculation result
        issue_id: GitHub issue ID
        issue_url: GitHub issue URL
        file_path: Primary affected file path
        line_number: Line number if available
        draft_pr_url: Draft PR URL if available
        
    Returns:
        NotificationResult with delivery status
    """
    return await notification_service.send_notification(
        assignment_result, issue_id, issue_url, file_path, line_number, draft_pr_url
    )