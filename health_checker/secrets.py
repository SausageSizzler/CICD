"""
Secret management for health checker
"""

import json
from functools import lru_cache
from typing import Any, Dict

import boto3

from .logger import get_logger
from .config import DATABASE_SECRET

# ────────────────────── Getting logger ─────────────────────────────

logger = get_logger()

# ───────────────────── Secrets management ──────────────────────────


_CLIENT = boto3.client("secretsmanager", "ap-southeast-2")


class SecretError(RuntimeError):
    """Exception raised for errors in secret retrieval."""

    pass


@lru_cache(maxsize=1)
def _get_secret_payload(secret_name: str) -> Dict[str, str]:
    """
    Fetch and cache the entire secret JSON once per cold start.

    Returns:
        Dict[str, str]: Secret payload as a dictionary

    Raises:
        SecretError: If the secret cannot be retrieved
    """
    try:
        resp = _CLIENT.get_secret_value(SecretId=secret_name)
        return json.loads(resp["SecretString"])
    except _CLIENT.exceptions.ResourceNotFoundException as exc:
        logger.error(f"Secret {secret_name} not found")
        raise SecretError(f"Secret {secret_name} not found") from exc
    except Exception as exc:
        logger.error(
            "Unable to retrieve secret. Check AWS credentials and permissions."
        )
        raise SecretError("Access denied to Secrets Manager") from exc


def get_db_config() -> Dict[str, str]:
    """
    Get database configuration from secrets.

    Returns:
        Dict[str, str]: Database configuration parameters
    """
    payload = _get_secret_payload(secret_name=DATABASE_SECRET)
    return {
        "host": payload["host"],
        "user": payload["user"],
        "password": payload["password"],
        "database": payload["database"],
    }
