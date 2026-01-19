"""
Handels SNS topic pushing
"""

from datetime import datetime, timezone

import boto3

from .config import ACCEPTABLE_ERROR_THRESHOLD
from .logger import get_logger

# ────────────────────── Getting logger ─────────────────────────────

logger = get_logger()

# ────────────── Notification AWS topic logic ───────────────────────

_SNS_CLIENT = boto3.client("sns", "ap-southeast-2")


def publish_to_topic(topic_ARN: str, error_rate: float, date: str, function_name: str):
    """
    Publishes warning to AWS topic if health checker detects a threshold violation

    Args:
        topic_ARN: AWS topic ARN
        error_rate: actual error rate for health checker call
        date: UTC date now
        function_name: function which health check was performed on
    """
    logger.info(f"Health warning causing publishing to ARN topic: {topic_ARN}")
    publish = _SNS_CLIENT.publish(
        TopicArn=topic_ARN,
        Message=f"Error rate on for {function_name} {date} of {error_rate} exceeded acceptable threshold of {ACCEPTABLE_ERROR_THRESHOLD}",
        Subject=f"Health checker warning {date}",
    )
