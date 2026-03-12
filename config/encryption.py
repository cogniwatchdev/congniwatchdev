"""
CogniWatch - Encryption Module
Secure encryption for configuration secrets, credential storage, and sensitive data.
Supports AES-256-GCM encryption and environment variable injection.
"""

import os
import json
import base64
import hashlib
import secrets
import hmac
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime, timezone
import logging

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    AESGCM = None
    logger = logging.getLogger(__name__)
    logger.warning("Cryptography library not installed. Encryption disabled.")

logger = logging.getLogger(__name__)

# Constants
SALT_SIZE = 16
NONCE_SIZE = 12  # 96 bits for GCM
TAG_SIZE = 16
KEY_SIZE = 32  # 256 bits
ITERATIONS = 100000


class SecretsManager:
    """
    Secure secrets management for CogniWatch.
    Handles encryption/decryption of configuration values and credentials.
    """
    
    def __init__(self, master_key: Optional[str] = None, config_path: Optional[Path] = None):
        """
        Initialize secrets manager.
        
        Args:
            master_key: Master encryption key (from environment or file).
                       If None, will try to load from COGNIWATCH_MASTER_KEY env var.
            config_path: Path to encrypted config file
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("Cryptography library required for encryption")
        
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'secrets.enc.json'
        
        # Get or generate master key
        if master_key:
            self.master_key = master_key
        else:
            self.master_key = os.environ.get('COGNIWATCH_MASTER_KEY')
        
        if not self.master_key:
            logger.warning("No master key provided. Secrets will be stored in plaintext.")
            self.master_key = None
        else:
            self.master_key = self._derive_key(self.master_key)
            logger.info("Secrets manager initialized with encryption")
        
        # Cache for decrypted secrets
        self._cache: Dict[str, Any] = {}
        
        # Load encrypted config if exists
        if self.config_path.exists() and self.master_key:
            self._load_secrets()
    
    def _derive_key(self, password: str) -> bytes:
        """Derive a 256-bit key from a password using PBKDF2"""
        # We'll use a fixed salt for the master key derivation
        # In production, store salt separately
        salt = b'cogniwatch_salt_v1'  # 16 bytes
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=ITERATIONS,
            backend=default_backend()
        )
        
        return kdf.derive(password.encode())
    
    def _encrypt(self, plaintext: bytes) -> str:
        """Encrypt data using AES-256-GCM"""
        if not self.master_key:
            return base64.b64encode(plaintext).decode()
        
        aesgcm = AESGCM(self.master_key)
        nonce = os.urandom(NONCE_SIZE)
        
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # Combine nonce + ciphertext + tag
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode()
    
    def _decrypt(self, encoded_data: str) -> bytes:
        """Decrypt data using AES-256-GCM"""
        if not self.master_key:
            return base64.b64decode(encoded_data)
        
        try:
            encrypted_data = base64.b64decode(encoded_data)
            
            # Extract nonce and ciphertext+tag
            nonce = encrypted_data[:NONCE_SIZE]
            ciphertext_with_tag = encrypted_data[NONCE_SIZE:]
            
            aesgcm = AESGCM(self.master_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
            
            return plaintext
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt data. Wrong key or corrupted data.")
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a single value"""
        return self._encrypt(value.encode())
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a single value"""
        return self._decrypt(encrypted_value).decode()
    
    def _load_secrets(self):
        """Load encrypted secrets from file"""
        try:
            with open(self.config_path) as f:
                encrypted_config = json.load(f)
            
            # Decrypt all secret values
            for key, value in encrypted_config.items():
                if value.startswith('enc:'):
                    self._cache[key] = self.decrypt_value(value[4:])  # Remove 'enc:' prefix
                else:
                    self._cache[key] = value
            
            logger.info(f"Loaded {len(self._cache)} secrets from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            self._cache = {}
    
    def _save_secrets(self):
        """Save secrets to encrypted file"""
        if not self.master_key:
            logger.warning("Cannot save encrypted secrets without master key")
            return
        
        try:
            encrypted_config = {}
            for key, value in self._cache.items():
                if isinstance(value, str) and not value.startswith('enc:'):
                    encrypted_config[key] = 'enc:' + self.encrypt_value(value)
                else:
                    encrypted_config[key] = value
            
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(encrypted_config, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.config_path, 0o600)
            
            logger.info(f"Saved {len(self._cache)} secrets to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")
    
    def set_secret(self, key: str, value: str):
        """Store a secret"""
        self._cache[key] = value
        self._save_secrets()
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a secret"""
        # Check environment variable first (highest priority)
        env_value = os.environ.get(f'COGNIWATCH_{key.upper()}')
        if env_value:
            return env_value
        
        # Check cache
        return self._cache.get(key, default)
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        if key in self._cache:
            del self._cache[key]
            self._save_secrets()
            return True
        return False
    
    def list_secrets(self) -> list:
        """List all secret keys (not values)"""
        return list(self._cache.keys())
    
    def rotate_master_key(self, old_key: str, new_key: str) -> bool:
        """
        Rotate the master encryption key.
        Re-encrypts all secrets with the new key.
        """
        try:
            # Temporarily use old key to decrypt
            old_derived = self._derive_key(old_key)
            old_aesgcm = AESGCM(old_derived)
            
            # Load encrypted file directly
            with open(self.config_path) as f:
                encrypted_config = json.load(f)
            
            # Decrypt all with old key
            decrypted_values = {}
            for key, value in encrypted_config.items():
                if value.startswith('enc:'):
                    encrypted_data = base64.b64decode(value[4:])
                    nonce = encrypted_data[:NONCE_SIZE]
                    ciphertext = encrypted_data[NONCE_SIZE:]
                    plaintext = old_aesgcm.decrypt(nonce, ciphertext, None)
                    decrypted_values[key] = plaintext.decode()
                else:
                    decrypted_values[key] = value
            
            # Now use new key
            self.master_key = self._derive_key(new_key)
            self._cache = {}
            
            # Re-encrypt with new key
            for key, value in decrypted_values.items():
                self.set_secret(key, value)
            
            logger.info("Master key rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate master key: {e}")
            return False


class CredentialStore:
    """
    Secure credential storage with encryption and rotation support.
    """
    
    def __init__(self, secrets_manager: SecretsManager):
        self.secrets = secrets_manager
        self.credentials_path = Path(__file__).parent.parent / 'config' / 'credentials.enc.json'
        self._credentials: Dict[str, Dict[str, Any]] = {}
        self._load_credentials()
    
    def _load_credentials(self):
        """Load encrypted credentials"""
        if self.credentials_path.exists():
            try:
                with open(self.credentials_path) as f:
                    encrypted_creds = json.load(f)
                
                for cred_id, cred_data in encrypted_creds.items():
                    # Decrypt sensitive fields
                    decrypted = {}
                    for key, value in cred_data.items():
                        if key in ['password', 'token', 'secret', 'api_key']:
                            try:
                                decrypted[key] = self.secrets.decrypt_value(value[4:])
                            except Exception:
                                logger.warning(f"Failed to decrypt {key} for {cred_id}")
                                decrypted[key] = None
                        else:
                            decrypted[key] = value
                    
                    self._credentials[cred_id] = decrypted
                
                logger.info(f"Loaded {len(self._credentials)} credentials")
            except Exception as e:
                logger.error(f"Failed to load credentials: {e}")
                self._credentials = {}
    
    def _save_credentials(self):
        """Save credentials with encryption"""
        try:
            encrypted_creds = {}
            for cred_id, cred_data in self._credentials.items():
                encrypted_data = {}
                for key, value in cred_data.items():
                    if key in ['password', 'token', 'secret', 'api_key']:
                        encrypted_data[key] = 'enc:' + self.secrets.encrypt_value(value)
                    else:
                        encrypted_data[key] = value
                encrypted_creds[cred_id] = encrypted_data
            
            with open(self.credentials_path, 'w') as f:
                json.dump(encrypted_creds, f, indent=2)
            
            os.chmod(self.credentials_path, 0o600)
            logger.info(f"Saved {len(self._credentials)} credentials")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    def store_credential(self, cred_id: str, credential_type: str, **kwargs):
        """
        Store a credential.
        
        Args:
            cred_id: Unique identifier for this credential
            credential_type: Type (e.g., 'api_token', 'database', 'oauth')
            **kwargs: Credential fields (password, token, api_key, etc.)
        """
        self._credentials[cred_id] = {
            'type': credential_type,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            **kwargs
        }
        self._save_credentials()
    
    def get_credential(self, cred_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a credential"""
        return self._credentials.get(cred_id)
    
    def delete_credential(self, cred_id: str) -> bool:
        """Delete a credential"""
        if cred_id in self._credentials:
            del self._credentials[cred_id]
            self._save_credentials()
            return True
        return False
    
    def update_credential(self, cred_id: str, **kwargs):
        """Update credential fields"""
        if cred_id in self._credentials:
            self._credentials[cred_id].update(kwargs)
            self._credentials[cred_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
            self._save_credentials()
            return True
        return False
    
    def rotate_credential(self, cred_id: str, new_value: str, field: str = 'password'):
        """
        Rotate a credential value.
        Keeps audit trail of rotation.
        """
        if cred_id not in self._credentials:
            return False
        
        old_value = self._credentials[cred_id].get(field, '')
        
        # Update with new value
        self._credentials[cred_id][field] = new_value
        self._credentials[cred_id]['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Track rotation (encrypted)
        if 'rotation_history' not in self._credentials[cred_id]:
            self._credentials[cred_id]['rotation_history'] = []
        
        self._credentials[cred_id]['rotation_history'].append({
            'rotated_at': datetime.now(timezone.utc).isoformat(),
            'field': field,
        })
        
        # Keep only last 5 rotations
        self._credentials[cred_id]['rotation_history'] = \
            self._credentials[cred_id]['rotation_history'][-5:]
        
        self._save_credentials()
        return True
    
    def list_credentials(self) -> list:
        """List all credential IDs and types"""
        return [
            {'id': cred_id, 'type': data['type'], 'updated_at': data['updated_at']}
            for cred_id, data in self._credentials.items()
        ]


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Returns bcrypt hash string.
    """
    try:
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    except ImportError:
        # Fallback to hashlib (not recommended for production)
        import hashlib
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"pbkdf2:{salt}:{hashed.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against a hash.
    Supports bcrypt and pbkdf2 formats.
    """
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ImportError:
        # Handle pbkdf2 format
        if hashed.startswith('pbkdf2:'):
            parts = hashed.split(':')
            if len(parts) == 3:
                _, salt, stored_hash = parts
                import hashlib
                computed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
                return hmac.compare_digest(computed.hex(), stored_hash)
        return False


# Convenience function to migrate config
def migrate_config_to_encrypted(config_path: Union[str, Path], secrets_manager: SecretsManager):
    """
    Migrate plaintext config to encrypted format.
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return False
    
    try:
        # Load plaintext config
        with open(config_path) as f:
            config = json.load(f)
        
        # Extract sensitive fields
        sensitive_paths = [
            ['openclaw_gateway', 'token'],
            ['alerts', 'discord_webhook_url'],
            ['alerts', 'email_smtp_server'],
        ]
        
        for path in sensitive_paths:
            value = config
            try:
                for key in path[:-1]:
                    value = value[key]
                secret_key = path[-1]
                secret_value = value.get(secret_key)
                
                if secret_value and not secret_value.startswith('YOUR_'):
                    # Store in secrets manager
                    secrets_manager.set_secret('_'.join(path), secret_value)
                    value[secret_key] = f"ref:COGNIWATCH_{'_'.join(path).upper()}"
                    logger.info(f"Encrypted: {'.'.join(path)}")
            except (KeyError, TypeError):
                pass
        
        # Save sanitized config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        os.chmod(config_path, 0o600)
        
        logger.info(f"Config migrated to encrypted format: {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to migrate config: {e}")
        return False
