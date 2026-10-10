"""PyMySQL database connection and query helpers."""

import logging

import pymysql
from pymysql.cursors import DictCursor

from config import DevelopmentConfig

logger = logging.getLogger(__name__)

_config = DevelopmentConfig()


def get_db_connection():
    """Return a PyMySQL connection using DictCursor and config settings."""
    try:
        connection = pymysql.connect(
            host=_config.DB_HOST,
            user=_config.DB_USER,
            password=_config.DB_PASSWORD,
            database=_config.DB_NAME,
            port=_config.DB_PORT,
            cursorclass=DictCursor,
            autocommit=False,
            charset="utf8mb4",
        )
        return connection
    except pymysql.MySQLError as exc:
        logger.error("Database connection failed: %s", exc)
        raise


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a single SQL query.

    Returns:
        - lastrowid for INSERT when commit=True and no fetch requested
        - dict for fetch_one=True
        - list of dicts for fetch_all=True
        - rowcount for UPDATE/DELETE when commit=True
    """
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            result = None

            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            elif commit:
                result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount

            if commit:
                connection.commit()

            return result
    except pymysql.MySQLError as exc:
        if connection:
            connection.rollback()
        logger.error("Query execution failed: %s | Query: %s", exc, query)
        raise
    finally:
        if connection:
            connection.close()


def execute_many(query, params_list, commit=False):
    """Execute the same query for multiple parameter sets."""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.executemany(query, params_list)
            if commit:
                connection.commit()
            return cursor.rowcount
    except pymysql.MySQLError as exc:
        if connection:
            connection.rollback()
        logger.error("Batch query execution failed: %s | Query: %s", exc, query)
        raise
    finally:
        if connection:
            connection.close()
