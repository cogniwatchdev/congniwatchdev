# CogniWatch Configuration Module
"""
Configuration management with encryption support.
"""

from .encryption import SecretsManager, CredentialStore, hash_password, verify_password, migrate_config_to_encrypted

__all__ = [
    'SecretsManager',
    'CredentialStore',
    'hash_password',
    'verify_password',
    'migrate_config_to_encrypted',
]
