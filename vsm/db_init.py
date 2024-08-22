from vsm import settings

from vsm.db import DbConnector
from vsm.db_dynanamo import DynamodbClient
from vsm.db_pgsql import PsqlConnector
from vsm.settings import DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME


def create_db_connector() -> DbConnector:
    return PsqlConnector(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USERNAME,
        password=DB_PASSWORD,
    ) if settings.DB_TYPE == "postgresql" else DynamodbClient()
