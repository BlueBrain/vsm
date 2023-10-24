import os

BASE_HOST = "127.0.0.1"
BASE_PORT = 4444

CERT_CRT = os.getenv("VSM_SSL_CRT", "sslcert.crt")
CERT_KEY = os.getenv("VSM_SSL_KEY", "sslcert.key")

ENVIRONMENT = os.getenv("VSM_ENVIRONMENT")
HTTP_PROXY = os.getenv("VSM_HTTP_PROXY")
SENTRY_DSN = os.getenv("VSM_SENTRY_DSN")
SWAGGER_ENABLED = bool(int(os.getenv("VSM_SWAGGER_ENABLED", "0")))

# Debug/logging
LOG_LEVEL = os.environ.get("VSM_LOG_LEVEL", "INFO").upper()

# DB variables
DB_HOST = os.getenv("VSM_DB_HOST", "localhost:5432")
DB_NAME = os.getenv("VSM_DB_NAME", "mooc_db")
DB_USERNAME = os.getenv("VSM_DB_USERNAME")
DB_PASSWORD = os.getenv("VSM_DB_PASSWORD")

# Job allocation variables (UNICORE or AWS)
JOB_ALLOCATOR = os.getenv("VSM_JOB_ALLOCATOR", "UNICORE")

# UNICORE variables
UNICORE_ENDPOINT = os.getenv("VSM_UNICORE_ENDPOINT", "https://unicore.bbp.epfl.ch:8080/BB5-CSCS/rest/core")
UNICORE_CA_FILE = os.getenv("VSM_UNICORE_CA_FILE", "/tmp/ca.pem")

# AWS variables
AWS_HOST = os.getenv("VSM_AWS_HOST", "localhost")

# BBP Keycloak variables
KEYCLOAK_USER_INFO_URL = os.getenv(
    "VSM_KEYCLOAK_URL",
    "https://bbpauth.epfl.ch/auth/realms/BBP/protocol/openid-connect/userinfo",
)
KEYCLOAK_HOST = os.getenv("VSM_KEYCLOAK_HOST", "bbpauth.epfl.ch")
