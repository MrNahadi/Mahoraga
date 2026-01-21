"""
Assignment Engine for Mahoraga Triage System

Implements intelligent bug assignment logic that combines AI analysis with git expertise,
includes confidence scoring, workload balancing, and assignment loop prevention.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from database import Assignment, User, SystemConfig, SessionLocal
from ai_analysis_service import BugAnalysis
from git_analysis_engine import ExpertiseScore, GitAnalysisEngine
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AssignmentCandidate:
    """Potential assignee with calculated scores"""
    developer_email: str
    developer_name: str
    expertise_score: float
    workload_score: float
    combined_score: float
    is_active: bool
    current_bug_count: int


@dataclass
class AssignmentResult:
    """Result of assignment calculation"""
    assignee_email: Optional[str]
    assignee_name: Optional[str]
    confidence: float
    reasoning: str
    estimated_effort: str
    priority: str
    should_route_to_human: bool
    fallback_candidates: List[AssignmentCandidate]


class AssignmentEngine:
    """
    Intelligent Assignment Engine that combines AI analysis with git expertise
    
    Features:
    - Confidence score calculation (0-100 range)
    - Assignment logic combining AI analysis with git expertise
    - Workload-based tie-breaking for similar expertise scores
    - Low confidence routing to human triage queue
    - Assignment loop prevention system
    """
    
    def __init__(self, git_engine: Optional[GitAnalysisEngine] = None):
        """
        Initialize Assignment Engine
        
        Args:
            git_engine: Git analysis engine instance (optional, will create if None)
        """
        self.git_engine = git_engine or GitAnalysisEngine()
    
    def calculate_confidence_score(self, 
                                 bug_analysis: Optional[BugAnalysis],
                                 expertise_scores: List[ExpertiseScore],
                                 affected_files: List[str]) -> float:
        """
        Calculate assignment confidence score (0-100 range)
        
        Args:
            bug_analysis: AI analysis result (optional)
            expertise_scores: Git expertise scores for affected files
            affected_files: List of files affected by the bug
            
        Returns:
            Confidence score between 0.0 and 100.0
        """
        confidence_factors = []
        
        # Factor 1: AI Analysis Quality (0-40 points)
        if bug_analysis:
            ai_confidence = bug_analysis.confidence * 40.0
            confidence_factors.append(ai_confidence)
            logger.debug(f"AI analysis confidence contributes: {ai_confidence:.1f} points")
        else:
            logger.debug("No AI analysis available, 0 points from AI")
            confidence_factors.append(0.0)
        
        # Factor 2: Expertise Score Quality (0-35 points)
        if expertise_scores:
            # Use the highest expertise score, normalized
            max_expertise = max(score.score for score in expertise_scores)
            # Normalize to 0-35 range (assuming max reasonable expertise score is 1000)
            expertise_confidence = min(35.0, (max_expertise / 1000.0) * 35.0)
            confidence_factors.append(expertise_confidence)
            logger.debug(f"Expertise score contributes: {expertise_confidence:.1f} points (max score: {max_expertise:.1f})")
        else:
            logger.debug("No expertise scores available, 0 points from expertise")
            confidence_factors.append(0.0)
        
        # Factor 3: File Coverage (0-15 points)
        if affected_files and expertise_scores:
            # Check how many affected files have expertise data
            files_with_expertise = set(score.file_path for score in expertise_scores)
            coverage_ratio = len(files_with_expertise.intersection(affected_files)) / len(affected_files)
            coverage_confidence = coverage_ratio * 15.0
            confidence_factors.append(coverage_confidence)
            logger.debug(f"File coverage contributes: {coverage_confidence:.1f} points ({coverage_ratio:.1%} coverage)")
        else:
            logger.debug("No file coverage data, 0 points from coverage")
            confidence_factors.append(0.0)
        
        # Factor 4: Recency Bonus (0-10 points)
        if expertise_scores:
            # Bonus for recent activity (commits within last 30 days)
            recent_cutoff = datetime.now() - timedelta(days=30)
            recent_scores = [s for s in expertise_scores if s.last_commit_date > recent_cutoff]
            if recent_scores:
                recency_bonus = min(10.0, len(recent_scores) * 2.0)
                confidence_factors.append(recency_bonus)
                logger.debug(f"Recency bonus contributes: {recency_bonus:.1f} points")
            else:
                confidence_factors.append(0.0)
        else:
            confidence_factors.append(0.0)
        
        # Calculate total confidence (max 100)
        total_confidence = sum(confidence_factors)
        
        # Ensure bounds [0, 100]
        final_confidence = max(0.0, min(100.0, total_confidence))
        
        logger.info(f"Confidence calculation: AI={confidence_factors[0]:.1f}, "
                   f"Expertise={confidence_factors[1]:.1f}, Coverage={confidence_factors[2]:.1f}, "
                   f"Recency={confidence_factors[3]:.1f} -> Total={final_confidence:.1f}")
        
        return final_confidence
    
    def get_current_workload(self, developer_email: str) -> int:
        """
        Get current bug count for a developer
        
        Args:
            developer_email: Developer's git email address
            
        Returns:
            Number of currently assigned bugs
        """
        try:
            with SessionLocal() as db:
                active_assignments = db.query(Assignment).filter(
                    Assignment.assigned_to_email == developer_email,
                    Assignment.status == "assigned"
                ).count()
                
                logger.debug(f"Developer {developer_email} has {active_assignments} active assignments")
                return active_assignments
                
        except Exception as e:
            logger.warning(f"Could not get workload for {developer_email}: {e}")
            return 0
    
    def calculate_workload_score(self, current_bug_count: int) -> float:
        """
        Calculate workload score (higher is better, meaning lower workload)
        
        Args:
            current_bug_count: Number of currently assigned bugs
            
        Returns:
            Workload score (0.0 to 1.0, where 1.0 is no workload)
        """
        # Exponential decay: score decreases as workload increases
        # 0 bugs = 1.0, 5 bugs = ~0.37, 10 bugs = ~0.14
        import math
        workload_score = math.exp(-current_bug_count / 5.0)
        
        logger.debug(f"Workload score for {current_bug_count} bugs: {workload_score:.3f}")
        return workload_score
    
    def get_assignment_candidates(self, 
                                affected_files: List[str],
                                bug_analysis: Optional[BugAnalysis] = None) -> List[AssignmentCandidate]:
        """
        Get potential assignment candidates with scores
        
        Args:
            affected_files: List of files affected by the bug
            bug_analysis: AI analysis result (optional)
            
        Returns:
            List of AssignmentCandidate objects sorted by combined score
        """
        candidates = {}
        
        # Collect expertise scores for all affected files
        for file_path in affected_files:
            try:
                expertise_scores = self.git_engine.get_active_contributors(file_path)
                
                for score in expertise_scores:
                    email = score.developer_email
                    
                    if email not in candidates:
                        # Get current workload
                        current_workload = self.get_current_workload(email)
                        workload_score = self.calculate_workload_score(current_workload)
                        
                        candidates[email] = AssignmentCandidate(
                            developer_email=email,
                            developer_name=score.developer_name,
                            expertise_score=score.score,
                            workload_score=workload_score,
                            combined_score=0.0,  # Will be calculated below
                            is_active=score.is_active,
                            current_bug_count=current_workload
                        )
                    else:
                        # Accumulate expertise scores across files
                        candidates[email].expertise_score += score.score
                        
            except Exception as e:
                logger.warning(f"Could not get expertise for file {file_path}: {e}")
                continue
        
        # Calculate combined scores and convert to list
        candidate_list = []
        for candidate in candidates.values():
            # Only include active developers
            if not candidate.is_active:
                logger.debug(f"Skipping inactive developer: {candidate.developer_email}")
                continue
            
            # Combined score: 70% expertise, 30% workload
            candidate.combined_score = (
                0.7 * candidate.expertise_score + 
                0.3 * candidate.workload_score * 100  # Scale workload to match expertise range
            )
            
            candidate_list.append(candidate)
        
        # Sort by combined score (highest first)
        candidate_list.sort(key=lambda x: x.combined_score, reverse=True)
        
        logger.info(f"Found {len(candidate_list)} active assignment candidates")
        for i, candidate in enumerate(candidate_list[:5]):  # Log top 5
            logger.debug(f"Candidate {i+1}: {candidate.developer_email} "
                        f"(expertise: {candidate.expertise_score:.1f}, "
                        f"workload: {candidate.workload_score:.3f}, "
                        f"combined: {candidate.combined_score:.1f})")
        
        return candidate_list
    
    def check_assignment_loop(self, issue_id: str, candidate_email: str) -> bool:
        """
        Check if this assignment would create a loop (same issue assigned to same person)
        
        Args:
            issue_id: GitHub issue ID
            candidate_email: Potential assignee email
            
        Returns:
            True if this would create a loop, False otherwise
        """
        try:
            with SessionLocal() as db:
                # Check if this issue was previously assigned to this person
                previous_assignment = db.query(Assignment).filter(
                    Assignment.issue_id == issue_id,
                    Assignment.assigned_to_email == candidate_email
                ).first()
                
                if previous_assignment:
                    logger.warning(f"Assignment loop detected: Issue {issue_id} was previously assigned to {candidate_email}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Could not check assignment loop for {issue_id}: {e}")
            # Err on the side of caution
            return True
    
    def get_confidence_threshold(self) -> float:
        """
        Get current confidence threshold from system configuration
        
        Returns:
            Confidence threshold (default 60.0)
        """
        try:
            with SessionLocal() as db:
                config = db.query(SystemConfig).filter(
                    SystemConfig.key == "confidence_threshold"
                ).first()
                
                if config:
                    return float(config.value)
                else:
                    return settings.confidence_threshold
                    
        except Exception as e:
            logger.warning(f"Could not get confidence threshold: {e}")
            return settings.confidence_threshold
    
    def calculate_assignment(self, 
                           issue_id: str,
                           affected_files: List[str],
                           bug_analysis: Optional[BugAnalysis] = None) -> AssignmentResult:
        """
        Calculate the best assignment for a bug
        
        Args:
            issue_id: GitHub issue ID
            affected_files: List of files affected by the bug
            bug_analysis: AI analysis result (optional)
            
        Returns:
            AssignmentResult with assignment decision
        """
        logger.info(f"Calculating assignment for issue {issue_id} affecting {len(affected_files)} files")
        
        # Get assignment candidates
        candidates = self.get_assignment_candidates(affected_files, bug_analysis)
        
        if not candidates:
            logger.warning(f"No active contributors found for issue {issue_id}")
            return AssignmentResult(
                assignee_email=None,
                assignee_name=None,
                confidence=0.0,
                reasoning="No active contributors found for affected files",
                estimated_effort="unknown",
                priority="medium",
                should_route_to_human=True,
                fallback_candidates=[]
            )
        
        # Filter out candidates that would create assignment loops
        valid_candidates = []
        for candidate in candidates:
            if not self.check_assignment_loop(issue_id, candidate.developer_email):
                valid_candidates.append(candidate)
            else:
                logger.debug(f"Skipping {candidate.developer_email} due to assignment loop")
        
        if not valid_candidates:
            logger.warning(f"All candidates would create assignment loops for issue {issue_id}")
            return AssignmentResult(
                assignee_email=None,
                assignee_name=None,
                confidence=0.0,
                reasoning="All potential assignees would create assignment loops",
                estimated_effort="unknown",
                priority="medium",
                should_route_to_human=True,
                fallback_candidates=candidates[:3]  # Show original candidates for human review
            )
        
        # Select the best candidate
        best_candidate = valid_candidates[0]
        fallback_candidates = valid_candidates[1:4]  # Up to 3 fallbacks
        
        # Calculate confidence score
        all_expertise_scores = []
        for file_path in affected_files:
            try:
                file_scores = self.git_engine.get_active_contributors(file_path)
                all_expertise_scores.extend(file_scores)
            except Exception as e:
                logger.warning(f"Could not get expertise for confidence calculation: {e}")
        
        confidence = self.calculate_confidence_score(bug_analysis, all_expertise_scores, affected_files)
        
        # Check confidence threshold
        confidence_threshold = self.get_confidence_threshold()
        should_route_to_human = confidence < confidence_threshold
        
        # Generate reasoning
        reasoning_parts = [
            f"Selected {best_candidate.developer_email} based on combined expertise and workload analysis."
        ]
        
        if bug_analysis:
            reasoning_parts.append(f"AI analysis confidence: {bug_analysis.confidence:.1%}")
            if bug_analysis.fix_complexity:
                reasoning_parts.append(f"Estimated complexity: {bug_analysis.fix_complexity}")
        
        reasoning_parts.append(f"Developer expertise score: {best_candidate.expertise_score:.1f}")
        reasoning_parts.append(f"Current workload: {best_candidate.current_bug_count} active bugs")
        
        if should_route_to_human:
            reasoning_parts.append(f"Confidence {confidence:.1f} below threshold {confidence_threshold:.1f}, routing to human triage")
        
        reasoning = " ".join(reasoning_parts)
        
        # Estimate effort based on AI analysis and expertise
        if bug_analysis and bug_analysis.fix_complexity:
            effort_map = {"simple": "1-2 hours", "moderate": "half day", "complex": "1-2 days"}
            estimated_effort = effort_map.get(bug_analysis.fix_complexity, "unknown")
        else:
            estimated_effort = "unknown"
        
        # Determine priority based on confidence and complexity
        if confidence >= 80:
            priority = "high"
        elif confidence >= 60:
            priority = "medium"
        else:
            priority = "low"
        
        result = AssignmentResult(
            assignee_email=best_candidate.developer_email if not should_route_to_human else None,
            assignee_name=best_candidate.developer_name if not should_route_to_human else None,
            confidence=confidence,
            reasoning=reasoning,
            estimated_effort=estimated_effort,
            priority=priority,
            should_route_to_human=should_route_to_human,
            fallback_candidates=fallback_candidates
        )
        
        logger.info(f"Assignment result for {issue_id}: "
                   f"assignee={result.assignee_email}, confidence={confidence:.1f}, "
                   f"route_to_human={should_route_to_human}")
        
        return result
    
    def record_assignment(self, 
                         issue_id: str,
                         issue_url: str,
                         assignment_result: AssignmentResult) -> Optional[Assignment]:
        """
        Record an assignment decision in the database
        
        Args:
            issue_id: GitHub issue ID
            issue_url: GitHub issue URL
            assignment_result: Assignment calculation result
            
        Returns:
            Created Assignment record or None if recording failed
        """
        if assignment_result.should_route_to_human:
            # Don't record assignments that go to human triage
            logger.info(f"Not recording assignment for {issue_id} - routed to human triage")
            return None
        
        try:
            with SessionLocal() as db:
                assignment = Assignment(
                    issue_id=issue_id,
                    issue_url=issue_url,
                    assigned_to_email=assignment_result.assignee_email,
                    confidence=assignment_result.confidence,
                    reasoning=assignment_result.reasoning,
                    status="assigned"
                )
                
                db.add(assignment)
                db.commit()
                db.refresh(assignment)
                
                logger.info(f"Recorded assignment {assignment.id} for issue {issue_id}")
                return assignment
                
        except Exception as e:
            logger.error(f"Failed to record assignment for {issue_id}: {e}")
            return None


# Global assignment engine instance
assignment_engine = AssignmentEngine()


def calculate_bug_assignment(issue_id: str,
                           issue_url: str,
                           affected_files: List[str],
                           bug_analysis: Optional[BugAnalysis] = None) -> AssignmentResult:
    """
    Convenience function for bug assignment calculation
    
    Args:
        issue_id: GitHub issue ID
        issue_url: GitHub issue URL
        affected_files: List of files affected by the bug
        bug_analysis: AI analysis result (optional)
        
    Returns:
        AssignmentResult with assignment decision
    """
    result = assignment_engine.calculate_assignment(issue_id, affected_files, bug_analysis)
    
    # Record the assignment if it's not going to human triage
    if not result.should_route_to_human:
        assignment_engine.record_assignment(issue_id, issue_url, result)
    
    return result