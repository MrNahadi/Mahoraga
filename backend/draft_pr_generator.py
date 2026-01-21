"""
Draft PR Generator for Mahoraga Triage Engine

Generates high-confidence draft fixes for bugs and creates GitHub PRs with proper labeling.
Implements constraints for single-file changes under 20 lines with explanatory comments.
"""

import asyncio
import logging
import json
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import httpx
from github import Github, GithubException
from ai_analysis_service import BugAnalysis, ai_service
from stack_trace_parser import StackTrace
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DraftFix:
    """Represents a draft code fix"""
    file_path: str
    original_content: str
    fixed_content: str
    line_changes: int
    explanation: str
    confidence: float


@dataclass
class DraftPR:
    """Result of draft PR generation"""
    title: str
    description: str
    file_changes: Dict[str, str]  # file_path -> new_content
    pr_url: Optional[str]
    confidence: float
    fix_explanation: str
    created_at: datetime


class DraftPRGenerator:
    """
    Draft PR Generator for high-confidence bug fixes
    
    Features:
    - High-confidence draft fix generation (>85% confidence)
    - Single-file, <20 lines change constraint enforcement
    - GitHub PR creation with draft labeling
    - Explanatory comment generation for fixes
    - Graceful error handling for edge cases
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize Draft PR Generator
        
        Args:
            github_token: GitHub API token (optional, will use settings if None)
        """
        self.github_token = github_token or settings.github_token
        self.github_client = None
        
        if self.github_token:
            try:
                self.github_client = Github(self.github_token)
                logger.info("GitHub client initialized for draft PR generation")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub client: {e}")
                self.github_client = None
        else:
            logger.warning("GitHub token not configured - draft PR generation will be disabled")
    
    def should_generate_draft_fix(self, confidence: float) -> bool:
        """
        Check if a draft fix should be generated based on confidence
        
        Args:
            confidence: Assignment confidence score (0-100)
            
        Returns:
            True if draft fix should be generated, False otherwise
        """
        # Only generate draft fixes for high confidence (>85%)
        return confidence > 85.0
    
    async def generate_draft_fix(self, 
                               bug_analysis: BugAnalysis,
                               stack_trace: Optional[StackTrace] = None,
                               repository_url: str = None) -> Optional[DraftFix]:
        """
        Generate a draft code fix for a high-confidence bug
        
        Args:
            bug_analysis: AI analysis result
            stack_trace: Parsed stack trace (optional)
            repository_url: GitHub repository URL
            
        Returns:
            DraftFix object or None if generation fails
        """
        if not self.should_generate_draft_fix(bug_analysis.confidence * 100):
            logger.debug(f"Confidence {bug_analysis.confidence * 100:.1f} too low for draft fix generation")
            return None
        
        if not bug_analysis.affected_files:
            logger.warning("No affected files identified - cannot generate draft fix")
            return None
        
        # Focus on the first affected file for single-file constraint
        target_file = bug_analysis.affected_files[0]
        
        try:
            # Get current file content
            file_content = await self._get_file_content(repository_url, target_file)
            if not file_content:
                logger.warning(f"Could not retrieve content for file: {target_file}")
                return None
            
            # Generate fix using AI
            draft_fix = await self._generate_fix_with_ai(
                bug_analysis, 
                target_file, 
                file_content, 
                stack_trace
            )
            
            if draft_fix and self._validate_fix_constraints(draft_fix):
                logger.info(f"Generated valid draft fix for {target_file}")
                return draft_fix
            else:
                logger.warning(f"Generated fix does not meet constraints for {target_file}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate draft fix: {e}")
            return None
    
    async def _get_file_content(self, repository_url: str, file_path: str) -> Optional[str]:
        """
        Get current content of a file from GitHub repository
        
        Args:
            repository_url: GitHub repository URL
            file_path: Path to the file in the repository
            
        Returns:
            File content as string or None if retrieval fails
        """
        if not self.github_client or not repository_url:
            return None
        
        try:
            # Extract owner/repo from URL
            repo_parts = repository_url.replace("https://github.com/", "").split("/")
            if len(repo_parts) < 2:
                logger.error(f"Invalid repository URL format: {repository_url}")
                return None
            
            owner, repo_name = repo_parts[0], repo_parts[1]
            
            # Get repository and file content
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            file_content = repo.get_contents(file_path)
            
            if hasattr(file_content, 'decoded_content'):
                return file_content.decoded_content.decode('utf-8')
            else:
                logger.error(f"Could not decode file content for {file_path}")
                return None
                
        except GithubException as e:
            logger.error(f"GitHub API error retrieving {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving {file_path}: {e}")
            return None
    
    async def _generate_fix_with_ai(self, 
                                  bug_analysis: BugAnalysis,
                                  file_path: str,
                                  file_content: str,
                                  stack_trace: Optional[StackTrace] = None) -> Optional[DraftFix]:
        """
        Use AI to generate a code fix
        
        Args:
            bug_analysis: AI analysis result
            file_path: Path to the file being fixed
            file_content: Current content of the file
            stack_trace: Parsed stack trace (optional)
            
        Returns:
            DraftFix object or None if generation fails
        """
        try:
            # Build fix generation prompt
            prompt = self._build_fix_prompt(bug_analysis, file_path, file_content, stack_trace)
            
            # Call AI service to generate fix
            fix_response = await self._call_ai_for_fix(prompt)
            
            if fix_response:
                return self._parse_fix_response(fix_response, file_path, file_content)
            else:
                return None
                
        except Exception as e:
            logger.error(f"AI fix generation failed: {e}")
            return None
    
    def _build_fix_prompt(self, 
                         bug_analysis: BugAnalysis,
                         file_path: str,
                         file_content: str,
                         stack_trace: Optional[StackTrace] = None) -> str:
        """
        Build a prompt for AI fix generation
        
        Args:
            bug_analysis: AI analysis result
            file_path: Path to the file being fixed
            file_content: Current content of the file
            stack_trace: Parsed stack trace (optional)
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are an expert software engineer. Generate a minimal code fix for the following bug.",
            "",
            "## Bug Analysis:",
            f"Root Cause: {bug_analysis.root_cause_hypothesis}",
            f"Explanation: {bug_analysis.plain_english_explanation}",
            f"Error Translation: {bug_analysis.error_translation}",
            f"Fix Complexity: {bug_analysis.fix_complexity}",
            "",
            f"## File to Fix: {file_path}",
            "```",
            file_content,
            "```",
            ""
        ]
        
        if stack_trace:
            prompt_parts.extend([
                "## Stack Trace Context:",
                f"Error: {stack_trace.error_message}",
                f"Type: {stack_trace.error_type}",
                ""
            ])
            
            # Add relevant stack frames
            relevant_frames = stack_trace.get_most_relevant_frames(limit=3)
            for frame in relevant_frames:
                if frame.file_path == file_path:
                    prompt_parts.append(f"Problem at line {frame.line_number} in {frame.function_name}")
            
            prompt_parts.append("")
        
        prompt_parts.extend([
            "## Fix Requirements:",
            "1. Make MINIMAL changes (prefer single-file fixes under 20 lines)",
            "2. Focus on the root cause identified in the analysis",
            "3. Add explanatory comments for the fix",
            "4. Preserve existing code style and patterns",
            "5. Ensure the fix is safe and doesn't introduce new issues",
            "",
            "## Response Format:",
            "Provide your response in the following JSON format:",
            "{",
            '  "fixed_content": "complete fixed file content",',
            '  "explanation": "clear explanation of what was changed and why",',
            '  "line_changes": 5,',
            '  "confidence": 0.92',
            "}",
            "",
            "Guidelines:",
            "- Include the complete file content with your fixes applied",
            "- Explain the changes in simple terms",
            "- Count only the lines that were actually modified",
            "- Provide confidence score between 0.0 and 1.0",
            "- If the fix requires more than 20 line changes, explain why it's necessary"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _call_ai_for_fix(self, prompt: str) -> Optional[str]:
        """
        Call AI service to generate a fix
        
        Args:
            prompt: Fix generation prompt
            
        Returns:
            AI response text or None if call fails
        """
        try:
            # Use the existing AI service with timeout
            response = await asyncio.wait_for(
                ai_service._call_gemini_api(prompt),
                timeout=settings.ai_analysis_timeout_seconds
            )
            
            return response
            
        except asyncio.TimeoutError:
            logger.warning("AI fix generation timed out")
            return None
        except Exception as e:
            logger.error(f"AI fix generation error: {e}")
            return None
    
    def _parse_fix_response(self, 
                           response_text: str, 
                           file_path: str, 
                           original_content: str) -> Optional[DraftFix]:
        """
        Parse AI response into a DraftFix object
        
        Args:
            response_text: Raw AI response
            file_path: Path to the file being fixed
            original_content: Original file content
            
        Returns:
            DraftFix object or None if parsing fails
        """
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in AI fix response")
                return None
            
            json_text = response_text[json_start:json_end]
            fix_data = json.loads(json_text)
            
            # Validate required fields
            required_fields = ['fixed_content', 'explanation', 'line_changes', 'confidence']
            for field in required_fields:
                if field not in fix_data:
                    logger.error(f"Missing required field in AI fix response: {field}")
                    return None
            
            # Validate confidence score
            confidence = float(fix_data['confidence'])
            if not 0.0 <= confidence <= 1.0:
                logger.warning(f"Invalid confidence score: {confidence}, clamping to [0.0, 1.0]")
                confidence = max(0.0, min(1.0, confidence))
            
            # Validate line changes
            line_changes = int(fix_data['line_changes'])
            if line_changes < 0:
                logger.warning(f"Invalid line changes count: {line_changes}, setting to 0")
                line_changes = 0
            
            return DraftFix(
                file_path=file_path,
                original_content=original_content,
                fixed_content=fix_data['fixed_content'],
                line_changes=line_changes,
                explanation=fix_data['explanation'],
                confidence=confidence
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI fix response as JSON: {e}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Invalid AI fix response format: {e}")
            return None
    
    def _validate_fix_constraints(self, draft_fix: DraftFix) -> bool:
        """
        Validate that the draft fix meets all constraints
        
        Args:
            draft_fix: Draft fix to validate
            
        Returns:
            True if fix meets constraints, False otherwise
        """
        # Constraint 1: Single file (already enforced by design)
        
        # Constraint 2: Less than 20 lines changed
        if draft_fix.line_changes >= 20:
            logger.warning(f"Draft fix exceeds line change limit: {draft_fix.line_changes} >= 20")
            return False
        
        # Constraint 3: Must have valid content
        if not draft_fix.fixed_content or not draft_fix.fixed_content.strip():
            logger.warning("Draft fix has empty or invalid content")
            return False
        
        # Constraint 4: Must have explanation
        if not draft_fix.explanation or len(draft_fix.explanation.strip()) < 10:
            logger.warning("Draft fix has insufficient explanation")
            return False
        
        # Constraint 5: Content should be different from original
        if draft_fix.fixed_content.strip() == draft_fix.original_content.strip():
            logger.warning("Draft fix content is identical to original")
            return False
        
        logger.debug(f"Draft fix validation passed: {draft_fix.line_changes} lines changed")
        return True
    
    async def create_draft_pr(self, 
                            repository_url: str,
                            draft_fix: DraftFix,
                            bug_analysis: BugAnalysis,
                            issue_id: str) -> Optional[DraftPR]:
        """
        Create a GitHub PR with the draft fix
        
        Args:
            repository_url: GitHub repository URL
            draft_fix: Draft fix to create PR for
            bug_analysis: Original bug analysis
            issue_id: GitHub issue ID
            
        Returns:
            DraftPR object or None if creation fails
        """
        if not self.github_client:
            logger.warning("GitHub client not available - cannot create draft PR")
            return None
        
        try:
            # Extract owner/repo from URL
            repo_parts = repository_url.replace("https://github.com/", "").split("/")
            if len(repo_parts) < 2:
                logger.error(f"Invalid repository URL format: {repository_url}")
                return None
            
            owner, repo_name = repo_parts[0], repo_parts[1]
            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            
            # Create branch for the fix
            branch_name = f"mahoraga-fix-{issue_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Get main branch reference
            main_branch = repo.get_branch(repo.default_branch)
            
            # Create new branch
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=main_branch.commit.sha
            )
            
            # Update file with fix
            file_content = repo.get_contents(draft_fix.file_path, ref=branch_name)
            
            commit_message = f"Draft fix for issue #{issue_id}: {bug_analysis.root_cause_hypothesis[:50]}..."
            
            repo.update_file(
                path=draft_fix.file_path,
                message=commit_message,
                content=draft_fix.fixed_content,
                sha=file_content.sha,
                branch=branch_name
            )
            
            # Create PR
            pr_title = f"DRAFT - Fix for issue #{issue_id}: {bug_analysis.root_cause_hypothesis[:60]}..."
            pr_description = self._build_pr_description(draft_fix, bug_analysis, issue_id)
            
            pr = repo.create_pull(
                title=pr_title,
                body=pr_description,
                head=branch_name,
                base=repo.default_branch,
                draft=True
            )
            
            # Add labels
            try:
                pr.add_to_labels("DRAFT - Review Required", "mahoraga-generated", "bug-fix")
            except Exception as e:
                logger.warning(f"Could not add labels to PR: {e}")
            
            logger.info(f"Created draft PR #{pr.number} for issue #{issue_id}")
            
            return DraftPR(
                title=pr_title,
                description=pr_description,
                file_changes={draft_fix.file_path: draft_fix.fixed_content},
                pr_url=pr.html_url,
                confidence=draft_fix.confidence,
                fix_explanation=draft_fix.explanation,
                created_at=datetime.utcnow()
            )
            
        except GithubException as e:
            logger.error(f"GitHub API error creating draft PR: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating draft PR: {e}")
            return None
    
    def _build_pr_description(self, 
                             draft_fix: DraftFix, 
                             bug_analysis: BugAnalysis, 
                             issue_id: str) -> str:
        """
        Build PR description with fix details
        
        Args:
            draft_fix: Draft fix details
            bug_analysis: Original bug analysis
            issue_id: GitHub issue ID
            
        Returns:
            Formatted PR description
        """
        description_parts = [
            "## 🤖 Mahoraga Draft Fix",
            "",
            f"**⚠️ This is a DRAFT PR generated automatically. Please review carefully before merging.**",
            "",
            f"**Related Issue:** #{issue_id}",
            f"**Confidence Score:** {draft_fix.confidence:.1%}",
            f"**Lines Changed:** {draft_fix.line_changes}",
            "",
            "## 🔍 Bug Analysis",
            f"**Root Cause:** {bug_analysis.root_cause_hypothesis}",
            "",
            f"**Explanation:** {bug_analysis.plain_english_explanation}",
            "",
            f"**Error Translation:** {bug_analysis.error_translation}",
            "",
            "## 🛠️ Fix Details",
            f"**File Modified:** `{draft_fix.file_path}`",
            "",
            f"**What Changed:** {draft_fix.explanation}",
            "",
            "## ✅ Review Checklist",
            "- [ ] Fix addresses the root cause correctly",
            "- [ ] No unintended side effects introduced",
            "- [ ] Code follows project style guidelines",
            "- [ ] Tests pass (if applicable)",
            "- [ ] Documentation updated (if needed)",
            "",
            "## 🚨 Important Notes",
            "- This fix was generated by AI and may not be perfect",
            "- Please test thoroughly before merging",
            "- Consider adding tests to prevent regression",
            "- Feel free to modify or close this PR if needed",
            "",
            f"*Generated by Mahoraga Triage Engine at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*"
        ]
        
        return "\n".join(description_parts)
    
    async def generate_and_create_draft_pr(self, 
                                         bug_analysis: BugAnalysis,
                                         repository_url: str,
                                         issue_id: str,
                                         stack_trace: Optional[StackTrace] = None) -> Optional[DraftPR]:
        """
        Complete workflow: generate draft fix and create PR
        
        Args:
            bug_analysis: AI analysis result
            repository_url: GitHub repository URL
            issue_id: GitHub issue ID
            stack_trace: Parsed stack trace (optional)
            
        Returns:
            DraftPR object or None if process fails
        """
        try:
            # Generate draft fix
            draft_fix = await self.generate_draft_fix(bug_analysis, stack_trace, repository_url)
            
            if not draft_fix:
                logger.info(f"No draft fix generated for issue {issue_id}")
                return None
            
            # Create PR with the fix
            draft_pr = await self.create_draft_pr(repository_url, draft_fix, bug_analysis, issue_id)
            
            if draft_pr:
                logger.info(f"Successfully created draft PR for issue {issue_id}: {draft_pr.pr_url}")
            else:
                logger.warning(f"Failed to create draft PR for issue {issue_id}")
            
            return draft_pr
            
        except Exception as e:
            logger.error(f"Draft PR generation workflow failed for issue {issue_id}: {e}")
            return None
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status for monitoring
        
        Returns:
            Service status information
        """
        return {
            "github_client_available": self.github_client is not None,
            "github_token_configured": self.github_token is not None,
            "service_enabled": self.github_client is not None and self.github_token is not None
        }


# Global draft PR generator instance
draft_pr_generator = DraftPRGenerator()


async def generate_draft_pr_for_bug(bug_analysis: BugAnalysis,
                                  repository_url: str,
                                  issue_id: str,
                                  stack_trace: Optional[StackTrace] = None) -> Optional[DraftPR]:
    """
    Convenience function for draft PR generation
    
    Args:
        bug_analysis: AI analysis result
        repository_url: GitHub repository URL
        issue_id: GitHub issue ID
        stack_trace: Parsed stack trace (optional)
        
    Returns:
        DraftPR object or None if generation fails
    """
    return await draft_pr_generator.generate_and_create_draft_pr(
        bug_analysis, repository_url, issue_id, stack_trace
    )


def get_draft_pr_service_status() -> Dict[str, Any]:
    """
    Get current draft PR service status for monitoring
    
    Returns:
        Service status information
    """
    return draft_pr_generator.get_service_status()