"""Data models for secrets"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Secret:
    """Represents a detected secret"""
    
    # Basic info
    type: str
    value: str
    location: str
    line_number: int = 0
    
    # Context
    context: str = ""
    file_type: str = ""
    
    # Analysis scores
    entropy: float = 0.0
    regex_match: bool = False
    
    # Validation results
    ai_confidence: float = 0.0
    ai_reasoning: str = ""
    api_valid: Optional[bool] = None
    api_details: Dict[str, Any] = field(default_factory=dict)
    
    # Classification
    severity: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    status: str = "UNVERIFIED"  # CONFIRMED, LIKELY, POSSIBLE, UNVERIFIED
    
    # Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'type': self.type,
            'value': self.value[:20] + '...' if len(self.value) > 20 else self.value,
            'location': self.location,
            'line_number': self.line_number,
            'context': self.context,
            'entropy': round(self.entropy, 2),
            'ai_confidence': round(self.ai_confidence, 2),
            'ai_reasoning': self.ai_reasoning,
            'api_valid': self.api_valid,
            'api_details': self.api_details,
            'severity': self.severity,
            'status': self.status,
            'discovered_at': self.discovered_at.isoformat()
        }
    
    def get_score(self) -> float:
        """Calculate overall confidence score"""
        score = 0.0
        
        # Regex match: +20
        if self.regex_match:
            score += 20
        
        # High entropy: +15
        if self.entropy > 4.0:
            score += 15
        elif self.entropy > 3.5:
            score += 10
        
        # AI confidence: +0-40
        score += (self.ai_confidence / 100) * 40
        
        # API validation: +25
        if self.api_valid:
            score += 25
        
        return min(score, 100)


@dataclass
class Finding:
    """Represents a scan finding"""
    
    target: str
    secrets: list[Secret] = field(default_factory=list)
    total_files_scanned: int = 0
    total_secrets_found: int = 0
    scan_duration: float = 0.0
    scan_timestamp: datetime = field(default_factory=datetime.now)
    
    def add_secret(self, secret: Secret):
        """Add a secret to findings"""
        self.secrets.append(secret)
        self.total_secrets_found += 1
    
    def get_critical_secrets(self) -> list[Secret]:
        """Get all critical severity secrets"""
        return [s for s in self.secrets if s.severity == "CRITICAL"]
    
    def get_confirmed_secrets(self) -> list[Secret]:
        """Get all confirmed secrets"""
        return [s for s in self.secrets if s.status == "CONFIRMED"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'target': self.target,
            'total_files_scanned': self.total_files_scanned,
            'total_secrets_found': self.total_secrets_found,
            'scan_duration': round(self.scan_duration, 2),
            'scan_timestamp': self.scan_timestamp.isoformat(),
            'secrets': [s.to_dict() for s in self.secrets]
        }
