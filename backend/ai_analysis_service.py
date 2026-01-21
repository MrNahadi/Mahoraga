"""
AI Analysis Service for Mahoraga Triage Engine
Integrates with Google Gemini 3 API for intelligent bug analysis
"""

import asyncio
import logging
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import httpx
from config import get_settings
from stack_trace_parser import StackTrace, StackFrame
from error_handling import get_circuit_breaker, execute_with_circuit_breaker, register_fallback_strategy

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class BugAnalysis:
    """Result of AI analysis for a bug report"""
    affected_files: List[str]
    root_cause_hypothesis: str
    plain_english_explanation: str
    fix_complexity: str  # "simple", "moderate", "complex"
    confidence: float
    error_translation: str
    additional_context: Dict[str, Any]
    analysis_timestamp: datetime


class AIAnalysisService:
    """
    AI-powered bug analysis service using Google Gemini 3
    
    Provides:
    - Code context analysis and plain English explanations
    - Error message translation for cryptic errors
    - Affected file identification beyond stack traces
    - Timeout and retry logic for API calls
    - Circuit breaker pattern for graceful degradation
    """
    
    def __init__(self):
        """Initialize AI Analysis Service"""
        self.circuit_breaker = get_circuit_breaker("gemini_api")
        self._configure_gemini()
        self._register_fallback_strategy()
    
    def _configure_gemini(self):
        """Configure Google Gemini API"""
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY not configured - AI analysis will be disabled")
            self.model = None
            return
        
        try:
            genai.configure(api_key=settings.gemini_api_key)
            
            # Configure the model with safety settings
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            logger.info("Gemini AI model configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            self.model = None
    
    def _register_fallback_strategy(self):
        """Register fallback strategy for when AI service is unavailable"""
        async def ai_fallback_strategy(issue_body: str, 
                                     stack_trace: Optional[StackTrace] = None,
                                     code_context: Optional[str] = None) -> Optional[BugAnalysis]:
            """
            Fallback analysis using regex-based parsing when AI is unavailable
            """
            logger.info("Using fallback analysis strategy (AI service unavailable)")
            
            try:
                # Basic regex-based analysis
                affected_files = []
                if stack_trace:
                    affected_files = [frame.file_path for frame in stack_trace.frames[:3]]
                
                # Simple error categorization
                error_keywords = ["null", "undefined", "timeout", "connection", "permission", "syntax"]
                detected_keywords = [kw for kw in error_keywords if kw.lower() in issue_body.lower()]
                
                fix_complexity = "moderate"  # Default to moderate when uncertain
                confidence = 0.3  # Low confidence for fallback analysis
                
                if detected_keywords:
                    confidence = 0.4  # Slightly higher if we detect known patterns
                
                return BugAnalysis(
                    affected_files=affected_files,
                    root_cause_hypothesis=f"Potential issue related to: {', '.join(detected_keywords) if detected_keywords else 'unknown error pattern'}",
                    plain_english_explanation="AI analysis unavailable. This appears to be a technical error that requires manual investigation.",
                    fix_complexity=fix_complexity,
                    confidence=confidence,
                    error_translation=f"Error detected with keywords: {detected_keywords}" if detected_keywords else "Unable to translate error - AI service unavailable",
                    additional_context={
                        "fallback_analysis": True,
                        "detected_keywords": detected_keywords,
                        "analysis_method": "regex_based"
                    },
                    analysis_timestamp=datetime.utcnow()
                )
                
            except Exception as e:
                logger.error(f"Fallback analysis failed: {e}")
                return None
        
        register_fallback_strategy("gemini_api", ai_fallback_strategy)
    
    async def analyze_bug(self, 
                         issue_body: str, 
                         stack_trace: Optional[StackTrace] = None,
                         code_context: Optional[str] = None) -> Optional[BugAnalysis]:
        """
        Analyze a bug report using AI with circuit breaker protection
        
        Args:
            issue_body: Raw issue description text
            stack_trace: Parsed stack trace object (optional)
            code_context: Additional code context (optional)
            
        Returns:
            BugAnalysis object or None if analysis fails
        """
        if not self.model:
            logger.warning("AI analysis unavailable - Gemini not configured")
            return None
        
        try:
            # Use circuit breaker for execution
            return await execute_with_circuit_breaker(
                "gemini_api",
                self._perform_analysis,
                issue_body,
                stack_trace,
                code_context
            )
        except Exception as e:
            logger.error(f"AI analysis failed with circuit breaker: {e}")
            return None
    
    async def _perform_analysis(self, 
                              issue_body: str, 
                              stack_trace: Optional[StackTrace] = None,
                              code_context: Optional[str] = None) -> Optional[BugAnalysis]:
        """
        Perform the actual AI analysis (called by circuit breaker)
        
        Args:
            issue_body: Raw issue description text
            stack_trace: Parsed stack trace object (optional)
            code_context: Additional code context (optional)
            
        Returns:
            BugAnalysis object or None if analysis fails
        """
        # Prepare the analysis prompt
        prompt = self._build_analysis_prompt(issue_body, stack_trace, code_context)
        
        # Execute analysis with timeout and retry
        analysis_result = await self._execute_with_retry(prompt)
        
        return analysis_result
    
    def _build_analysis_prompt(self, 
                              issue_body: str, 
                              stack_trace: Optional[StackTrace] = None,
                              code_context: Optional[str] = None) -> str:
        """
        Build a comprehensive analysis prompt for Gemini
        
        Args:
            issue_body: Raw issue description
            stack_trace: Parsed stack trace
            code_context: Additional code context
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "You are an expert software engineer analyzing a bug report. Please provide a comprehensive analysis.",
            "",
            "## Bug Report:",
            issue_body,
            ""
        ]
        
        if stack_trace:
            prompt_parts.extend([
                "## Stack Trace Analysis:",
                f"Language: {stack_trace.language.value}",
                f"Error Type: {stack_trace.error_type}",
                f"Error Message: {stack_trace.error_message}",
                "",
                "### Stack Frames (most relevant first):",
            ])
            
            # Include most relevant frames
            relevant_frames = stack_trace.get_most_relevant_frames(limit=5)
            for i, frame in enumerate(relevant_frames, 1):
                prompt_parts.append(
                    f"{i}. {frame.file_path}:{frame.line_number} in {frame.function_name}"
                )
                if frame.code_snippet:
                    prompt_parts.append(f"   Code: {frame.code_snippet}")
            
            prompt_parts.append("")
        
        if code_context:
            prompt_parts.extend([
                "## Additional Code Context:",
                code_context,
                ""
            ])
        
        prompt_parts.extend([
            "## Analysis Required:",
            "",
            "Please provide your analysis in the following JSON format:",
            "{",
            '  "affected_files": ["list of file paths that might be affected beyond the stack trace"],',
            '  "root_cause_hypothesis": "your hypothesis about what caused this bug",',
            '  "plain_english_explanation": "explain the technical issue in simple terms",',
            '  "fix_complexity": "simple|moderate|complex",',
            '  "confidence": 0.85,',
            '  "error_translation": "translate cryptic error messages into actionable descriptions",',
            '  "additional_context": {',
            '    "likely_impact": "description of impact",',
            '    "suggested_investigation": "what to look at first",',
            '    "related_components": ["list of related system components"]',
            '  }',
            "}",
            "",
            "Guidelines:",
            "- Focus on actionable insights for developers",
            "- Consider the programming language and framework context",
            "- Identify files beyond the stack trace that might need attention",
            "- Translate technical jargon into clear explanations",
            "- Assess fix complexity based on scope and risk",
            "- Provide confidence score between 0.0 and 1.0",
            "- Be specific about investigation steps"
        ])
        
        return "\n".join(prompt_parts)
    
    async def _execute_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[BugAnalysis]:
        """
        Execute AI analysis with timeout and retry logic
        
        Args:
            prompt: Analysis prompt
            max_retries: Maximum number of retry attempts
            
        Returns:
            BugAnalysis object or None if all attempts fail
        """
        for attempt in range(max_retries):
            try:
                # Execute with timeout
                response = await asyncio.wait_for(
                    self._call_gemini_api(prompt),
                    timeout=settings.ai_analysis_timeout_seconds
                )
                
                if response:
                    return self._parse_analysis_response(response)
                
            except asyncio.TimeoutError:
                logger.warning(f"AI analysis timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    logger.error("AI analysis failed after all retry attempts (timeout)")
                    break
                    
            except Exception as e:
                logger.warning(f"AI analysis error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"AI analysis failed after all retry attempts: {e}")
                    break
        
        return None
    
    async def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """
        Make the actual API call to Gemini
        
        Args:
            prompt: Analysis prompt
            
        Returns:
            Response text or None if call fails
        """
        try:
            # Generate content using the model
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent analysis
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _parse_analysis_response(self, response_text: str) -> Optional[BugAnalysis]:
        """
        Parse the JSON response from Gemini into a BugAnalysis object
        
        Args:
            response_text: Raw response text from Gemini
            
        Returns:
            BugAnalysis object or None if parsing fails
        """
        try:
            # Extract JSON from response (handle cases where there's extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in AI response")
                return None
            
            json_text = response_text[json_start:json_end]
            analysis_data = json.loads(json_text)
            
            # Validate required fields
            required_fields = [
                'affected_files', 'root_cause_hypothesis', 'plain_english_explanation',
                'fix_complexity', 'confidence', 'error_translation'
            ]
            
            for field in required_fields:
                if field not in analysis_data:
                    logger.error(f"Missing required field in AI response: {field}")
                    return None
            
            # Validate confidence score
            confidence = float(analysis_data['confidence'])
            if not 0.0 <= confidence <= 1.0:
                logger.warning(f"Invalid confidence score: {confidence}, clamping to [0.0, 1.0]")
                confidence = max(0.0, min(1.0, confidence))
            
            # Validate fix complexity
            valid_complexities = ['simple', 'moderate', 'complex']
            fix_complexity = analysis_data['fix_complexity'].lower()
            if fix_complexity not in valid_complexities:
                logger.warning(f"Invalid fix complexity: {fix_complexity}, defaulting to 'moderate'")
                fix_complexity = 'moderate'
            
            return BugAnalysis(
                affected_files=analysis_data['affected_files'],
                root_cause_hypothesis=analysis_data['root_cause_hypothesis'],
                plain_english_explanation=analysis_data['plain_english_explanation'],
                fix_complexity=fix_complexity,
                confidence=confidence,
                error_translation=analysis_data['error_translation'],
                additional_context=analysis_data.get('additional_context', {}),
                analysis_timestamp=datetime.utcnow()
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Invalid AI response format: {e}")
            logger.debug(f"Response data: {response_text}")
            return None
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """
        Get current circuit breaker status for monitoring
        
        Returns:
            Dictionary with circuit breaker state information
        """
        return self.circuit_breaker.get_status()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the AI service
        
        Returns:
            Health status information
        """
        if not self.model:
            return {
                "status": "unavailable",
                "reason": "Gemini API not configured",
                "circuit_breaker": self.get_circuit_breaker_status()
            }
        
        if not self.circuit_breaker.can_execute():
            return {
                "status": "degraded",
                "reason": "Circuit breaker is open",
                "circuit_breaker": self.get_circuit_breaker_status()
            }
        
        try:
            # Simple test query with short timeout
            test_response = await asyncio.wait_for(
                self._call_gemini_api("Respond with 'OK' if you can process this request."),
                timeout=5.0
            )
            
            if test_response and "OK" in test_response:
                return {
                    "status": "healthy",
                    "circuit_breaker": self.get_circuit_breaker_status()
                }
            else:
                return {
                    "status": "degraded",
                    "reason": "Unexpected response from Gemini API",
                    "circuit_breaker": self.get_circuit_breaker_status()
                }
                
        except Exception as e:
            logger.warning(f"AI service health check failed: {e}")
            return {
                "status": "degraded",
                "reason": f"Health check failed: {str(e)}",
                "circuit_breaker": self.get_circuit_breaker_status()
            }


# Global service instance
ai_service = AIAnalysisService()


async def analyze_bug_report(issue_body: str, 
                           stack_trace: Optional[StackTrace] = None,
                           code_context: Optional[str] = None) -> Optional[BugAnalysis]:
    """
    Convenience function for bug analysis
    
    Args:
        issue_body: Raw issue description text
        stack_trace: Parsed stack trace object (optional)
        code_context: Additional code context (optional)
        
    Returns:
        BugAnalysis object or None if analysis fails
    """
    return await ai_service.analyze_bug(issue_body, stack_trace, code_context)


def get_ai_service_status() -> Dict[str, Any]:
    """
    Get current AI service status for monitoring
    
    Returns:
        Service status information
    """
    return ai_service.get_circuit_breaker_status()