import logging

from . import settings


def configure() -> None:
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)
    formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s - %(filename)s.%(funcName)s(%(lineno)d) - %(message)s",
    )
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
