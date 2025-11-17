"""Main scanner orchestrator"""
import asyncio
import time
from typing import List
from pathlib import Path
from models.secret import Secret, Finding
from extraction.pattern_matcher import PatternMatcher
from extraction.entropy_analyzer import EntropyAnalyzer
from validation.ai_validator import AIValidator
from validation.api_validator import APIValidator
from discovery.web_crawler import WebCrawler
from core.config import Config
from core.logger import logger


class SecretsScanner:
    """Main secrets scanner orchestrator"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
        # Initialize modules
        self.pattern_matcher = PatternMatcher()
        self.entropy_analyzer = EntropyAnalyzer(
            min_entropy=self.config.get('extraction.min_entropy', 3.5),
            min_length=self.config.get('extraction.min_length', 12)
        )
        self.ai_validator = AIValidator(self.config)
        self.api_validator = APIValidator(self.config)
        self.web_crawler = WebCrawler(self.config)
        
        # Settings
        self.enable_ai = self.config.get('validation.enable_ai_validation', True)
        self.enable_api = self.config.get('validation.enable_api_validation', True)
        self.ai_threshold = self.config.get('validation.ai_confidence_threshold', 70)
    
    async def scan_url(self, url: str) -> Finding:
        """Scan a URL for secrets (with crawling)"""
        logger.info(f"Starting scan of: {url}")
        start_time = time.time()
        
        finding = Finding(target=url)
        all_secrets = []
        
        try:
            # Crawl website
            pages_content = await self.web_crawler.crawl(url)
            
            logger.info(f"Crawled {len(pages_content)} pages, extracting secrets...")
            
            # Extract secrets from all pages
            for page_url, content in pages_content.items():
                secrets = await self._extract_secrets(content, page_url)
                all_secrets.extend(secrets)
            
            logger.info(f"Extracted {len(all_secrets)} potential secrets")
            
            # Validate secrets
            validated_secrets = await self._validate_secrets(all_secrets)
            
            # Add to finding
            for secret in validated_secrets:
                finding.add_secret(secret)
            
            finding.total_files_scanned = len(pages_content)
            finding.scan_duration = time.time() - start_time
            
            logger.info(f"Scan complete. Found {len(validated_secrets)} potential secrets.")
            
        except Exception as e:
            logger.error(f"Error scanning URL: {e}")
        
        return finding
    
    async def scan_file(self, file_path: str) -> Finding:
        """Scan a single file for secrets"""
        logger.info(f"Scanning file: {file_path}")
        start_time = time.time()
        
        finding = Finding(target=file_path)
        
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract secrets
            secrets = await self._extract_secrets(content, file_path)
            
            # Validate secrets
            validated_secrets = await self._validate_secrets(secrets)
            
            # Add to finding
            for secret in validated_secrets:
                finding.add_secret(secret)
            
            finding.total_files_scanned = 1
            finding.scan_duration = time.time() - start_time
            
            logger.info(f"Found {len(validated_secrets)} potential secrets in file.")
            
        except Exception as e:
            logger.error(f"Error scanning file: {e}")
        
        return finding
    
    async def scan_directory(self, dir_path: str) -> Finding:
        """Scan a directory recursively for secrets"""
        logger.info(f"Scanning directory: {dir_path}")
        start_time = time.time()
        
        finding = Finding(target=dir_path)
        
        try:
            path = Path(dir_path)
            files = []
            
            # Collect all files
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    # Skip binary files and common excludes
                    if self._should_scan_file(file_path):
                        files.append(file_path)
            
            logger.info(f"Found {len(files)} files to scan")
            
            # Scan each file
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Extract secrets
                    secrets = await self._extract_secrets(content, str(file_path))
                    
                    # Add to finding
                    for secret in secrets:
                        finding.add_secret(secret)
                    
                    finding.total_files_scanned += 1
                    
                except Exception as e:
                    logger.debug(f"Error scanning {file_path}: {e}")
            
            # Validate all secrets
            if finding.secrets:
                logger.info(f"Validating {len(finding.secrets)} potential secrets...")
                finding.secrets = await self._validate_secrets(finding.secrets)
            
            finding.scan_duration = time.time() - start_time
            
            logger.info(f"Directory scan complete. Found {len(finding.secrets)} potential secrets.")
            
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
        
        return finding
    
    async def _extract_secrets(self, content: str, location: str) -> List[Secret]:
        """Extract secrets from content"""
        secrets = []
        
        # Pattern matching
        pattern_matches = self.pattern_matcher.find_matches(content, location)
        secrets.extend(pattern_matches)
        
        # Entropy analysis
        entropy_matches = self.entropy_analyzer.find_high_entropy_strings(content, location)
        secrets.extend(entropy_matches)
        
        # Calculate entropy for all secrets
        for secret in secrets:
            if secret.entropy == 0:
                secret = self.entropy_analyzer.analyze_secret(secret)
        
        # Deduplicate
        secrets = self._deduplicate_secrets(secrets)
        
        return secrets
    
    async def _validate_secrets(self, secrets: List[Secret]) -> List[Secret]:
        """Validate secrets using AI and API"""
        if not secrets:
            return []
        
        # AI Validation
        if self.enable_ai and self.ai_validator.client:
            logger.info(f"Running AI validation on {len(secrets)} secrets...")
            secrets = self.ai_validator.validate_batch(secrets)
            
            # Filter by AI confidence threshold
            high_confidence = [s for s in secrets if s.ai_confidence >= self.ai_threshold]
            logger.info(f"AI validation: {len(high_confidence)} high-confidence matches")
        else:
            high_confidence = secrets
        
        # API Validation
        if self.enable_api and high_confidence:
            logger.info(f"Running live API validation on {len(high_confidence)} secrets...")
            high_confidence = await self.api_validator.validate_batch(high_confidence)
            
            confirmed = [s for s in high_confidence if s.api_valid]
            logger.info(f"API validation: {len(confirmed)} confirmed active secrets")
        
        return secrets
    
    def _deduplicate_secrets(self, secrets: List[Secret]) -> List[Secret]:
        """Remove duplicate secrets"""
        seen = set()
        unique = []
        
        for secret in secrets:
            key = (secret.type, secret.value, secret.location)
            if key not in seen:
                seen.add(key)
                unique.append(secret)
        
        return unique
    
    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if file should be scanned"""
        # Skip common binary and large files
        skip_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip',
            '.tar', '.gz', '.exe', '.dll', '.so', '.dylib',
            '.mp4', '.mp3', '.avi', '.mov', '.wav'
        }
        
        if file_path.suffix.lower() in skip_extensions:
            return False
        
        # Skip common directories
        skip_dirs = {
            'node_modules', '.git', '__pycache__', 'venv',
            'env', '.venv', 'dist', 'build', '.next'
        }
        
        if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
            return False
        
        # Check file size (skip files > 10MB)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:
                return False
        except:
            return False
        
        return True
