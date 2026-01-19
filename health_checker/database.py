"""
Database access functionality for health checker
"""

from typing import List, Dict, Mapping, Any
import os
from contextlib import contextmanager
from datetime import datetime

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

from .logger import get_logger

# ────────────────────── Getting logger ─────────────────────────────

logger = get_logger()

# ────────────────────── MySQL connection ───────────────────────────

_POOL: MySQLConnectionPool | None = None


class DatabaseError(Exception):
    """
    Exception for database related errors
    """

    pass


def init_pool(db_config: Dict[str, str]) -> None:
    """
    Initialize the database connection pool.

    Args:
        db_config: Database configuration parameters
    """
    global _POOL
    if _POOL is not None:  # cold-start only
        return

    pool_kwargs: Mapping[str, Any] = {
        **db_config,
        "autocommit": False,
        "charset": "utf8mb4",
    }

    _POOL = MySQLConnectionPool(
        pool_name="live_station_pool",
        pool_size=int(os.getenv("DB_POOL_SIZE", 4)),
        **pool_kwargs,
    )
    logger.debug("Database connection pool initialized")


# ──────────────────── Context managers ───────────────────────────


@contextmanager
def get_conn() -> Any:
    """
    Handles Connectioning to DB and commiting/rolling back DB queries

    Raises:
        DatabaseError: If the connection cannot be created
    """
    if _POOL is None:
        return

    connection = _POOL.get_connection()

    try:
        yield connection
        logger.debug("Transaction commited")
        connection.commit()
    except DatabaseError as e:
        connection.rollback()
        logger.error(f"Failed to connect and commit transaction to database: {e}")
        raise e
    finally:
        connection.close()


@contextmanager
def get_cursor(connection: Any) -> Any:
    """
    Context manager for the cursor object for DB connection

    Args:
        connection: Connection to the database from connection pool
    """
    cursor = connection.cursor(dictionary=True)
    logger.debug("Cursor created")
    try:
        yield cursor
    except Exception as e:
        raise e
    finally:
        cursor.close()


# ────────────────────── Database query logic ─────────────────────────────


def return_function_rows(function_name: str, date: str) -> List:
    """
    Queries database for runAudits rows for the given function
    on the given date

    Args:
        function_name: name of function to query for
        date: date when invokation took place

    Returns:
        List: list of dicts, one dict for each row containing the
        revelvent data
    """
    try:
        logger.info(f"Getting database rows for {function_name} on {date}")
        with get_conn() as connection, get_cursor(connection) as cursor:
            cursor.execute(
                """
                SELECT * FROM runAudits WHERE function_name = %s 
                AND function_start_time LIKE %s
                """,
                (function_name, f"{date}%"),
            )
            result = cursor.fetchall()
            return result
    except:
        logger.warning(f"Failed to find any rows for the {function_name} function")
        raise
