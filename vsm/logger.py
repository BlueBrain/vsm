import sys
from logging import Formatter, Logger, StreamHandler

from .settings import LOG_LEVEL

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
FORMAT = "%(asctime)s [%(levelname)s] %(name)s %(module)s.%(funcName)s(%(lineno)d): %(message)s"


def create_logger(name: str, level: int | str = LOG_LEVEL, fmt: str = FORMAT) -> Logger:
    logger = Logger(name)
    logger.setLevel(level)
    handler = StreamHandler(sys.stdout)
    formatter = Formatter(fmt, DATE_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
