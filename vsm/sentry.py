import logging

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from . import settings


def set_up():
    sentry_logging = LoggingIntegration(
        level=logging.DEBUG,  # Capture debug and above as breadcrumbs
        event_level=logging.WARNING,  # Send errors as events
    )

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[sentry_logging, AioHttpIntegration()],
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0,
        debug=False,
        http_proxy=settings.HTTP_PROXY,
    )
