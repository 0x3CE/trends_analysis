# app/exceptions.py
"""Custom exceptions for the application."""


class TwitterAPIError(Exception):
    """Exception levée lors d'erreurs avec l'API Twitter/X."""
    pass


class DatabaseError(Exception):
    """Exception levée lors d'erreurs de base de données."""
    pass


class ConfigurationError(Exception):
    """Exception levée lors d'erreurs de configuration."""
    pass