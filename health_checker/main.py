"""
Logic orchestrator for health checker
"""

from typing import List, Dict, Any
from logging import LoggerAdapter, Logger

import boto3

from .utils import (
    prior_day_calls,
    query_parser,
    threshold_checker,
    compare_run_times,
    get_current_UTC_date,
)
from .logger import get_logger
from .database import init_pool
from .secrets import get_db_config
from .config import FUNCTIONS_TO_CHECK

# ────────────────────── Getting logger ─────────────────────────────

logger = get_logger()

# ────────────────────── Handler function ─────────────────────────────


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Dict[str, Any]: Response with status code

    """
    try:
        session_id = get_current_UTC_date
        logger_ctx: LoggerAdapter[Logger] = LoggerAdapter(
            logger,
            {"session_id": session_id, "aws_request_id": context.aws_request_id},
        )
        logger_ctx.info("Starting health check")
        # ───────────────── Database connection init ──────────────────

        init_pool(get_db_config())

        # ───────────────── Main status check logic ──────────────────

        # query_result = prior_day_calls("ENWL_power_scraper")
        # logger.debug(f"{query_result}")
        for function_name in FUNCTIONS_TO_CHECK:
            query_result = prior_day_calls(function_name)
            errored_rows = query_parser(query_result, function_name)
            threshold_checker(errored_rows, query_result, function_name)
        # dif_times = compare_run_times("ENWL_power_scraper")
        # logger.info(f"{dif_times}")

        return {"status code": 200, "body": "Health check completed successfully"}
    except Exception as e:
        logger.error(f"Error occured at main function call: {e}")
        raise


# ────────────────────── Out of date test event ─────────────────────────────

event = {
    "Records": [
        {
            "EventSource": "aws:sns",
            "EventVersion": "1.0",
            "EventSubscriptionArn": "arn:aws:sns:ap-southeast-2:542726313726:All_scrapers:1f6f3ad2-a463-4e33-ae3c-7e4f9be1d695",
            "Sns": {
                "Type": "Notification",
                "MessageId": "240c0160-9eb0-541b-b08a-601994906cf4",
                "TopicArn": "arn:aws:sns:ap-southeast-2:542726313726:All_scrapers",
                "Message": '{"version":"0","id":"0568ff07-bed0-45d0-84fb-e4bc87b57a3c","detail-type":"Scheduled Event","source":"aws.scheduler","account":"542726313726","time":"2025-10-27T05:48:46Z","region":"ap-southeast-2","resources":["arn:aws:scheduler:ap-southeast-2:542726313726:schedule/default/3_min_schedule"],"detail":"{}"}',
                "Timestamp": "2025-10-27T05:49:20.652Z",
                "SignatureVersion": "1",
                "Signature": "BFIJviwHDxlh3FWRDAWznobQHSZ6VD04TwzDzape3iQeNf+CPEGVhQEe0gw9EEKFUP4JcgROr61movdRMPGZBEQbdUMVfPjCykpBH6xrlFq6QFm58aqCFd6+ryC9Opa61dGwsQ0FlCoyp3TiBQxwNkv57h2i8wX85QUBS1kcE2uHNXw6ubznl+z02suvlBO0EocVUDWGx2zj8X628KbBCCxU4qTKHp6yyqLI8SyYS6RS3peVdHkmQNLqBMgrDbIa3xXkbBJvnCPhu5amdQCnFpx2A7r+9lLgdklsRJKnfbQvaZUtAgUvFlOiCPiHGj7Wvn8puixy2J/9H3tgE7fRXQ==",
                "SigningCertUrl": "https://sns.ap-southeast-2.amazonaws.com/SimpleNotificationService-6209c161c6221fdf56ec1eb5c821d112.pem",
                "Subject": None,
                "UnsubscribeUrl": "https://sns.ap-southeast-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:ap-southeast-2:542726313726:All_scrapers:1f6f3ad2-a463-4e33-ae3c-7e4f9be1d695",
                "MessageAttributes": {},
            },
        }
    ]
}

if __name__ == "__main__":
    handler(event, "test")
