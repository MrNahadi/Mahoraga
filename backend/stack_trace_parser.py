"""
Stack Trace Parser for Mahoraga Triage Engine
Handles multi-language stack trace parsing and analysis
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported programming languages for stack trace parsing"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    UNKNOWN = "unknown"


@dataclass
class StackFrame:
    """Represents a single frame in a stack trace"""
    file_path: str
    line_number: int
    function_name: str
    code_snippet: str
    relevance_score: float
    
    def __post_init__(self):
        """Validate stack frame data"""
        if self.line_number < 0:
            self.line_number = 0
        if self.relevance_score < 0.0:
            self.relevance_score = 0.0
        elif self.relevance_score > 1.0:
            self.relevance_score = 1.0


@dataclass
class StackTrace:
    """Represents a complete stack trace with metadata"""
    frames: List[StackFrame]
    error_message: str
    error_type: str
    language: Language
    
    def get_most_relevant_frames(self, limit: int = 5) -> List[StackFrame]:
        """Get the most relevant frames sorted by relevance score"""
        return sorted(self.frames, key=lambda f: f.relevance_score, reverse=True)[:limit]
    
    def get_file_paths(self) -> List[str]:
        """Get all unique file paths from the stack trace"""
        return list(set(frame.file_path for frame in self.frames if frame.file_path))


class StackTraceParser:
    """Multi-language stack trace parser with relevance ranking"""
    
    def __init__(self):
        self._python_patterns = self._init_python_patterns()
        self._javascript_patterns = self._init_javascript_patterns()
        self._java_patterns = self._init_java_patterns()
    
    def parse_stack_trace(self, issue_body: str) -> Optional[StackTrace]:
        """
        Parse stack trace from issue body text
        
        Args:
            issue_body: Raw issue description text
            
        Returns:
            StackTrace object or None if no valid stack trace found
        """
        if not issue_body or not issue_body.strip():
            return None
        
        # Detect language and extract stack trace
        language = self._detect_language(issue_body)
        
        if language == Language.PYTHON:
            return self._parse_python_stack_trace(issue_body)
        elif language == Language.JAVASCRIPT:
            return self._parse_javascript_stack_trace(issue_body)
        elif language == Language.JAVA:
            return self._parse_java_stack_trace(issue_body)
        else:
            # Try generic parsing as fallback
            return self._parse_generic_stack_trace(issue_body)
    
    def _detect_language(self, text: str) -> Language:
        """
        Detect programming language from stack trace patterns
        
        Args:
            text: Stack trace text
            
        Returns:
            Detected language enum
        """
        text_lower = text.lower()
        
        # Python indicators
        python_indicators = [
            "traceback (most recent call last)",
            "file \"", "line ", "in ",
            ".py\"", "python", "django", "flask"
        ]
        
        # JavaScript indicators  
        js_indicators = [
            "at ", "node.js", "javascript", ".js:", 
            "typeerror:", "referenceerror:", "syntaxerror:",
            "webpack://", "chrome-extension://"
        ]
        
        # Java indicators
        java_indicators = [
            "exception in thread", "at ", ".java:",
            "caused by:", "java.lang.", "java.util.",
            "org.springframework", "com.example"
        ]
        
        # Count indicators for each language
        python_score = sum(1 for indicator in python_indicators if indicator in text_lower)
        js_score = sum(1 for indicator in js_indicators if indicator in text_lower)
        java_score = sum(1 for indicator in java_indicators if indicator in text_lower)
        
        # Return language with highest score
        if python_score >= js_score and python_score >= java_score and python_score > 0:
            return Language.PYTHON
        elif js_score >= java_score and js_score > 0:
            return Language.JAVASCRIPT
        elif java_score > 0:
            return Language.JAVA
        else:
            return Language.UNKNOWN
    
    def _init_python_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize Python stack trace regex patterns"""
        return {
            "traceback_start": re.compile(r"Traceback \(most recent call last\):", re.IGNORECASE),
            "frame": re.compile(r'File "([^"]+)", line (\d+), in (.+)'),
            "code_line": re.compile(r"^\s+(.+)$", re.MULTILINE),
            "error_line": re.compile(r"^(\w+(?:Error|Exception)): (.+)$", re.MULTILINE),
        }
    
    def _init_javascript_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize JavaScript stack trace regex patterns"""
        return {
            "frame": re.compile(r"at (?:(.+) \()?([^:]+):(\d+):(\d+)\)?"),
            "node_frame": re.compile(r"at (.+) \(([^:]+):(\d+):(\d+)\)"),
            "error_line": re.compile(r"^(\w+(?:Error|Exception)): (.+)$", re.MULTILINE),
            "webpack_frame": re.compile(r"at (.+) \(webpack://[^:]+:(\d+):(\d+)\)"),
        }
    
    def _init_java_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize Java stack trace regex patterns"""
        return {
            "frame": re.compile(r"at ([^(]+)\(([^:]+):(\d+)\)"),
            "error_line": re.compile(r"^(\w+(?:Exception|Error)): (.+)$", re.MULTILINE),
            "caused_by": re.compile(r"^Caused by: (\w+(?:Exception|Error)): (.+)$", re.MULTILINE),
        }
    
    def _parse_python_stack_trace(self, text: str) -> Optional[StackTrace]:
        """Parse Python stack trace"""
        patterns = self._python_patterns
        
        # Find traceback start
        traceback_match = patterns["traceback_start"].search(text)
        if not traceback_match:
            return None
        
        # Extract frames
        frames = []
        frame_matches = patterns["frame"].findall(text)
        
        for i, (file_path, line_num, function_name) in enumerate(frame_matches):
            try:
                line_number = int(line_num)
                
                # Extract code snippet (next line after frame)
                code_snippet = self._extract_code_snippet(text, file_path, line_number)
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(
                    file_path, function_name, i, len(frame_matches), Language.PYTHON
                )
                
                frame = StackFrame(
                    file_path=file_path,
                    line_number=line_number,
                    function_name=function_name,
                    code_snippet=code_snippet,
                    relevance_score=relevance_score
                )
                frames.append(frame)
                
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse Python frame: {e}")
                continue
        
        # Extract error information
        error_type, error_message = self._extract_error_info(text, patterns["error_line"])
        
        if not frames:
            return None
        
        return StackTrace(
            frames=frames,
            error_message=error_message,
            error_type=error_type,
            language=Language.PYTHON
        )
    
    def _parse_javascript_stack_trace(self, text: str) -> Optional[StackTrace]:
        """Parse JavaScript stack trace"""
        patterns = self._javascript_patterns
        
        frames = []
        
        # Try different JavaScript frame patterns
        for pattern_name, pattern in [("frame", patterns["frame"]), ("node_frame", patterns["node_frame"])]:
            frame_matches = pattern.findall(text)
            
            for i, match in enumerate(frame_matches):
                try:
                    if pattern_name == "frame" and len(match) == 4:
                        function_name, file_path, line_num, col_num = match
                    elif pattern_name == "node_frame" and len(match) == 4:
                        function_name, file_path, line_num, col_num = match
                    else:
                        continue
                    
                    line_number = int(line_num)
                    
                    # Clean up function name
                    if not function_name or function_name.strip() == "":
                        function_name = "<anonymous>"
                    
                    # Extract code snippet
                    code_snippet = self._extract_code_snippet(text, file_path, line_number)
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(
                        file_path, function_name, i, len(frame_matches), Language.JAVASCRIPT
                    )
                    
                    frame = StackFrame(
                        file_path=file_path,
                        line_number=line_number,
                        function_name=function_name,
                        code_snippet=code_snippet,
                        relevance_score=relevance_score
                    )
                    frames.append(frame)
                    
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse JavaScript frame: {e}")
                    continue
        
        # Extract error information
        error_type, error_message = self._extract_error_info(text, patterns["error_line"])
        
        if not frames:
            return None
        
        return StackTrace(
            frames=frames,
            error_message=error_message,
            error_type=error_type,
            language=Language.JAVASCRIPT
        )
    
    def _parse_java_stack_trace(self, text: str) -> Optional[StackTrace]:
        """Parse Java stack trace"""
        patterns = self._java_patterns
        
        frames = []
        frame_matches = patterns["frame"].findall(text)
        
        for i, (method_info, file_name, line_num) in enumerate(frame_matches):
            try:
                line_number = int(line_num)
                
                # Extract class and method from method_info
                if "." in method_info:
                    parts = method_info.rsplit(".", 1)
                    class_name = parts[0]
                    method_name = parts[1] if len(parts) > 1 else method_info
                    function_name = f"{class_name}.{method_name}"
                else:
                    function_name = method_info
                
                # Construct file path
                file_path = file_name if file_name != "Unknown Source" else f"{class_name}.java"
                
                # Extract code snippet
                code_snippet = self._extract_code_snippet(text, file_path, line_number)
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(
                    file_path, function_name, i, len(frame_matches), Language.JAVA
                )
                
                frame = StackFrame(
                    file_path=file_path,
                    line_number=line_number,
                    function_name=function_name,
                    code_snippet=code_snippet,
                    relevance_score=relevance_score
                )
                frames.append(frame)
                
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse Java frame: {e}")
                continue
        
        # Extract error information (try both regular and "Caused by" patterns)
        error_type, error_message = self._extract_error_info(text, patterns["error_line"])
        
        if not error_type:
            error_type, error_message = self._extract_error_info(text, patterns["caused_by"])
        
        if not frames:
            return None
        
        return StackTrace(
            frames=frames,
            error_message=error_message,
            error_type=error_type,
            language=Language.JAVA
        )
    
    def _parse_generic_stack_trace(self, text: str) -> Optional[StackTrace]:
        """Generic stack trace parsing for unknown formats"""
        # Look for common patterns across languages
        generic_patterns = [
            re.compile(r"([^:\s]+):(\d+)"),  # file:line
            re.compile(r"at ([^(]+)\(([^:]+):(\d+)\)"),  # at function(file:line)
            re.compile(r'File "([^"]+)", line (\d+)'),  # File "path", line N
        ]
        
        frames = []
        
        for pattern in generic_patterns:
            matches = pattern.findall(text)
            
            for i, match in enumerate(matches):
                try:
                    if len(match) == 2:  # file:line pattern
                        file_path, line_num = match
                        function_name = "<unknown>"
                    elif len(match) == 3:  # function(file:line) pattern
                        function_name, file_path, line_num = match
                    else:
                        continue
                    
                    line_number = int(line_num)
                    
                    # Extract code snippet
                    code_snippet = self._extract_code_snippet(text, file_path, line_number)
                    
                    # Calculate basic relevance score
                    relevance_score = max(0.1, 1.0 - (i * 0.1))  # Decrease with position
                    
                    frame = StackFrame(
                        file_path=file_path,
                        line_number=line_number,
                        function_name=function_name,
                        code_snippet=code_snippet,
                        relevance_score=relevance_score
                    )
                    frames.append(frame)
                    
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse generic frame: {e}")
                    continue
        
        if not frames:
            return None
        
        # Extract basic error information
        error_lines = [line.strip() for line in text.split('\n') if 'error' in line.lower() or 'exception' in line.lower()]
        error_message = error_lines[0] if error_lines else "Unknown error"
        error_type = "UnknownError"
        
        return StackTrace(
            frames=frames,
            error_message=error_message,
            error_type=error_type,
            language=Language.UNKNOWN
        )
    
    def _extract_code_snippet(self, text: str, file_path: str, line_number: int) -> str:
        """Extract code snippet from stack trace text"""
        lines = text.split('\n')
        
        # Look for code lines near the file reference
        for i, line in enumerate(lines):
            if file_path in line and str(line_number) in line:
                # Check next few lines for code snippet
                for j in range(i + 1, min(i + 4, len(lines))):
                    if lines[j].strip() and not lines[j].strip().startswith('File') and not lines[j].strip().startswith('at'):
                        return lines[j].strip()
        
        return ""
    
    def _extract_error_info(self, text: str, pattern: re.Pattern) -> Tuple[str, str]:
        """Extract error type and message from text"""
        match = pattern.search(text)
        if match:
            error_type = match.group(1)
            error_message = match.group(2) if len(match.groups()) > 1 else ""
            return error_type, error_message
        
        return "UnknownError", "No error message found"
    
    def _calculate_relevance_score(self, file_path: str, function_name: str, 
                                 position: int, total_frames: int, language: Language) -> float:
        """
        Calculate relevance score for a stack frame
        
        Args:
            file_path: Path to the file
            function_name: Name of the function/method
            position: Position in the stack trace (0 = top)
            total_frames: Total number of frames
            language: Programming language
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        score = 1.0
        
        # Position-based scoring (earlier frames are more relevant)
        if total_frames > 1:
            position_penalty = position / (total_frames - 1) * 0.3
            score -= position_penalty
        
        # File path scoring
        if file_path:
            # Penalize system/library files
            system_indicators = [
                '/usr/', '/lib/', 'node_modules/', 'site-packages/',
                'java.lang.', 'java.util.', '__pycache__',
                'webpack://', 'chrome-extension://'
            ]
            
            for indicator in system_indicators:
                if indicator in file_path.lower():
                    score *= 0.5
                    break
            
            # Boost application files
            app_indicators = [
                '/src/', '/app/', '/components/', '/services/',
                'main.', 'index.', 'app.', 'server.'
            ]
            
            for indicator in app_indicators:
                if indicator in file_path.lower():
                    score *= 1.2
                    break
        
        # Function name scoring
        if function_name:
            # Penalize generic/system functions
            generic_functions = [
                '<anonymous>', '__init__', 'main', 'run',
                'execute', 'call', 'apply', 'invoke'
            ]
            
            if function_name.lower() in [f.lower() for f in generic_functions]:
                score *= 0.8
            
            # Boost error-related functions
            error_functions = [
                'error', 'exception', 'fail', 'throw',
                'assert', 'validate', 'check'
            ]
            
            if any(keyword in function_name.lower() for keyword in error_functions):
                score *= 1.3
        
        # Language-specific adjustments
        if language == Language.PYTHON:
            # Boost Django/Flask specific patterns
            if any(framework in file_path.lower() for framework in ['django', 'flask', 'fastapi']):
                score *= 1.1
        elif language == Language.JAVASCRIPT:
            # Boost React/Node specific patterns
            if any(framework in file_path.lower() for framework in ['react', 'node', 'express']):
                score *= 1.1
        elif language == Language.JAVA:
            # Boost Spring/application specific patterns
            if any(framework in file_path.lower() for framework in ['spring', 'com.example']):
                score *= 1.1
        
        # Ensure score is within bounds
        return max(0.0, min(1.0, score))


# Convenience function for easy usage
def parse_stack_trace(issue_body: str) -> Optional[StackTrace]:
    """
    Parse stack trace from issue body text
    
    Args:
        issue_body: Raw issue description text
        
    Returns:
        StackTrace object or None if no valid stack trace found
    """
    parser = StackTraceParser()
    return parser.parse_stack_trace(issue_body)