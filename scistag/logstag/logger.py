"""
Helper module which provides easy access to SciStag's logging functions
"""

import logging


def get_logger() -> logging.Logger:
    """
    Returns the default logger object

    :return: The SciStag shared logging object
    """
    return logging.getLogger("scistag")


def log_info(msg: str):
    """
    Logs an info message

    :param msg: The text to log
    """
    logger = get_logger()
    logger.info(msg)


def log_warning(msg: str):
    """
    Logs a warning message

    :param msg: The text to log
    """
    logger = get_logger()
    logger.warning(msg)


def log_error(msg: str):
    """
    Logs an error message

    :param msg: The text to log
    """
    logger = get_logger()
    logger.error(msg)
