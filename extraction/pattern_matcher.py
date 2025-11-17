"""Pattern matching engine for secret detection"""
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any
from models.secret import Secret
from core.logger import logger


class PatternMatcher:
    """Regex-based pattern matcher"""
    
    def __init__(self, patterns_file: str = None):
        self.patterns_file = patterns_file or self._find_patterns_file()
        self.patterns = self._load_patterns()
    
    def _find_patterns_file(self) -> str:
        """Find patterns.yml file"""
        current_dir = Path(__file__).parent.parent
        patterns_file = current_dir / "signatures" / "patterns.yml"
        return str(patterns_file)
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load patterns from YAML file"""
        try:
            with open(self.patterns_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            return {}
    
    def find_matches(self, content: str, location: str = "", file_type: str = "") -> List[Secret]:
        """Find all pattern matches in content"""
        secrets = []
        lines = content.split('\n')
        
        for pattern_name, pattern_config in self.patterns.items():
            pattern = pattern_config.get('pattern')
            if not pattern:
                continue
            
            try:
                # Compile regex
                regex = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                
                # Find matches
                for match in regex.finditer(content):
                    matched_value = match.group(0)
                    
                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Extract context
                    context = self._extract_context(lines, line_num, context_lines=5)
                    
                    # Check context keywords if specified
                    if 'context_keywords' in pattern_config:
                        if not self._check_context_keywords(context, pattern_config['context_keywords']):
                            continue
                    
                    # Create secret object
                    secret = Secret(
                        type=pattern_name,
                        value=matched_value,
                        location=location,
                        line_number=line_num,
                        context=context,
                        file_type=file_type,
                        regex_match=True,
                        severity=pattern_config.get('severity', 'MEDIUM')
                    )
                    
                    secrets.append(secret)
                    
            except re.error as e:
                logger.error(f"Invalid regex pattern for {pattern_name}: {e}")
        
        return secrets
    
    def _extract_context(self, lines: List[str], line_num: int, context_lines: int = 5) -> str:
        """Extract surrounding context"""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        context_lines_list = lines[start:end]
        return '\n'.join(context_lines_list)
    
    def _check_context_keywords(self, context: str, keywords: List[str]) -> bool:
        """Check if context contains required keywords"""
        context_lower = context.lower()
        return any(keyword.lower() in context_lower for keyword in keywords)
    
    def get_pattern_info(self, pattern_name: str) -> Dict[str, Any]:
        """Get information about a specific pattern"""
        return self.patterns.get(pattern_name, {})
