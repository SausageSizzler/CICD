"""
Structured JSON logger shared by all modules.
"""

import logging
import os
import sys
import traceback
from typing import Any, Dict

# ─────────────────────────── fixed-path import ──────────────────────────────

from pythonjsonlogger.json import JsonFormatter


# ───────────────────────────── custom formatter ─────────────────────────────
class LineWiseJsonFormatter(JsonFormatter):  # type: ignore[misc, valid-type]
    """
    Custom JSON formatter that converts exception information to a list of lines.

    This formatter extends the standard JsonFormatter to provide better formatting
    of exception information in the logs, making them more readable and structured.
    """

    def add_fields(  # type: ignore[override]
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # Convert exc_info string to list-of-lines for cleaner JSON
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_record["trace"] = traceback.format_exception(
                exc_type, exc_value, exc_tb
            )
            log_record.pop("exc_info", None)


# ─────────────────────────── module-level logger ─────────────────────────────
_LOGGER_NAME = "health_checker"
_DEFAULT_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def _build_handler() -> logging.Handler:
    """
    Create and configure a logging handler with JSON formatting.

    Returns:
        logging.Handler: Configured logging handler that outputs to stdout
                         with JSON formatting.
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(session_id)s %(aws_request_id)s"
    )
    handler.setFormatter(formatter)
    return handler


_logger = logging.getLogger(_LOGGER_NAME)
if not _logger.handlers:  # prevent duplicate logs in local tests
    _logger.setLevel(_DEFAULT_LEVEL)
    _logger.addHandler(_build_handler())
    _logger.propagate = False


def get_logger() -> logging.Logger:
    """
    Get the configured logger instance for the application.

    This function returns a singleton logger instance that is configured with
    JSON formatting and appropriate log levels. All modules should use this
    function to obtain a logger instance to ensure consistent logging behavior.

    Returns:
        logging.Logger: Configured logger instance for the application.
    """
    return _logger
