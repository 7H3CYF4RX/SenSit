"""Live API validation for secrets"""
import asyncio
from typing import List, Optional
from models.secret import Secret
from core.logger import logger
from core.config import Config


class APIValidator:
    """Orchestrates live API validation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.timeout = config.get('validation.api_timeout', 10)
        self.max_retries = config.get('validation.max_retries', 3)
    
    async def validate_secret(self, secret: Secret) -> Secret:
        """Validate a single secret"""
        validator_map = {
            'aws_access_key': self._validate_aws,
            'aws_secret_key': self._validate_aws,
            'stripe_secret_key': self._validate_stripe,
            'stripe_restricted_key': self._validate_stripe,
            'github_token': self._validate_github,
            'github_oauth': self._validate_github,
            'twilio_account_sid': self._validate_twilio,
            'twilio_auth_token': self._validate_twilio,
            'slack_webhook': self._validate_slack_webhook,
            'slack_token': self._validate_slack_token,
        }
        
        validator = validator_map.get(secret.type)
        
        if validator:
            try:
                is_valid, details = await validator(secret)
                secret.api_valid = is_valid
                secret.api_details = details
                
                if is_valid:
                    secret.status = "CONFIRMED"
                    secret.severity = "CRITICAL"
                    logger.info(f"✓ Confirmed valid {secret.type}")
                else:
                    logger.debug(f"✗ Invalid {secret.type}")
                    
            except Exception as e:
                logger.error(f"API validation error for {secret.type}: {e}")
                secret.api_valid = None
        
        return secret
    
    async def validate_batch(self, secrets: List[Secret]) -> List[Secret]:
        """Validate multiple secrets concurrently"""
        tasks = [self.validate_secret(secret) for secret in secrets]
        return await asyncio.gather(*tasks)
    
    async def _validate_aws(self, secret: Secret) -> tuple[bool, dict]:
        """Validate AWS credentials"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Extract access key and secret key
            # This is simplified - in production, you'd need to pair them
            if secret.type == 'aws_access_key':
                # Try to use STS GetCallerIdentity
                # Note: This requires both access key and secret key
                return False, {'error': 'Requires secret key pair'}
            
            return False, {'error': 'Not implemented'}
            
        except ImportError:
            return False, {'error': 'boto3 not installed'}
        except Exception as e:
            return False, {'error': str(e)}
    
    async def _validate_stripe(self, secret: Secret) -> tuple[bool, dict]:
        """Validate Stripe API key"""
        stripe = None
        try:
            import stripe
            
            stripe.api_key = secret.value
            
            # Try to retrieve balance
            balance = stripe.Balance.retrieve()
            
            return True, {
                'valid': True,
                'type': 'live' if 'live' in secret.value else 'test',
                'currency': balance.get('available', [{}])[0].get('currency', 'unknown')
            }
            
        except ImportError:
            return False, {'error': 'stripe not installed'}
        except Exception as e:
            if stripe and hasattr(stripe, 'error') and isinstance(e, stripe.error.AuthenticationError):
                return False, {'error': 'Invalid API key'}
            return False, {'error': str(e)}
    
    async def _validate_github(self, secret: Secret) -> tuple[bool, dict]:
        """Validate GitHub token"""
        try:
            import requests
            
            headers = {
                'Authorization': f'token {secret.value}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(
                'https://api.github.com/user',
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return True, {
                    'valid': True,
                    'username': user_data.get('login'),
                    'user_id': user_data.get('id'),
                    'scopes': response.headers.get('X-OAuth-Scopes', '')
                }
            else:
                return False, {'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    async def _validate_twilio(self, secret: Secret) -> tuple[bool, dict]:
        """Validate Twilio credentials"""
        try:
            from twilio.rest import Client
            
            # This is simplified - needs account SID + auth token pair
            return False, {'error': 'Requires SID and token pair'}
            
        except ImportError:
            return False, {'error': 'twilio not installed'}
        except Exception as e:
            return False, {'error': str(e)}
    
    async def _validate_slack_webhook(self, secret: Secret) -> tuple[bool, dict]:
        """Validate Slack webhook"""
        try:
            import requests
            
            # Send test message
            response = requests.post(
                secret.value,
                json={'text': 'SenSIt validation test (please ignore)'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return True, {'valid': True, 'type': 'webhook'}
            else:
                return False, {'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return False, {'error': str(e)}
    
    async def _validate_slack_token(self, secret: Secret) -> tuple[bool, dict]:
        """Validate Slack API token"""
        try:
            import requests
            
            headers = {'Authorization': f'Bearer {secret.value}'}
            
            response = requests.get(
                'https://slack.com/api/auth.test',
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return True, {
                        'valid': True,
                        'team': data.get('team'),
                        'user': data.get('user')
                    }
            
            return False, {'error': 'Invalid token'}
            
        except Exception as e:
            return False, {'error': str(e)}
