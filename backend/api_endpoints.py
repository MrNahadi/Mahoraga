"""
API endpoints for Mahoraga Triage Engine
Provides dashboard data, user management, configuration, and assignment management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
import json
import logging

from database import get_db, User, Assignment, ExpertiseCache, TriageDecision, SystemConfig
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create API router
router = APIRouter(prefix="/api", tags=["api"])

# Pydantic models for request/response validation
class UserCreate(BaseModel):
    git_email: str = Field(..., description="Git email address")
    slack_id: str = Field(..., description="Slack user ID")
    display_name: str = Field(..., description="Display name")
    is_active: bool = Field(default=True, description="Whether user is active")

    @validator('git_email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('slack_id')
    def validate_slack_id(cls, v):
        if not v.startswith('U') or len(v) < 9:
            raise ValueError('Invalid Slack ID format')
        return v


class UserUpdate(BaseModel):
    slack_id: Optional[str] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('slack_id')
    def validate_slack_id(cls, v):
        if v and (not v.startswith('U') or len(v) < 9):
            raise ValueError('Invalid Slack ID format')
        return v


class UserResponse(BaseModel):
    id: int
    git_email: str
    slack_id: str
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemSettings(BaseModel):
    confidence_threshold: float = Field(ge=0, le=100, description="Confidence threshold (0-100)")
    draft_pr_enabled: bool = Field(description="Enable draft PR generation")
    duplicate_detection_window_minutes: int = Field(ge=1, le=60, description="Duplicate detection window in minutes")
    max_assignment_retries: int = Field(ge=1, le=10, description="Maximum assignment retries")
    notification_retry_attempts: int = Field(ge=1, le=10, description="Notification retry attempts")


class AssignmentReassign(BaseModel):
    new_assignee_email: str = Field(..., description="New assignee email")
    reason: str = Field(..., description="Reason for reassignment")

    @validator('new_assignee_email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


class TeamStats(BaseModel):
    developers: List[Dict[str, Any]]
    recent_decisions: List[Dict[str, Any]]
    total_active_bugs: int
    average_confidence: float
    processing_metrics: Dict[str, Any]


class BusFactorData(BaseModel):
    risk_files: List[Dict[str, Any]]
    ownership_data: List[Dict[str, Any]]
    total_files_analyzed: int
    high_risk_count: int


class HealthMetrics(BaseModel):
    system_status: str
    database_health: Dict[str, Any]
    api_dependencies: Dict[str, Any]
    performance_metrics: Dict[str, Any]


# Dashboard Data Endpoints
@router.get("/dashboard/stats", response_model=TeamStats)
async def get_team_stats(db: Session = Depends(get_db)):
    """
    Get team statistics including bug counts per developer and recent triage decisions
    
    Returns:
        TeamStats: Team load data and recent decisions
    """
    try:
        # Get active assignments per developer
        active_assignments = (
            db.query(
                Assignment.assigned_to_email,
                func.count(Assignment.id).label('bug_count'),
                func.avg(Assignment.confidence).label('avg_confidence')
            )
            .filter(Assignment.status == 'assigned')
            .group_by(Assignment.assigned_to_email)
            .all()
        )

        # Create map of assignments
        assignment_map = {
            a.assigned_to_email: {
                "bug_count": a.bug_count,
                "avg_confidence": a.avg_confidence or 0
            }
            for a in active_assignments
        }

        # Get all users with git email
        all_users = db.query(User).filter(User.git_email.isnot(None)).all()

        # Format developer data
        developers = []
        total_bugs = 0
        confidence_sum = 0
        confidence_count = 0

        for user in all_users:
            stats = assignment_map.get(user.git_email, {"bug_count": 0, "avg_confidence": 0})
            bug_count = stats["bug_count"]
            avg_confidence = stats["avg_confidence"]
            
            developers.append({
                "email": user.git_email,
                "display_name": user.display_name,
                "bug_count": bug_count,
                "average_confidence": round(avg_confidence, 1),
                "is_overloaded": bug_count > 5  # Warning threshold from requirements
            })
            
            total_bugs += bug_count
            confidence_sum += avg_confidence * bug_count
            confidence_count += bug_count

        # Get recent triage decisions (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_decisions = (
            db.query(TriageDecision)
            .filter(TriageDecision.created_at >= recent_cutoff)
            .order_by(desc(TriageDecision.created_at))
            .limit(20)
            .all()
        )

        recent_decisions_data = []
        for decision in recent_decisions:
            affected_files = []
            if decision.affected_files:
                try:
                    affected_files = json.loads(decision.affected_files)
                except json.JSONDecodeError:
                    affected_files = [decision.affected_files]

            recent_decisions_data.append({
                "issue_id": decision.issue_id,
                "confidence": decision.confidence,
                "affected_files": affected_files,
                "root_cause": decision.root_cause,
                "has_draft_pr": bool(decision.draft_pr_url),
                "processing_time_ms": decision.processing_time_ms,
                "created_at": decision.created_at.isoformat()
            })

        # Calculate overall average confidence
        overall_avg_confidence = confidence_sum / confidence_count if confidence_count > 0 else 0

        # Calculate processing metrics
        avg_processing_time = 0
        decisions_last_hour = 0
        if recent_decisions:
            processing_times = [d.processing_time_ms for d in recent_decisions if d.processing_time_ms is not None]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
            
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            decisions_last_hour = sum(1 for d in recent_decisions if d.created_at >= one_hour_ago)
            
        processing_metrics = {
             "average_processing_time_ms": round(avg_processing_time, 2),
             "decisions_last_24h": len(recent_decisions),
             "decisions_last_1h": decisions_last_hour,
             "total_decisions": len(recent_decisions)  # Alias for test compatibility
        }

        return TeamStats(
            developers=developers,
            recent_decisions=recent_decisions_data,
            total_active_bugs=total_bugs,
            average_confidence=round(overall_avg_confidence, 1),
            processing_metrics=processing_metrics
        )


    except Exception as e:
        logger.error(f"Failed to get team stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve team statistics")


@router.get("/dashboard/bus-factor", response_model=BusFactorData)
async def get_bus_factor_data(db: Session = Depends(get_db)):
    """
    Get bus factor analysis including knowledge risk files and ownership data
    
    Returns:
        BusFactorData: Knowledge risk analysis
    """
    try:
        # Get files with single active contributors
        # First, get all files and their top contributor
        file_expertise = (
            db.query(
                ExpertiseCache.file_path,
                ExpertiseCache.developer_email,
                ExpertiseCache.score,
                ExpertiseCache.lines_owned,
                func.row_number().over(
                    partition_by=ExpertiseCache.file_path,
                    order_by=desc(ExpertiseCache.score)
                ).label('rank')
            )
            .join(User, User.git_email == ExpertiseCache.developer_email)
            .filter(User.is_active == True)
            .subquery()
        )

        # Get top contributor for each file
        top_contributors = (
            db.query(file_expertise)
            .filter(file_expertise.c.rank == 1)
            .all()
        )

        # Get second contributors for risk assessment
        second_contributors = (
            db.query(file_expertise)
            .filter(file_expertise.c.rank == 2)
            .all()
        )

        second_contributor_map = {sc.file_path: sc.score for sc in second_contributors}

        # Identify high-risk files (single contributor or large expertise gap)
        risk_files = []
        for top in top_contributors:
            second_score = second_contributor_map.get(top.file_path, 0)
            expertise_gap = top.score - second_score
            
            # High risk if no second contributor or large expertise gap (>70% of top score)
            is_high_risk = second_score == 0 or expertise_gap > (top.score * 0.7)
            
            if is_high_risk:
                risk_files.append({
                    "file_path": top.file_path,
                    "primary_owner": top.developer_email,
                    "ownership_score": round(top.score, 2),
                    "lines_owned": top.lines_owned,
                    "has_backup": second_score > 0,
                    "expertise_gap": round(expertise_gap, 2)
                })

        # Calculate ownership percentages per developer
        total_files_per_dev = (
            db.query(
                ExpertiseCache.developer_email,
                func.count(ExpertiseCache.file_path).label('total_files')
            )
            .join(User, User.git_email == ExpertiseCache.developer_email)
            .filter(User.is_active == True)
            .group_by(ExpertiseCache.developer_email)
            .all()
        )

        # Get files where developer is the clear primary owner (>60% score advantage)
        primary_ownership = (
            db.query(
                file_expertise.c.developer_email,
                func.count(file_expertise.c.file_path).label('primary_files')
            )
            .filter(
                and_(
                    file_expertise.c.rank == 1,
                    file_expertise.c.score > 60  # Minimum expertise threshold
                )
            )
            .group_by(file_expertise.c.developer_email)
            .all()
        )

        primary_ownership_map = {po.developer_email: po.primary_files for po in primary_ownership}
        total_files_map = {tf.developer_email: tf.total_files for tf in total_files_per_dev}

        # Get user display names
        users = {user.git_email: user.display_name for user in db.query(User).filter(User.is_active == True).all()}

        ownership_data = []
        for email, total_files in total_files_map.items():
            primary_files = primary_ownership_map.get(email, 0)
            ownership_percentage = (primary_files / total_files * 100) if total_files > 0 else 0
            
            ownership_data.append({
                "developer_email": email,
                "display_name": users.get(email, email),
                "total_files": total_files,
                "primary_files": primary_files,
                "ownership_percentage": round(ownership_percentage, 1),
                "is_high_concentration": ownership_percentage > 40  # High concentration threshold
            })

        # Sort by ownership percentage descending
        ownership_data.sort(key=lambda x: x['ownership_percentage'], reverse=True)

        total_files_analyzed = len(top_contributors)
        high_risk_count = len(risk_files)

        return BusFactorData(
            risk_files=risk_files,
            ownership_data=ownership_data,
            total_files_analyzed=total_files_analyzed,
            high_risk_count=high_risk_count
        )

    except Exception as e:
        logger.error(f"Failed to get bus factor data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bus factor analysis")


@router.get("/dashboard/health", response_model=HealthMetrics)
async def get_health_metrics(db: Session = Depends(get_db)):
    """
    Get system health metrics including database status and performance data
    
    Returns:
        HealthMetrics: System health information
    """
    try:
        from database import check_database_health
        from config import validate_required_env_vars
        
        # Get database health
        db_health = check_database_health()
        
        # Check API dependencies
        env_validation = validate_required_env_vars()
        api_dependencies = {
            "github_configured": env_validation.get("GITHUB_TOKEN", False),
            "slack_configured": env_validation.get("SLACK_BOT_TOKEN", False),
            "gemini_configured": env_validation.get("GEMINI_API_KEY", False),
            "webhook_secret_configured": env_validation.get("GITHUB_WEBHOOK_SECRET", False)
        }
        
        # Get performance metrics
        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_decisions = (
            db.query(TriageDecision)
            .filter(
                and_(
                    TriageDecision.created_at >= recent_cutoff,
                    TriageDecision.processing_time_ms.isnot(None)
                )
            )
            .all()
        )
        
        processing_times = [d.processing_time_ms for d in recent_decisions if d.processing_time_ms]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        performance_metrics = {
            "average_processing_time_ms": round(avg_processing_time, 2),
            "decisions_last_hour": len(recent_decisions),
            "target_processing_time_ms": 10000,  # 10 seconds from requirements
            "performance_status": "good" if avg_processing_time < 10000 else "degraded"
        }
        
        # Determine overall system status
        system_status = "healthy"
        if db_health["status"] != "healthy":
            system_status = "degraded"
        elif not all(api_dependencies.values()):
            system_status = "degraded"
        elif performance_metrics["performance_status"] == "degraded":
            system_status = "degraded"
        
        return HealthMetrics(
            system_status=system_status,
            database_health=db_health,
            api_dependencies=api_dependencies,
            performance_metrics=performance_metrics
        )
        
    except Exception as e:
        logger.error(f"Failed to get health metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve health metrics")


# User Management Endpoints
@router.get("/config/users", response_model=List[UserResponse])
async def get_users(
    active_only: bool = Query(False, description="Return only active users"),
    db: Session = Depends(get_db)
):
    """
    Get list of user mappings
    
    Args:
        active_only: If True, return only active users
        
    Returns:
        List[UserResponse]: List of user mappings
    """
    try:
        query = db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        
        users = query.order_by(User.display_name).all()
        return [UserResponse.from_orm(user) for user in users]
        
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


@router.post("/config/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create new user mapping
    
    Args:
        user_data: User creation data
        
    Returns:
        UserResponse: Created user mapping
    """
    try:
        # Check for existing user with same email or Slack ID
        existing_email = db.query(User).filter(User.git_email == user_data.git_email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        existing_slack = db.query(User).filter(User.slack_id == user_data.slack_id).first()
        if existing_slack:
            raise HTTPException(status_code=400, detail="User with this Slack ID already exists")
        
        # Create new user
        user = User(
            git_email=user_data.git_email,
            slack_id=user_data.slack_id,
            display_name=user_data.display_name,
            is_active=user_data.is_active
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Created user mapping: {user_data.git_email} -> {user_data.slack_id}")
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


@router.put("/config/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """
    Update existing user mapping
    
    Args:
        user_id: User ID to update
        user_data: User update data
        
    Returns:
        UserResponse: Updated user mapping
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check for conflicts if updating Slack ID
        if user_data.slack_id and user_data.slack_id != user.slack_id:
            existing_slack = db.query(User).filter(
                and_(User.slack_id == user_data.slack_id, User.id != user_id)
            ).first()
            if existing_slack:
                raise HTTPException(status_code=400, detail="User with this Slack ID already exists")
        
        # Update fields
        if user_data.slack_id is not None:
            user.slack_id = user_data.slack_id
        if user_data.display_name is not None:
            user.display_name = user_data.display_name
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Updated user mapping: {user.git_email}")
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.delete("/config/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete user mapping
    
    Args:
        user_id: User ID to delete
        
    Returns:
        dict: Success message
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has active assignments
        active_assignments = db.query(Assignment).filter(
            and_(
                Assignment.assigned_to_email == user.git_email,
                Assignment.status == 'assigned'
            )
        ).count()
        
        if active_assignments > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete user with {active_assignments} active assignments"
            )
        
        db.delete(user)
        db.commit()
        
        logger.info(f"Deleted user mapping: {user.git_email}")
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")


# Configuration Endpoints
@router.get("/config/settings", response_model=SystemSettings)
async def get_system_settings(db: Session = Depends(get_db)):
    """
    Get current system settings
    
    Returns:
        SystemSettings: Current system configuration
    """
    try:
        configs = db.query(SystemConfig).all()
        config_dict = {config.key: config.value for config in configs}
        
        # Convert to proper types and provide defaults
        settings = SystemSettings(
            confidence_threshold=float(config_dict.get("confidence_threshold", "60.0")),
            draft_pr_enabled=config_dict.get("draft_pr_enabled", "true").lower() == "true",
            duplicate_detection_window_minutes=int(config_dict.get("duplicate_detection_window_minutes", "10")),
            max_assignment_retries=int(config_dict.get("max_assignment_retries", "3")),
            notification_retry_attempts=int(config_dict.get("notification_retry_attempts", "5"))
        )
        
        return settings
        
    except Exception as e:
        logger.error(f"Failed to get system settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system settings")


@router.put("/config/settings", response_model=SystemSettings)
async def update_system_settings(settings: SystemSettings, db: Session = Depends(get_db)):
    """
    Update system settings
    
    Args:
        settings: New system settings
        
    Returns:
        SystemSettings: Updated system configuration
    """
    try:
        # Convert settings to config entries
        config_updates = {
            "confidence_threshold": str(settings.confidence_threshold),
            "draft_pr_enabled": str(settings.draft_pr_enabled).lower(),
            "duplicate_detection_window_minutes": str(settings.duplicate_detection_window_minutes),
            "max_assignment_retries": str(settings.max_assignment_retries),
            "notification_retry_attempts": str(settings.notification_retry_attempts)
        }
        
        # Update or create each config entry
        for key, value in config_updates.items():
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config:
                config.value = value
                config.updated_at = datetime.utcnow()
            else:
                config = SystemConfig(key=key, value=value)
                db.add(config)
        
        db.commit()
        
        logger.info("Updated system settings")
        return settings
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update system settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update system settings")


# Assignment Management Endpoints
@router.get("/assignments/history")
async def get_assignment_history(
    limit: int = Query(50, ge=1, le=200, description="Number of assignments to return"),
    offset: int = Query(0, ge=0, description="Number of assignments to skip"),
    status: Optional[str] = Query(None, description="Filter by assignment status"),
    assignee_email: Optional[str] = Query(None, description="Filter by assignee email"),
    db: Session = Depends(get_db)
):
    """
    Get paginated assignment history
    
    Args:
        limit: Number of assignments to return (1-200)
        offset: Number of assignments to skip
        status: Filter by assignment status
        assignee_email: Filter by assignee email
        
    Returns:
        dict: Paginated assignment history with metadata
    """
    try:
        query = db.query(Assignment)
        
        # Apply filters
        if status:
            query = query.filter(Assignment.status == status)
        if assignee_email:
            query = query.filter(Assignment.assigned_to_email == assignee_email.lower())
        
        # Get total count for pagination
        total_count = query.count()
        
        # Get assignments with pagination
        assignments = (
            query.order_by(desc(Assignment.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        # Get user display names
        users = {user.git_email: user.display_name for user in db.query(User).all()}
        
        # Format assignment data
        assignment_data = []
        for assignment in assignments:
            assignment_data.append({
                "id": assignment.id,
                "issue_id": assignment.issue_id,
                "issue_url": assignment.issue_url,
                "assigned_to_email": assignment.assigned_to_email,
                "assignee_display_name": users.get(assignment.assigned_to_email, assignment.assigned_to_email),
                "confidence": assignment.confidence,
                "reasoning": assignment.reasoning,
                "status": assignment.status,
                "created_at": assignment.created_at.isoformat(),
                "updated_at": assignment.updated_at.isoformat()
            })
        
        return {
            "assignments": assignment_data,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get assignment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assignment history")


@router.post("/assignments/{assignment_id}/reassign")
async def reassign_assignment(
    assignment_id: int,
    reassign_data: AssignmentReassign,
    db: Session = Depends(get_db)
):
    """
    Reassign an assignment to a different user
    
    Args:
        assignment_id: Assignment ID to reassign
        reassign_data: Reassignment data including new assignee and reason
        
    Returns:
        dict: Updated assignment information
    """
    try:
        # Get the assignment
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Check if new assignee exists and is active
        new_assignee = db.query(User).filter(User.git_email == reassign_data.new_assignee_email).first()
        if not new_assignee:
            raise HTTPException(status_code=400, detail="New assignee not found in user mappings")
        if not new_assignee.is_active:
            raise HTTPException(status_code=400, detail="New assignee is not active")
        
        # Update assignment
        old_assignee = assignment.assigned_to_email
        assignment.assigned_to_email = reassign_data.new_assignee_email
        assignment.reasoning = f"Reassigned from {old_assignee}: {reassign_data.reason}"
        assignment.status = "reassigned"
        assignment.updated_at = datetime.utcnow()
        
        # Create new assignment record for the new assignee
        new_assignment = Assignment(
            issue_id=assignment.issue_id,
            issue_url=assignment.issue_url,
            assigned_to_email=reassign_data.new_assignee_email,
            confidence=assignment.confidence,
            reasoning=f"Reassigned from {old_assignee}: {reassign_data.reason}",
            status="assigned"
        )
        
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)
        
        logger.info(f"Reassigned assignment {assignment_id} from {old_assignee} to {reassign_data.new_assignee_email}")
        
        return {
            "message": "Assignment reassigned successfully",
            "old_assignment_id": assignment_id,
            "new_assignment_id": new_assignment.id,
            "old_assignee": old_assignee,
            "new_assignee": reassign_data.new_assignee_email,
            "reason": reassign_data.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reassign assignment {assignment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reassign assignment")


@router.put("/assignments/{assignment_id}/status")
async def update_assignment_status(
    assignment_id: int,
    status: str = Query(..., description="New assignment status"),
    db: Session = Depends(get_db)
):
    """
    Update assignment status
    
    Args:
        assignment_id: Assignment ID to update
        status: New status (assigned, completed, reassigned)
        
    Returns:
        dict: Updated assignment information
    """
    try:
        valid_statuses = ["assigned", "completed", "reassigned"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        old_status = assignment.status
        assignment.status = status
        assignment.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(assignment)
        
        logger.info(f"Updated assignment {assignment_id} status from {old_status} to {status}")
        
        return {
            "message": "Assignment status updated successfully",
            "assignment_id": assignment_id,
            "old_status": old_status,
            "new_status": status,
            "updated_at": assignment.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update assignment {assignment_id} status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update assignment status")