"""
Database configuration and models for Mahoraga Triage Engine
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, UniqueConstraint, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from typing import Generator
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create SQLAlchemy engine with connection pooling
engine_kwargs = {
    "echo": False,  # Set to True for SQL debugging
}

if "sqlite" in settings.database_url:
    # SQLite-specific configuration with connection pooling
    engine_kwargs.update({
        "connect_args": {
            "check_same_thread": False,
            "timeout": 20,
        },
        "poolclass": StaticPool,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    })
else:
    # PostgreSQL/MySQL configuration
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    })

engine = create_engine(settings.database_url, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class User(Base):
    """User mapping between git email and Slack ID"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    git_email = Column(String(255), unique=True, nullable=False, index=True)
    slack_id = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(git_email='{self.git_email}', display_name='{self.display_name}', active={self.is_active})>"


class Assignment(Base):
    """Bug assignment history"""
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String(100), nullable=False, index=True)
    issue_url = Column(String(500), nullable=False)
    assigned_to_email = Column(String(255), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=False)
    status = Column(String(20), default="assigned", nullable=False)  # assigned, completed, reassigned
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Add index for common queries
    __table_args__ = (
        Index('ix_assignments_status_created', 'status', 'created_at'),
        Index('ix_assignments_assignee_status', 'assigned_to_email', 'status'),
    )

    def __repr__(self):
        return f"<Assignment(issue_id='{self.issue_id}', assignee='{self.assigned_to_email}', confidence={self.confidence})>"


class ExpertiseCache(Base):
    """Cached git expertise calculations"""
    __tablename__ = "expertise_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(1000), nullable=False, index=True)
    developer_email = Column(String(255), nullable=False, index=True)
    score = Column(Float, nullable=False)
    commit_count = Column(Integer, nullable=False)
    last_commit_date = Column(DateTime, nullable=False)
    lines_owned = Column(Integer, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Ensure unique combination of file_path and developer_email
    __table_args__ = (
        UniqueConstraint('file_path', 'developer_email', name='uq_expertise_file_developer'),
        Index('ix_expertise_file_score', 'file_path', 'score'),
    )

    def __repr__(self):
        return f"<ExpertiseCache(file='{self.file_path}', developer='{self.developer_email}', score={self.score})>"


class TriageDecision(Base):
    """Complete triage decision records"""
    __tablename__ = "triage_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(String(100), nullable=False, index=True)
    stack_trace = Column(Text)
    affected_files = Column(Text)  # JSON array of file paths
    root_cause = Column(Text)
    confidence = Column(Float, nullable=False)
    draft_pr_url = Column(String(500))
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Add index for performance queries
    __table_args__ = (
        Index('ix_triage_confidence_created', 'confidence', 'created_at'),
        Index('ix_triage_created_desc', 'created_at'),
    )

    def __repr__(self):
        return f"<TriageDecision(issue_id='{self.issue_id}', confidence={self.confidence})>"


class SystemConfig(Base):
    """System configuration key-value store"""
    __tablename__ = "system_config"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(500))  # Optional description of the config key
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value[:50]}...')>"


# Database Migration System
class DatabaseMigration:
    """Simple database migration system for schema changes"""
    
    @staticmethod
    def get_current_version(db_session) -> int:
        """Get current database schema version"""
        try:
            # Check if migration table exists
            result = db_session.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
            if not result.fetchone():
                return 0
            
            # Get latest version
            result = db_session.execute("SELECT MAX(version) FROM schema_migrations")
            version = result.fetchone()[0]
            return version if version is not None else 0
        except Exception as e:
            logger.warning(f"Could not determine schema version: {e}")
            return 0
    
    @staticmethod
    def create_migration_table(db_session):
        """Create the schema migrations tracking table"""
        db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """))
        db_session.commit()
    
    @staticmethod
    def apply_migration(db_session, version: int, description: str, sql_commands: list):
        """Apply a database migration"""
        try:
            for command in sql_commands:
                db_session.execute(command)
            
            # Record migration
            db_session.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                (version, description)
            )
            db_session.commit()
            logger.info(f"Applied migration {version}: {description}")
        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to apply migration {version}: {e}")
            raise
    
    @staticmethod
    def run_migrations(db_session):
        """Run all pending migrations"""
        DatabaseMigration.create_migration_table(db_session)
        current_version = DatabaseMigration.get_current_version(db_session)
        
        # Define migrations (version, description, sql_commands)
        migrations = [
            # Add any future migrations here
            # Example:
            # (1, "Add indexes for performance", [
            #     "CREATE INDEX IF NOT EXISTS ix_custom_index ON table_name(column_name)"
            # ])
        ]
        
        for version, description, commands in migrations:
            if version > current_version:
                DatabaseMigration.apply_migration(db_session, version, description, commands)


def create_tables():
    """Create all database tables and run migrations"""
    try:
        # Create all tables from models
        Base.metadata.create_all(bind=engine)
        
        # Run any pending migrations
        with SessionLocal() as db:
            DatabaseMigration.run_migrations(db)
        
        logger.info("Database tables created and migrations applied successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def get_db() -> Generator:
    """
    Get database session with proper connection management
    
    Yields:
        Database session that automatically closes after use
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_database():
    """Initialize database with default configuration"""
    try:
        create_tables()
        
        # Insert default system configuration if not exists
        with SessionLocal() as db:
            default_configs = [
                ("confidence_threshold", "60.0", "Minimum confidence score for auto-assignment"),
                ("draft_pr_enabled", "true", "Enable automatic draft PR generation"),
                ("duplicate_detection_window_minutes", "10", "Time window for duplicate issue detection"),
                ("max_assignment_retries", "3", "Maximum retries for failed assignments"),
                ("notification_retry_attempts", "5", "Maximum retry attempts for notifications"),
            ]
            
            for key, value, description in default_configs:
                existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
                if not existing:
                    config = SystemConfig(key=key, value=value, description=description)
                    db.add(config)
            
            db.commit()
        
        logger.info("Database initialized with default configuration")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def check_database_health() -> dict:
    """
    Check database connectivity and health
    
    Returns:
        Dictionary with health status information
    """
    try:
        with SessionLocal() as db:
            # Test basic connectivity
            db.execute(text("SELECT 1"))
            
            # Get table counts for health metrics
            user_count = db.query(User).count()
            assignment_count = db.query(Assignment).count()
            expertise_count = db.query(ExpertiseCache).count()
            decision_count = db.query(TriageDecision).count()
            config_count = db.query(SystemConfig).count()
            
            return {
                "status": "healthy",
                "database_url": settings.database_url.split("://")[0] + "://***",  # Hide credentials
                "tables": {
                    "users": user_count,
                    "assignments": assignment_count,
                    "expertise_cache": expertise_count,
                    "triage_decisions": decision_count,
                    "system_config": config_count,
                },
                "connection_pool": {
                    "size": engine.pool.size() if hasattr(engine.pool, 'size') else "N/A",
                    "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else "N/A",
                }
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_url": settings.database_url.split("://")[0] + "://***",
        }


def cleanup_old_data(days_to_keep: int = 90):
    """
    Clean up old data to prevent database bloat
    
    Args:
        days_to_keep: Number of days of data to retain
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with SessionLocal() as db:
            # Clean up old triage decisions
            old_decisions = db.query(TriageDecision).filter(
                TriageDecision.created_at < cutoff_date
            ).count()
            
            if old_decisions > 0:
                db.query(TriageDecision).filter(
                    TriageDecision.created_at < cutoff_date
                ).delete()
                
                logger.info(f"Cleaned up {old_decisions} old triage decisions")
            
            # Clean up old expertise cache entries (keep more recent for performance)
            cache_cutoff = datetime.utcnow() - timedelta(days=30)
            old_cache = db.query(ExpertiseCache).filter(
                ExpertiseCache.calculated_at < cache_cutoff
            ).count()
            
            if old_cache > 0:
                db.query(ExpertiseCache).filter(
                    ExpertiseCache.calculated_at < cache_cutoff
                ).delete()
                
                logger.info(f"Cleaned up {old_cache} old expertise cache entries")
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Failed to clean up old data: {e}")
        raise