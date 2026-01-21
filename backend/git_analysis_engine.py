"""
Git Analysis Engine for Mahoraga Triage System

Implements git blame execution, expertise score calculation, and caching
to determine code ownership and developer expertise for bug assignment.
"""

import subprocess
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from database import ExpertiseCache, User, SessionLocal
from config import get_settings
import json
import os

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class GitBlameEntry:
    """Single line entry from git blame output"""
    commit_hash: str
    author_email: str
    author_name: str
    commit_date: datetime
    line_number: int
    line_content: str


@dataclass
class ExpertiseScore:
    """Calculated expertise score for a developer on a specific file"""
    developer_email: str
    developer_name: str
    file_path: str
    score: float
    commit_count: int
    last_commit_date: datetime
    lines_owned: int
    recency_weight: float
    is_active: bool


class GitAnalysisEngine:
    """
    Git Analysis Engine that calculates code ownership and expertise scores
    based on git history analysis with caching for performance.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize Git Analysis Engine
        
        Args:
            repo_path: Path to the git repository (default: current directory)
        """
        self.repo_path = repo_path
        self.bot_patterns = [
            r'.*bot.*',
            r'.*noreply.*',
            r'.*github.*@.*',
            r'.*dependabot.*',
            r'.*renovate.*',
            r'.*automation.*',
            r'.*ci.*@.*',
            r'.*deploy.*@.*'
        ]
        self.merge_commit_patterns = [
            r'^Merge pull request #\d+',
            r'^Merge branch',
            r'^Merge remote-tracking branch',
            r'^Auto-merge',
            r'^Automatic merge'
        ]
    
    def is_bot_account(self, email: str, name: str) -> bool:
        """
        Check if an email/name belongs to a bot account
        
        Args:
            email: Author email address
            name: Author name
            
        Returns:
            True if this appears to be a bot account
        """
        email_lower = email.lower()
        name_lower = name.lower()
        
        # Check email patterns
        for pattern in self.bot_patterns:
            if re.match(pattern, email_lower):
                return True
        
        # Check name patterns
        bot_name_keywords = ['bot', 'automation', 'ci', 'deploy', 'github', 'dependabot', 'renovate']
        for keyword in bot_name_keywords:
            if keyword in name_lower:
                return True
        
        return False
    
    def is_merge_commit(self, commit_message: str) -> bool:
        """
        Check if a commit message indicates a merge commit
        
        Args:
            commit_message: The commit message to check
            
        Returns:
            True if this appears to be a merge commit
        """
        for pattern in self.merge_commit_patterns:
            if re.match(pattern, commit_message.strip()):
                return True
        return False
    
    def execute_git_blame(self, file_path: str) -> List[GitBlameEntry]:
        """
        Execute git blame with rename and move tracking flags
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of GitBlameEntry objects for each line
            
        Raises:
            subprocess.CalledProcessError: If git blame fails
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(os.path.join(self.repo_path, file_path)):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use git blame with rename and move tracking flags as required
        cmd = [
            'git', 'blame',
            '-w',      # Ignore whitespace changes
            '-C', '-C', # Detect copies within and across files
            '-M',      # Detect moves/renames
            '--line-porcelain',  # Machine-readable format
            file_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid characters instead of failing
                timeout=settings.git_blame_timeout_seconds,
                check=True
            )
            
            # Handle case where stdout might be None or empty
            stdout = result.stdout or ""
            return self._parse_git_blame_output(stdout)
            
        except subprocess.TimeoutExpired:
            logger.error(f"Git blame timeout for file: {file_path}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Git blame failed for file {file_path}: {e.stderr}")
            raise
    
    def _parse_git_blame_output(self, blame_output: str) -> List[GitBlameEntry]:
        """
        Parse git blame --line-porcelain output into structured data
        
        Args:
            blame_output: Raw output from git blame --line-porcelain
            
        Returns:
            List of GitBlameEntry objects
        """
        if not blame_output:
            return []
            
        entries = []
        lines = blame_output.strip().split('\n')
        
        i = 0
        while i < len(lines):
            if not lines[i].strip():
                i += 1
                continue
            
            # First line contains commit hash and line info
            commit_line = lines[i].strip()
            if not commit_line:
                i += 1
                continue
            
            parts = commit_line.split()
            if len(parts) < 3:
                i += 1
                continue
            
            commit_hash = parts[0]
            line_number = int(parts[2])
            
            # Parse metadata lines
            author_email = ""
            author_name = ""
            commit_date = None
            line_content = ""
            
            i += 1
            while i < len(lines) and not lines[i].startswith('\t'):
                line = lines[i].strip()
                if line.startswith('author-mail '):
                    author_email = line[12:].strip('<>')
                elif line.startswith('author '):
                    author_name = line[7:]
                elif line.startswith('author-time '):
                    timestamp = int(line[12:])
                    commit_date = datetime.fromtimestamp(timestamp)
                i += 1
            
            # Get the actual line content
            if i < len(lines) and lines[i].startswith('\t'):
                line_content = lines[i][1:]  # Remove leading tab
                i += 1
            
            if commit_date and author_email:
                entries.append(GitBlameEntry(
                    commit_hash=commit_hash,
                    author_email=author_email,
                    author_name=author_name,
                    commit_date=commit_date,
                    line_number=line_number,
                    line_content=line_content
                ))
            else:
                i += 1
        
        return entries
    
    def calculate_recency_weight(self, commit_date: datetime) -> float:
        """
        Calculate recency weight for a commit based on its age
        
        Args:
            commit_date: Date of the commit
            
        Returns:
            Weight factor between 0.1 and 1.0 (newer commits get higher weight)
        """
        now = datetime.now()
        days_old = (now - commit_date).days
        
        # Exponential decay: weight = e^(-days/365)
        # Recent commits (< 30 days) get weight close to 1.0
        # Older commits decay exponentially
        import math
        weight = math.exp(-days_old / 365.0)
        
        # Ensure minimum weight of 0.1 for very old commits
        return max(0.1, weight)
    
    def calculate_expertise_scores(self, file_path: str) -> List[ExpertiseScore]:
        """
        Calculate expertise scores for all developers who have contributed to a file
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of ExpertiseScore objects sorted by score (highest first)
        """
        try:
            # Execute git blame
            blame_entries = self.execute_git_blame(file_path)
            
            if not blame_entries:
                logger.warning(f"No git blame entries found for file: {file_path}")
                return []
            
            # Group entries by developer
            developer_stats = {}
            
            for entry in blame_entries:
                # Skip bot accounts and merge commits
                if self.is_bot_account(entry.author_email, entry.author_name):
                    continue
                
                # Get commit message to check for merge commits
                commit_message = self._get_commit_message(entry.commit_hash)
                if commit_message and self.is_merge_commit(commit_message):
                    continue
                
                email = entry.author_email
                if email not in developer_stats:
                    developer_stats[email] = {
                        'name': entry.author_name,
                        'lines': [],
                        'commits': set(),
                        'last_commit': entry.commit_date
                    }
                
                developer_stats[email]['lines'].append(entry)
                developer_stats[email]['commits'].add(entry.commit_hash)
                
                # Track most recent commit
                if entry.commit_date > developer_stats[email]['last_commit']:
                    developer_stats[email]['last_commit'] = entry.commit_date
            
            # Calculate expertise scores
            expertise_scores = []
            
            for email, stats in developer_stats.items():
                lines_owned = len(stats['lines'])
                commit_count = len(stats['commits'])
                last_commit_date = stats['last_commit']
                
                # Calculate recency weight
                recency_weight = self.calculate_recency_weight(last_commit_date)
                
                # Calculate base score: (lines_owned * commit_count) with recency weighting
                base_score = lines_owned * commit_count
                weighted_score = base_score * recency_weight
                
                # Check if developer is active
                is_active = self._is_developer_active(email)
                
                expertise_scores.append(ExpertiseScore(
                    developer_email=email,
                    developer_name=stats['name'],
                    file_path=file_path,
                    score=weighted_score,
                    commit_count=commit_count,
                    last_commit_date=last_commit_date,
                    lines_owned=lines_owned,
                    recency_weight=recency_weight,
                    is_active=is_active
                ))
            
            # Sort by score (highest first)
            expertise_scores.sort(key=lambda x: x.score, reverse=True)
            
            return expertise_scores
            
        except Exception as e:
            logger.error(f"Failed to calculate expertise scores for {file_path}: {e}")
            return []
    
    def _get_commit_message(self, commit_hash: str) -> Optional[str]:
        """
        Get commit message for a given commit hash
        
        Args:
            commit_hash: The commit hash to look up
            
        Returns:
            Commit message or None if not found
        """
        try:
            result = subprocess.run(
                ['git', 'log', '--format=%s', '-n', '1', commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
    
    def _is_developer_active(self, email: str) -> bool:
        """
        Check if a developer is marked as active in the user database
        
        Args:
            email: Developer's git email address
            
        Returns:
            True if developer is active, False if inactive or not found
        """
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.git_email == email).first()
                return user.is_active if user else True  # Default to active if not in DB
        except Exception as e:
            logger.warning(f"Could not check active status for {email}: {e}")
            return True  # Default to active on error
    
    def get_cached_expertise(self, file_path: str) -> List[ExpertiseScore]:
        """
        Get cached expertise scores for a file if available and fresh
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of cached ExpertiseScore objects or empty list if cache miss
        """
        try:
            with SessionLocal() as db:
                # Check if we have fresh cache entries (less than 24 hours old)
                cache_cutoff = datetime.utcnow() - timedelta(hours=24)
                
                cached_entries = db.query(ExpertiseCache).filter(
                    ExpertiseCache.file_path == file_path,
                    ExpertiseCache.calculated_at > cache_cutoff
                ).all()
                
                if not cached_entries:
                    return []
                
                # Convert to ExpertiseScore objects
                expertise_scores = []
                for entry in cached_entries:
                    # Check current active status
                    is_active = self._is_developer_active(entry.developer_email)
                    
                    # Recalculate recency weight based on current time
                    recency_weight = self.calculate_recency_weight(entry.last_commit_date)
                    
                    # Recalculate score with current recency weight
                    base_score = entry.lines_owned * entry.commit_count
                    current_score = base_score * recency_weight
                    
                    expertise_scores.append(ExpertiseScore(
                        developer_email=entry.developer_email,
                        developer_name="",  # Name not stored in cache
                        file_path=entry.file_path,
                        score=current_score,
                        commit_count=entry.commit_count,
                        last_commit_date=entry.last_commit_date,
                        lines_owned=entry.lines_owned,
                        recency_weight=recency_weight,
                        is_active=is_active
                    ))
                
                # Sort by current score
                expertise_scores.sort(key=lambda x: x.score, reverse=True)
                
                logger.info(f"Using cached expertise data for {file_path} ({len(expertise_scores)} developers)")
                return expertise_scores
                
        except Exception as e:
            logger.warning(f"Failed to retrieve cached expertise for {file_path}: {e}")
            return []
    
    def cache_expertise_scores(self, expertise_scores: List[ExpertiseScore]):
        """
        Cache expertise scores in the database
        
        Args:
            expertise_scores: List of ExpertiseScore objects to cache
        """
        if not expertise_scores:
            return
        
        try:
            with SessionLocal() as db:
                file_path = expertise_scores[0].file_path
                
                # Remove existing cache entries for this file
                db.query(ExpertiseCache).filter(
                    ExpertiseCache.file_path == file_path
                ).delete()
                
                # Add new cache entries
                for score in expertise_scores:
                    cache_entry = ExpertiseCache(
                        file_path=score.file_path,
                        developer_email=score.developer_email,
                        score=score.score,
                        commit_count=score.commit_count,
                        last_commit_date=score.last_commit_date,
                        lines_owned=score.lines_owned,
                        calculated_at=datetime.utcnow()
                    )
                    db.add(cache_entry)
                
                db.commit()
                logger.info(f"Cached expertise scores for {file_path} ({len(expertise_scores)} developers)")
                
        except Exception as e:
            logger.error(f"Failed to cache expertise scores: {e}")
    
    def get_file_expertise(self, file_path: str, use_cache: bool = True) -> List[ExpertiseScore]:
        """
        Get expertise scores for a file, using cache if available
        
        Args:
            file_path: Path to the file to analyze
            use_cache: Whether to use cached results if available
            
        Returns:
            List of ExpertiseScore objects sorted by expertise (highest first)
        """
        # Try cache first if enabled
        if use_cache:
            cached_scores = self.get_cached_expertise(file_path)
            if cached_scores:
                return cached_scores
        
        # Calculate fresh expertise scores
        logger.info(f"Calculating fresh expertise scores for {file_path}")
        expertise_scores = self.calculate_expertise_scores(file_path)
        
        # Cache the results
        if expertise_scores:
            self.cache_expertise_scores(expertise_scores)
        
        return expertise_scores
    
    def get_active_contributors(self, file_path: str) -> List[ExpertiseScore]:
        """
        Get active contributors for a file with fallback logic
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of active ExpertiseScore objects, or empty list if no active contributors
        """
        all_scores = self.get_file_expertise(file_path)
        
        # Filter for active contributors
        active_scores = [score for score in all_scores if score.is_active]
        
        if active_scores:
            logger.info(f"Found {len(active_scores)} active contributors for {file_path}")
            return active_scores
        
        # Fallback: if no active contributors, log warning and return empty list
        # This will trigger routing to human triage queue as per requirements
        logger.warning(f"No active contributors found for {file_path}, routing to human triage")
        return []
    
    def get_primary_and_fallback_assignees(self, file_path: str) -> Tuple[Optional[ExpertiseScore], List[ExpertiseScore]]:
        """
        Get primary assignee and fallback options for a file
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Tuple of (primary_assignee, fallback_assignees)
            primary_assignee is None if no active contributors exist
        """
        active_contributors = self.get_active_contributors(file_path)
        
        if not active_contributors:
            return None, []
        
        primary = active_contributors[0]
        fallbacks = active_contributors[1:5]  # Up to 4 fallback options
        
        logger.info(f"Primary assignee for {file_path}: {primary.developer_email} (score: {primary.score:.2f})")
        if fallbacks:
            fallback_emails = [f.developer_email for f in fallbacks]
            logger.info(f"Fallback assignees: {fallback_emails}")
        
        return primary, fallbacks