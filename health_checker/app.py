"""
Entry point for lambda
"""

from .main import handler
from .logger import get_logger
from logging import Logger

# ────────────────────── Getting logger ─────────────────────────────

logger: Logger = get_logger()

# ───────────────────────── Handler ─────────────────────────────────


def lambda_handler(event, context):
    """
    Lambda function handler.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        dict: Response with status code
    """
    result = handler(event, context)
    logger.info(result["body"])
    return result
