"""Configuration management for SenSIt"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()
        self._load_env_vars()
    
    def _find_config(self) -> str:
        """Find config.yml in project directory"""
        current_dir = Path(__file__).parent.parent
        config_file = current_dir / "config.yml"
        
        if config_file.exists():
            return str(config_file)
        
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path or not os.path.exists(self.config_path):
            return self._default_config()
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_env_vars(self):
        """Load sensitive data from environment variables"""
        # OpenAI API Key
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            if 'openai' not in self.config:
                self.config['openai'] = {}
            self.config['openai']['api_key'] = openai_key
        
        # Gemini API Key
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            if 'gemini' not in self.config:
                self.config['gemini'] = {}
            self.config['gemini']['api_key'] = gemini_key
        
        # Ollama Base URL (optional override)
        ollama_url = os.getenv('OLLAMA_BASE_URL')
        if ollama_url:
            if 'ollama' not in self.config:
                self.config['ollama'] = {}
            self.config['ollama']['base_url'] = ollama_url
        
        # AWS Credentials (for validation)
        aws_access = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
        if aws_access and aws_secret:
            if 'aws' not in self.config:
                self.config['aws'] = {}
            self.config['aws']['access_key'] = aws_access
            self.config['aws']['secret_key'] = aws_secret
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'openai': {
                'api_key': '',
                'model': 'gpt-4o-mini',
                'max_tokens': 500,
                'temperature': 0.3,
                'batch_size': 10
            },
            'scanning': {
                'max_depth': 3,
                'max_pages': 500,
                'rate_limit': 10,
                'timeout': 10,
                'user_agent': 'SenSIt/1.0 Security Scanner'
            },
            'extraction': {
                'min_entropy': 3.5,
                'min_length': 12,
                'context_lines': 5
            },
            'validation': {
                'enable_ai_validation': True,
                'enable_api_validation': True,
                'ai_confidence_threshold': 70
            },
            'output': {
                'format': 'cli',
                'verbose': True
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
