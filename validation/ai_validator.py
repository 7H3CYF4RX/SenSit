"""AI-powered validation using multiple providers (OpenAI, Gemini, Ollama)"""
import json
from typing import List, Optional
from tqdm import tqdm
from models.secret import Secret
from core.logger import logger
from core.config import Config


class AIValidator:
    """Multi-provider AI secret validator (OpenAI, Gemini, Ollama)"""
    
    def __init__(self, config: Config):
        self.config = config
        self.provider = config.get('ai_provider', 'openai').lower()
        
        # Initialize the appropriate provider
        if self.provider == 'openai':
            self.client = self._init_openai()
        elif self.provider == 'gemini':
            self.client = self._init_gemini()
        elif self.provider == 'ollama':
            self.client = self._init_ollama()
        else:
            logger.error(f"Unknown AI provider: {self.provider}")
            self.client = None
        
        if not self.client:
            logger.warning(f"AI validation disabled. Provider: {self.provider}")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            api_key = self.config.get('openai.api_key')
            if not api_key:
                logger.warning("OpenAI API key not configured")
                return None
            
            self.model = self.config.get('openai.model', 'gpt-4o-mini')
            self.max_tokens = self.config.get('openai.max_tokens', 500)
            self.temperature = self.config.get('openai.temperature', 0.3)
            self.batch_size = self.config.get('openai.batch_size', 10)
            
            logger.info(f"Initialized OpenAI with model: {self.model}")
            return OpenAI(api_key=api_key)
        except ImportError:
            logger.error("OpenAI library not installed. Run: pip install openai")
            return None
        except Exception as e:
            logger.error(f"Error initializing OpenAI: {e}")
            return None
    
    def _init_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            api_key = self.config.get('gemini.api_key')
            if not api_key:
                logger.warning("Gemini API key not configured")
                return None
            
            self.model = self.config.get('gemini.model', 'gemini-pro')
            self.max_tokens = self.config.get('gemini.max_tokens', 500)
            self.temperature = self.config.get('gemini.temperature', 0.3)
            self.batch_size = self.config.get('gemini.batch_size', 10)
            
            genai.configure(api_key=api_key)
            logger.info(f"Initialized Gemini with model: {self.model}")
            return genai.GenerativeModel(self.model)
        except ImportError:
            logger.error("Gemini library not installed. Run: pip install google-generativeai")
            return None
        except Exception as e:
            logger.error(f"Error initializing Gemini: {e}")
            return None
    
    def _init_ollama(self):
        """Initialize Ollama client (local)"""
        try:
            import ollama
            self.base_url = self.config.get('ollama.base_url', 'http://localhost:11434')
            self.model = self.config.get('ollama.model', 'llama2')
            self.max_tokens = self.config.get('ollama.max_tokens', 500)
            self.temperature = self.config.get('ollama.temperature', 0.3)
            self.batch_size = self.config.get('ollama.batch_size', 5)
            
            # Test connection
            try:
                ollama.list()
                logger.info(f"Initialized Ollama with model: {self.model}")
                return ollama
            except:
                logger.warning(f"Ollama not running at {self.base_url}. Start with: ollama serve")
                return None
        except ImportError:
            logger.error("Ollama library not installed. Run: pip install ollama")
            return None
        except Exception as e:
            logger.error(f"Error initializing Ollama: {e}")
            return None
    
    def validate_secret(self, secret: Secret) -> Secret:
        """Validate a single secret using AI"""
        if not self.client:
            return secret
        
        try:
            prompt = self._create_prompt(secret)
            
            # Call appropriate provider
            if self.provider == 'openai':
                result = self._call_openai(prompt)
            elif self.provider == 'gemini':
                result = self._call_gemini(prompt)
            elif self.provider == 'ollama':
                result = self._call_ollama(prompt)
            else:
                return secret
            
            if result:
                # Update secret with AI analysis
                secret.ai_confidence = result.get('confidence', 0)
                secret.ai_reasoning = result.get('reasoning', '')
                
                # Adjust severity based on AI confidence
                if secret.ai_confidence < 30:
                    secret.status = "UNVERIFIED"
                elif secret.ai_confidence < 60:
                    secret.status = "POSSIBLE"
                elif secret.ai_confidence < 85:
                    secret.status = "LIKELY"
                else:
                    secret.status = "CONFIRMED"
                
                logger.debug(f"AI validation for {secret.type}: {secret.ai_confidence}% confidence")
            
        except Exception as e:
            logger.error(f"AI validation error: {e}")
        
        return secret
    
    def validate_batch(self, secrets: List[Secret]) -> List[Secret]:
        """Validate multiple secrets in batches"""
        if not self.client:
            return secrets
        
        validated = []
        total_batches = (len(secrets) + self.batch_size - 1) // self.batch_size
        
        # Create progress bar
        with tqdm(total=len(secrets), desc=f"AI Validation ({self.provider})", 
                  unit="secret", ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            
            # Process in batches
            for i in range(0, len(secrets), self.batch_size):
                batch = secrets[i:i + self.batch_size]
                
                try:
                    # Create batch prompt
                    prompt = self._create_batch_prompt(batch)
                    
                    # Call appropriate provider
                    if self.provider == 'openai':
                        result = self._call_openai_batch(prompt, len(batch))
                    elif self.provider == 'gemini':
                        result = self._call_gemini_batch(prompt)
                    elif self.provider == 'ollama':
                        result = self._call_ollama_batch(prompt)
                    else:
                        validated.extend(batch)
                        pbar.update(len(batch))
                        continue
                    
                    if result:
                        results = result.get('secrets', [])
                        
                        # Update secrets with AI analysis
                        for j, secret in enumerate(batch):
                            if j < len(results):
                                ai_result = results[j]
                                secret.ai_confidence = ai_result.get('confidence', 0)
                                secret.ai_reasoning = ai_result.get('reasoning', '')
                                
                                # Update status
                                if secret.ai_confidence < 30:
                                    secret.status = "UNVERIFIED"
                                elif secret.ai_confidence < 60:
                                    secret.status = "POSSIBLE"
                                elif secret.ai_confidence < 85:
                                    secret.status = "LIKELY"
                                else:
                                    secret.status = "CONFIRMED"
                            
                            validated.append(secret)
                    else:
                        validated.extend(batch)
                    
                    # Update progress bar
                    pbar.update(len(batch))
                    
                except Exception as e:
                    logger.error(f"Batch AI validation error: {e}")
                    validated.extend(batch)
                    pbar.update(len(batch))
        
        logger.info(f"AI validation complete: {len(validated)} secrets processed")
        return validated
    
    def _create_prompt(self, secret: Secret) -> str:
        """Create validation prompt for a single secret"""
        prompt = f"""Analyze this potential secret and determine if it's a real credential or a false positive.

Secret Type: {secret.type}
Value: {secret.value[:50]}...
Entropy: {secret.entropy:.2f}
Location: {secret.location}

Context (surrounding code):
```
{secret.context[:500]}
```

Determine:
1. Is this a real secret or a test/example/placeholder?
2. Confidence level (0-100)
3. Brief reasoning

IMPORTANT: Respond ONLY with valid JSON in this exact format:
{{
    "is_valid": true,
    "confidence": 85,
    "reasoning": "brief explanation"
}}

Do not include any other text, only the JSON object.
"""
        return prompt
    
    def _create_batch_prompt(self, secrets: List[Secret]) -> str:
        """Create validation prompt for multiple secrets"""
        secrets_data = []
        
        for i, secret in enumerate(secrets):
            secrets_data.append({
                'id': i,
                'type': secret.type,
                'value': secret.value[:50] + '...' if len(secret.value) > 50 else secret.value,
                'entropy': round(secret.entropy, 2),
                'context': secret.context[:200]
            })
        
        prompt = f"""Analyze these {len(secrets)} potential secrets and determine which are real credentials vs false positives.

Secrets to analyze:
{json.dumps(secrets_data, indent=2)}

For each secret, determine:
1. Is it a real secret or test/example/placeholder?
2. Confidence level (0-100)
3. Brief reasoning

IMPORTANT: Respond ONLY with valid JSON in this exact format:
{{
    "secrets": [
        {{
            "id": 0,
            "is_valid": true,
            "confidence": 85,
            "reasoning": "brief explanation"
        }}
    ]
}}

Do not include any other text, only the JSON object.
"""
        return prompt
    
    def _call_openai(self, prompt: str) -> Optional[dict]:
        """Call OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security expert analyzing potential secrets. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    def _call_openai_batch(self, prompt: str, batch_size: int) -> Optional[dict]:
        """Call OpenAI API for batch"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security expert analyzing potential secrets. Respond only with valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens * batch_size,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI batch API error: {e}")
            return None
    
    def _call_gemini(self, prompt: str) -> Optional[dict]:
        """Call Google Gemini API"""
        try:
            response = self.client.generate_content(
                prompt,
                generation_config={
                    'temperature': self.temperature,
                    'max_output_tokens': self.max_tokens,
                }
            )
            # Parse JSON from response
            text = response.text
            # Extract JSON from markdown code blocks if present
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
    
    def _call_gemini_batch(self, prompt: str) -> Optional[dict]:
        """Call Google Gemini API for batch"""
        try:
            response = self.client.generate_content(
                prompt,
                generation_config={
                    'temperature': self.temperature,
                    'max_output_tokens': self.max_tokens * 2,
                }
            )
            text = response.text
            # Extract JSON from markdown code blocks if present
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini batch API error: {e}")
            return None
    
    def _call_ollama(self, prompt: str) -> Optional[dict]:
        """Call Ollama API (local)"""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,
                }
            )
            text = response['response']
            return self._extract_json(text)
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return None
    
    def _call_ollama_batch(self, prompt: str) -> Optional[dict]:
        """Call Ollama API for batch (local)"""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens * 2,
                }
            )
            text = response['response']
            return self._extract_json(text)
        except Exception as e:
            logger.error(f"Ollama batch API error: {e}")
            return None
    
    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from text response (handles markdown, plain text, etc.)"""
        try:
            # Try direct JSON parse first
            return json.loads(text)
        except:
            pass
        
        try:
            # Extract from markdown code blocks
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            return json.loads(text)
        except:
            pass
        
        try:
            # Find JSON object in text
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except:
            pass
        
        logger.debug(f"Could not extract JSON from response: {text[:200]}")
        return None
