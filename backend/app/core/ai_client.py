"""
AI Client Dependency
Provides AI client instance for dependency injection
"""
from app.services.ai_client import ai_client


def get_ai_client():
    """
    Dependency function to get the global AI client instance

    Returns:
        AIClient: Global AI client instance
    """
    return ai_client