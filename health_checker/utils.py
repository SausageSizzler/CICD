"""
Helper functions for health checker
"""

from typing import Any, List
from datetime import datetime, timezone, timedelta

import boto3

from .logger import get_logger
from .database import return_function_rows
from .config import ACCEPTABLE_ERROR_THRESHOLD, EMAIL_TOPIC_ARN, SCHEDULE_NAME
from .notification import publish_to_topic

# ────────────────────── Getting logger ─────────────────────────────

logger = get_logger()

# ────────────────────── Helper functions ─────────────────────────────


def get_event_bridge_schedule() -> dict:
    """
    Obtain the eventbridge schedule for lambda functions

    Returns:
        dict: AWS event bridge schedule
    """
    _CLIENT = boto3.client("scheduler", "ap-southeast-2")
    response = _CLIENT.get_schedule(Name=SCHEDULE_NAME)
    return response


def prior_day_calls(function_name: str) -> List:
    """
    Obtains all prior day invokations for a given lambda function

    Args:
        function_name: relevant lambda function

    Returns:
        List: list of dicts, one dict for each call of the lambda funciton
        the prior day
    """
    current_utc_datetime = datetime.now(timezone.utc)
    prior_date = current_utc_datetime - timedelta(days=1)
    prior_date = prior_date.strftime("%Y-%m-%d")
    result = return_function_rows(function_name, prior_date)
    return result


def query_parser(query_result: List[dict], function_name: str) -> List[List]:
    """
    From a lambda funciton's prior day calls, checks if there are any unsuccessful
    invokations, or if the records written and read don't match for any call

    Args:
        query_result: list of all prior day calls of a given lambda function
        function_name: lambda function name

    Returns:
        List[List]: list of each row that failed the checks, plus where the
        checks failed
    """
    logger.info(f"Parsing database query results for function {function_name}")
    errored_rows: List[List] = []
    for row_data in query_result:
        if row_data["records_written"] != row_data["records_read"]:
            errored_rows.append(
                [
                    row_data["run_id"],
                    f"Records read != records written: {row_data['records_written']} != {row_data['records_read']}",
                ]
            )
        elif (
            row_data["status"].upper() != "SUCCESS_WITH_DATA"
            and row_data["status"].upper() != "SUCCESS_NO_DATA"
        ):
            errored_rows.append(
                [row_data["run_id"], f"Status was not successful: {row_data["status"]}"]
            )
        # Add another here for delyed function start time?
    return errored_rows


def threshold_checker(
    errored_rows: List[List], query_result: List[dict], function_name: str
):
    """
    Checks if a function's error rate was above the acceptable rate for a given day.
    If yes, calls the notification service

    Args:
        errored_rows: all calls which were considered failed
        query_result: all prior day invokations for the lambda function
        function_name: lambda function name
    """
    error_rate: float = len(errored_rows) / len(query_result)
    if error_rate >= ACCEPTABLE_ERROR_THRESHOLD:
        logger.warning(
            f"Error rate for {function_name} health check on {get_current_UTC_date()} "
            f"was {error_rate}, > acceptable rate of {ACCEPTABLE_ERROR_THRESHOLD}"
        )
        publish_to_topic(
            EMAIL_TOPIC_ARN, error_rate, get_current_UTC_date(), function_name
        )
        return

    logger.info(
        f"Error rate for {function_name} health check on {get_current_UTC_date()} was {error_rate}"
    )


def get_current_UTC_date() -> str:
    """
    Obtains current UTC datetime in %Y-%m-%d format

    Returns:
        UTC_date: UTC datatime in specified format
    """
    UTC_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return UTC_date


# ─────────── Start time comparison helper functions ───────────────
# Note these are not actually implemented


def relative_start_time(function_name: str) -> datetime:
    """
    Because lambda functions are called on a rate(...) basis, their first call
    each day is slightly different. This time is then the basis for comparison
    for all further day invokations. This function returns the first call time
    for the given day

    Args:
        function_name: lambda function name

    Retuns:
        earliest_date: time of earliest call for the lambda on a given day
    """
    query_result: List[dict] = prior_day_calls(function_name)
    earliest_date: datetime = query_result[0]["function_start_time"]
    for row in query_result:
        if row["function_start_time"] < earliest_date:
            earliest_date = row["function_start_time"]

    return earliest_date


def generate_exp_times(function_name: str) -> list[datetime]:
    """
    Based on the first call of the day, extrapolates the schedule of the other
    calls for the day

    Args:
        function_name: lmabda function name

    Retuns:
        expected_run_times: schedule of expected call times
    """
    earliest_time: datetime = relative_start_time(function_name)
    rate_expression = get_schedule_expression(get_event_bridge_schedule())
    if not "rate" in rate_expression:
        logger.warning(
            f"Cron expression used for function schedule - this functionality is not added yet"
        )
        raise NotImplementedError

    parts = rate_expression.split("(")
    rate_part = parts[1].rstrip(")")
    rate_value, rate = rate_part.split()

    if rate != "minutes":
        logger.warning(
            f"Rate in different granularity to minutes used - functionality not added"
        )
        raise NotImplementedError

    expected_run_times: List[datetime] = []
    start_time = earliest_time

    while start_time < earliest_time + timedelta(days=1):
        expected_run_times.append(start_time)
        start_time += timedelta(minutes=3)

    logger.info(f"Expected schedule created")
    return expected_run_times


def enumerate_run_times(function_name: str):
    """
    Enumerates the actual start_times of the given lambda function
    for a given day

    Args:
        function_name: lmabda function name

    Returns:
        enumerated_run_times: actual runtimes for lambda function in
        chronological order
    """
    query_result: List[dict] = prior_day_calls(function_name)
    function_start_times: List[datetime] = []
    enumerated_run_times: dict = {}
    for row in query_result:
        function_start_times.append(row["function_start_time"])

    function_start_times.sort()
    for call, run_time in enumerate(function_start_times):
        enumerated_run_times[call] = run_time

    return enumerated_run_times


def get_schedule_expression(event_bridge_response: dict) -> str:
    """
    From the eventbridge schedule, obtains the actual rate expression
    used for scheduling the lambda functions

    Args:
        event_bridge_response: AWS eventbrige schedule information

    Returns:
        rate_expression: rate expression used in eventbridge schedule
    """
    rate_expression = event_bridge_response["ScheduleExpression"]
    return rate_expression


def compare_run_times(function_name: str) -> list[dict]:
    """
    Given the actual and expected start_times for the lambda function,
    compare the two and report any discrepancies

    Args:
        function_name: lambda function name

    Returns:
        dif_times: list of all different start_times including the expected
        and actual run times
    """
    enumerated_run_times: dict[int, datetime] = enumerate_run_times(function_name)
    expected_run_times: list[datetime] = generate_exp_times(function_name)
    dif_times: List[dict] = []
    logger.info(f"{len(expected_run_times)} vs {len(enumerated_run_times)}")
    for i in range(len(enumerated_run_times)):
        if enumerated_run_times[i] != expected_run_times[i]:
            dif_times.append(
                {
                    "Expected_run_time": expected_run_times[i],
                    "Actual_run_time": enumerated_run_times[i],
                }
            )
    # logger here?
    return dif_times
