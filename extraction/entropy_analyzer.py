"""Shannon entropy analyzer for detecting high-entropy secrets"""
import re
import math
from typing import List
from models.secret import Secret
from core.logger import logger


class EntropyAnalyzer:
    """Analyzes entropy to detect potential secrets"""
    
    def __init__(self, min_entropy: float = 3.5, min_length: int = 12):
        self.min_entropy = min_entropy
        self.min_length = min_length
    
    def calculate_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not data:
            return 0.0
        
        # Count character frequencies
        frequencies = {}
        for char in data:
            frequencies[char] = frequencies.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        data_len = len(data)
        
        for count in frequencies.values():
            probability = count / data_len
            entropy -= probability * math.log2(probability)
        
        return entropy
    
    def find_high_entropy_strings(self, content: str, location: str = "") -> List[Secret]:
        """Find high-entropy strings that might be secrets"""
        secrets = []
        lines = content.split('\n')
        
        # Patterns to extract potential secrets
        patterns = [
            # Quoted strings
            r'["\']([A-Za-z0-9+/=_-]{12,})["\']',
            # Assignment values
            r'=\s*([A-Za-z0-9+/=_-]{12,})',
            # Environment variables
            r'export\s+\w+=([A-Za-z0-9+/=_-]{12,})',
            # JSON values
            r':\s*["\']([A-Za-z0-9+/=_-]{12,})["\']',
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                matches = re.finditer(pattern, line)
                
                for match in matches:
                    value = match.group(1) if match.lastindex else match.group(0)
                    
                    # Skip if too short
                    if len(value) < self.min_length:
                        continue
                    
                    # Calculate entropy
                    entropy = self.calculate_entropy(value)
                    
                    # Check if entropy is high enough
                    if entropy >= self.min_entropy:
                        # Extract context
                        context = self._extract_context(lines, line_num)
                        
                        secret = Secret(
                            type="high_entropy_string",
                            value=value,
                            location=location,
                            line_number=line_num,
                            context=context,
                            entropy=entropy,
                            regex_match=False,
                            severity="MEDIUM"
                        )
                        
                        secrets.append(secret)
        
        return secrets
    
    def _extract_context(self, lines: List[str], line_num: int, context_lines: int = 3) -> str:
        """Extract surrounding context"""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        context_lines_list = lines[start:end]
        return '\n'.join(context_lines_list)
    
    def analyze_secret(self, secret: Secret) -> Secret:
        """Analyze entropy of an existing secret"""
        secret.entropy = self.calculate_entropy(secret.value)
        return secret
    
    def is_base64(self, data: str) -> bool:
        """Check if string is likely base64 encoded"""
        # Base64 pattern
        base64_pattern = r'^[A-Za-z0-9+/]*={0,2}$'
        
        if not re.match(base64_pattern, data):
            return False
        
        # Check length (base64 is always multiple of 4)
        if len(data) % 4 != 0:
            return False
        
        # Check entropy (base64 typically has high entropy)
        entropy = self.calculate_entropy(data)
        return entropy > 4.0
