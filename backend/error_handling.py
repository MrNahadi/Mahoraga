"""
Error Handling and Graceful Degradation for Mahoraga Triage Engine

Implements circuit breaker pattern, graceful degradation strategies,
administrator notifications, and comprehensive logging.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from database import SystemConfig, TriageDecision, SessionLocal
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar('T')


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    timeout_seconds: int = 60
    success_threshold: int = 3  # Successes needed to close from half-open
    max_requests_half_open: int = 5  # Max requests allowed in half-open state


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: List[Dict[str, Any]] = field(default_factory=list)


class CircuitBreaker(Generic[T]):
    """
    Circuit breaker pattern implementation for external API calls
    
    Provides automatic failure detection, timeout handling, and recovery testing
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        """
        Initialize circuit breaker
        
        Args:
            name: Unique name for this circuit breaker
            config: Configuration parameters
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.metrics = CircuitBreakerMetrics()
        self.half_open_requests = 0
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")
    
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution"""
        now = datetime.utcnow()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if (self.last_failure_time and 
                (now - self.last_failure_time).total_seconds() > self.config.timeout_seconds):
                self._transition_to_half_open()
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_requests < self.config.max_requests_half_open
        
        return False
    
    def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN state"""
        old_state = self.state
        self.state = CircuitBreakerState.HALF_OPEN
        self.half_open_requests = 0
        self.success_count = 0
        
        self._record_state_change(old_state, self.state, "Timeout expired, testing recovery")
        logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state (normal operation)"""
        old_state = self.state
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.half_open_requests = 0
        
        self._record_state_change(old_state, self.state, "Service recovered")
        logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED (recovered)")
    
    def _transition_to_open(self):
        """Transition to OPEN state (failing)"""
        old_state = self.state
        self.state = CircuitBreakerState.OPEN
        self.last_failure_time = datetime.utcnow()
        self.half_open_requests = 0
        
        self._record_state_change(old_state, self.state, f"Failure threshold exceeded ({self.failure_count})")
        logger.warning(f"Circuit breaker '{self.name}' OPENED after {self.failure_count} failures")
    
    def _record_state_change(self, old_state: CircuitBreakerState, new_state: CircuitBreakerState, reason: str):
        """Record state change for monitoring"""
        change_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "old_state": old_state.value,
            "new_state": new_state.value,
            "reason": reason,
            "failure_count": self.failure_count,
            "success_count": self.success_count
        }
        
        self.metrics.state_changes.append(change_record)
        
        # Keep only last 50 state changes to prevent memory bloat
        if len(self.metrics.state_changes) > 50:
            self.metrics.state_changes = self.metrics.state_changes[-50:]
    
    def record_success(self):
        """Record a successful operation"""
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.last_success_time = datetime.utcnow()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed operation"""
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            # Immediately go back to OPEN on failure in half-open
            self._transition_to_open()
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
    
    @asynccontextmanager
    async def execute(self):
        """
        Context manager for executing operations with circuit breaker protection
        
        Usage:
            async with circuit_breaker.execute() as cb:
                if cb.can_proceed:
                    result = await some_operation()
                    cb.record_success()
                else:
                    # Handle circuit breaker open
                    pass
        """
        class ExecutionContext:
            def __init__(self, breaker: 'CircuitBreaker'):
                self.breaker = breaker
                self.can_proceed = breaker.can_execute()
                self.executed = False
            
            def record_success(self):
                if self.can_proceed and not self.executed:
                    self.breaker.record_success()
                    self.executed = True
            
            def record_failure(self):
                if self.can_proceed and not self.executed:
                    self.breaker.record_failure()
                    self.executed = True
        
        context = ExecutionContext(self)
        
        if context.can_proceed and self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_requests += 1
        
        try:
            yield context
        except Exception as e:
            if context.can_proceed and not context.executed:
                context.record_failure()
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status for monitoring"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "success_threshold": self.config.success_threshold,
            },
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": (
                    self.metrics.successful_requests / self.metrics.total_requests 
                    if self.metrics.total_requests > 0 else 0.0
                ),
                "last_failure_time": (
                    self.metrics.last_failure_time.isoformat() 
                    if self.metrics.last_failure_time else None
                ),
                "last_success_time": (
                    self.metrics.last_success_time.isoformat() 
                    if self.metrics.last_success_time else None
                ),
            },
            "can_execute": self.can_execute(),
        }


class ServiceDegradationLevel(Enum):
    """Levels of service degradation"""
    NORMAL = "normal"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class ServiceStatus:
    """Status of an external service"""
    name: str
    level: ServiceDegradationLevel
    last_check: datetime
    error_message: Optional[str] = None
    fallback_active: bool = False
    circuit_breaker_status: Optional[Dict[str, Any]] = None


class GracefulDegradationManager:
    """
    Manages graceful degradation strategies for external service failures
    
    Provides fallback mechanisms and service health monitoring
    """
    
    def __init__(self):
        """Initialize degradation manager"""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.service_statuses: Dict[str, ServiceStatus] = {}
        self.fallback_strategies: Dict[str, Callable] = {}
        self.administrator_notifications_sent: Dict[str, datetime] = {}
        
        # Initialize circuit breakers for external services
        self._initialize_circuit_breakers()
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for all external services"""
        services = {
            "gemini_api": CircuitBreakerConfig(failure_threshold=5, timeout_seconds=60),
            "github_api": CircuitBreakerConfig(failure_threshold=3, timeout_seconds=30),
            "slack_api": CircuitBreakerConfig(failure_threshold=5, timeout_seconds=60),
            "git_operations": CircuitBreakerConfig(failure_threshold=3, timeout_seconds=30),
        }
        
        for service_name, config in services.items():
            self.circuit_breakers[service_name] = CircuitBreaker(service_name, config)
            self.service_statuses[service_name] = ServiceStatus(
                name=service_name,
                level=ServiceDegradationLevel.NORMAL,
                last_check=datetime.utcnow()
            )
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get circuit breaker for a service"""
        if service_name not in self.circuit_breakers:
            logger.warning(f"Circuit breaker for '{service_name}' not found, creating default")
            self.circuit_breakers[service_name] = CircuitBreaker(service_name)
        
        return self.circuit_breakers[service_name]
    
    def register_fallback_strategy(self, service_name: str, fallback_func: Callable):
        """Register a fallback strategy for a service"""
        self.fallback_strategies[service_name] = fallback_func
        logger.info(f"Registered fallback strategy for '{service_name}'")
    
    async def execute_with_fallback(self, 
                                  service_name: str, 
                                  primary_func: Callable,
                                  *args, **kwargs) -> Any:
        """
        Execute operation with circuit breaker and fallback
        
        Args:
            service_name: Name of the service
            primary_func: Primary function to execute
            *args, **kwargs: Arguments for the function
            
        Returns:
            Result from primary function or fallback
        """
        circuit_breaker = self.get_circuit_breaker(service_name)
        
        async with circuit_breaker.execute() as cb:
            if cb.can_proceed:
                try:
                    result = await primary_func(*args, **kwargs)
                    cb.record_success()
                    self._update_service_status(service_name, ServiceDegradationLevel.NORMAL)
                    return result
                except Exception as e:
                    cb.record_failure()
                    logger.error(f"Primary function failed for {service_name}: {e}")
                    self._update_service_status(
                        service_name, 
                        ServiceDegradationLevel.DEGRADED, 
                        str(e)
                    )
                    
                    # Try fallback if available
                    if service_name in self.fallback_strategies:
                        try:
                            logger.info(f"Executing fallback strategy for {service_name}")
                            result = await self.fallback_strategies[service_name](*args, **kwargs)
                            self.service_statuses[service_name].fallback_active = True
                            return result
                        except Exception as fallback_error:
                            logger.error(f"Fallback strategy failed for {service_name}: {fallback_error}")
                    
                    # Send administrator notification
                    await self._notify_administrators(service_name, str(e))
                    raise
            else:
                # Circuit breaker is open
                self._update_service_status(
                    service_name, 
                    ServiceDegradationLevel.CRITICAL,
                    "Circuit breaker is open"
                )
                
                # Try fallback if available
                if service_name in self.fallback_strategies:
                    try:
                        logger.info(f"Circuit breaker open, using fallback for {service_name}")
                        result = await self.fallback_strategies[service_name](*args, **kwargs)
                        self.service_statuses[service_name].fallback_active = True
                        return result
                    except Exception as fallback_error:
                        logger.error(f"Fallback strategy failed for {service_name}: {fallback_error}")
                
                # No fallback available or fallback failed
                await self._notify_administrators(service_name, "Circuit breaker is open")
                raise Exception(f"Service {service_name} is unavailable (circuit breaker open)")
    
    def _update_service_status(self, 
                             service_name: str, 
                             level: ServiceDegradationLevel,
                             error_message: Optional[str] = None):
        """Update service status"""
        """Update service status"""
        if service_name not in self.service_statuses:
            self.service_statuses[service_name] = ServiceStatus(
                name=service_name,
                level=level,
                last_check=datetime.utcnow()
            )
            
        if service_name in self.service_statuses:
            status = self.service_statuses[service_name]
            status.level = level
            status.last_check = datetime.utcnow()
            status.error_message = error_message
            status.circuit_breaker_status = self.circuit_breakers[service_name].get_status()
            
            if level == ServiceDegradationLevel.NORMAL:
                status.fallback_active = False
    
    async def _notify_administrators(self, service_name: str, error_message: str):
        """Send notification to administrators about service failures"""
        # Throttle notifications - don't spam administrators
        notification_key = f"{service_name}:{error_message}"
        now = datetime.utcnow()
        
        if (notification_key in self.administrator_notifications_sent and
            (now - self.administrator_notifications_sent[notification_key]).total_seconds() < 3600):
            return  # Don't send duplicate notifications within 1 hour
        
        self.administrator_notifications_sent[notification_key] = now
        
        try:
            # Log the error for administrator attention
            logger.critical(
                f"ADMINISTRATOR ALERT: Service '{service_name}' failure - {error_message}",
                extra={
                    "service": service_name,
                    "error": error_message,
                    "timestamp": now.isoformat(),
                    "alert_type": "service_failure"
                }
            )
            
            # Store notification in database for dashboard display
            await self._store_admin_notification(service_name, error_message)
            
            # TODO: Implement additional notification channels (email, Slack admin channel, etc.)
            
        except Exception as e:
            logger.error(f"Failed to send administrator notification: {e}")
    
    async def _store_admin_notification(self, service_name: str, error_message: str):
        """Store administrator notification in database"""
        try:
            with SessionLocal() as db:
                # Store as system config for dashboard retrieval
                notification_data = {
                    "service": service_name,
                    "error": error_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "service_failure"
                }
                
                config_key = f"admin_alert_{service_name}_{int(time.time())}"
                config = SystemConfig(
                    key=config_key,
                    value=json.dumps(notification_data),
                    description=f"Administrator alert for {service_name} failure"
                )
                
                db.add(config)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store administrator notification: {e}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        overall_level = ServiceDegradationLevel.NORMAL
        degraded_services = []
        
        for service_name, status in self.service_statuses.items():
            if status.level in [ServiceDegradationLevel.CRITICAL, ServiceDegradationLevel.OFFLINE]:
                overall_level = ServiceDegradationLevel.CRITICAL
                degraded_services.append(service_name)
            elif status.level == ServiceDegradationLevel.DEGRADED and overall_level == ServiceDegradationLevel.NORMAL:
                overall_level = ServiceDegradationLevel.DEGRADED
                degraded_services.append(service_name)
        
        return {
            "overall_status": overall_level.value,
            "degraded_services": degraded_services,
            "services": {
                name: {
                    "status": status.level.value,
                    "last_check": status.last_check.isoformat(),
                    "error_message": status.error_message,
                    "fallback_active": status.fallback_active,
                    "circuit_breaker": status.circuit_breaker_status or {
                        "name": name,
                        "state": "closed",
                        "can_execute": True,
                        "metrics": {}
                    },
                }
                for name, status in self.service_statuses.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }


class ComprehensiveLogger:
    """
    Comprehensive logging system for triage decisions and system events
    
    Provides structured logging with correlation IDs and audit trails
    """
    
    def __init__(self):
        """Initialize comprehensive logger"""
        self.logger = logging.getLogger("mahoraga.audit")
        
        # Configure structured logging format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(extra_data)s',
            defaults={'extra_data': '{}'}
        )
        
        # Add file handler for audit logs
        try:
            file_handler = logging.FileHandler('mahoraga_audit.log')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)
        except Exception as e:
            logger.warning(f"Could not set up audit log file: {e}")
    
    async def log_triage_decision(self,
                                issue_id: str,
                                decision_data: Dict[str, Any],
                                processing_time_ms: int,
                                correlation_id: Optional[str] = None):
        """
        Log a complete triage decision with all reasoning
        
        Args:
            issue_id: GitHub issue ID
            decision_data: Complete decision information
            processing_time_ms: Time taken to process
            correlation_id: Optional correlation ID for tracking
        """
        try:
            log_entry = {
                "event_type": "triage_decision",
                "issue_id": issue_id,
                "correlation_id": correlation_id or f"triage_{issue_id}_{int(time.time())}",
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.utcnow().isoformat(),
                "decision_data": decision_data
            }
            
            # Log to structured logger
            self.logger.info(
                f"Triage decision completed for {issue_id}",
                extra={"extra_data": json.dumps(log_entry)}
            )
            
            # Store in database for persistence
            await self._store_triage_decision(issue_id, decision_data, processing_time_ms)
            
        except Exception as e:
            logger.error(f"Failed to log triage decision: {e}")
    
    async def _store_triage_decision(self,
                                   issue_id: str,
                                   decision_data: Dict[str, Any],
                                   processing_time_ms: int):
        """Store triage decision in database"""
        try:
            with SessionLocal() as db:
                decision = TriageDecision(
                    issue_id=issue_id,
                    stack_trace=decision_data.get("stack_trace"),
                    affected_files=json.dumps(decision_data.get("affected_files", [])),
                    root_cause=decision_data.get("root_cause"),
                    confidence=decision_data.get("confidence", 0.0),
                    draft_pr_url=decision_data.get("draft_pr_url"),
                    processing_time_ms=processing_time_ms
                )
                
                db.add(decision)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store triage decision in database: {e}")
    
    def log_system_event(self,
                        event_type: str,
                        event_data: Dict[str, Any],
                        level: str = "INFO"):
        """
        Log system events for monitoring and debugging
        
        Args:
            event_type: Type of event (e.g., "service_failure", "config_change")
            event_data: Event-specific data
            level: Log level (INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            log_entry = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "event_data": event_data
            }
            
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(
                f"System event: {event_type}",
                extra={"extra_data": json.dumps(log_entry)}
            )
            
        except Exception as e:
            logger.error(f"Failed to log system event: {e}")


# Global instances
degradation_manager = GracefulDegradationManager()
comprehensive_logger = ComprehensiveLogger()


# Convenience functions for easy access
def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get circuit breaker for a service"""
    return degradation_manager.get_circuit_breaker(service_name)


async def execute_with_circuit_breaker(service_name: str, func: Callable, *args, **kwargs):
    """Execute function with circuit breaker protection"""
    return await degradation_manager.execute_with_fallback(service_name, func, *args, **kwargs)


def register_fallback_strategy(service_name: str, fallback_func: Callable):
    """Register fallback strategy for a service"""
    degradation_manager.register_fallback_strategy(service_name, fallback_func)


async def log_triage_decision(issue_id: str, decision_data: Dict[str, Any], processing_time_ms: int):
    """Log triage decision"""
    await comprehensive_logger.log_triage_decision(issue_id, decision_data, processing_time_ms)


def get_system_health() -> Dict[str, Any]:
    """Get system health status"""
    return degradation_manager.get_system_health()