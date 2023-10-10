import os

BASE_HOST = "127.0.0.1"
BASE_PORT = 4444
ALLOWED_HOSTS = os.getenv("VMM_ALLOWED_HOSTS", "").split(",")

ENVIRONMENT = os.getenv("VMM_ENVIRONMENT")
HTTP_PROXY = os.getenv("HTTP_PROXY")
SENTRY_DSN = os.getenv("VMM_SENTRY_DSN")
SWAGGER_ENABLED = bool(int(os.getenv("VMM_SWAGGER_ENABLED", "0")))

# Debug/logging
LOG_LEVEL = os.environ.get("VMM_LOG_LEVEL", "INFO").upper()

# DB variables
DB_HOST = os.getenv("VMM_DB_HOST", "localhost:27017")
DB_NAME = os.getenv("VMM_DB_NAME", "mooc_db")
DB_USERNAME = os.getenv("VMM_DB_USERNAME")
DB_PASSWORD = os.getenv("VMM_DB_PASSWORD")

# Job allocation variables (UNICORE or AWS)
JOB_ALLOCATOR = os.getenv("VMM_JOB_ALLOCATOR", "UNICORE")

# UNICORE variables
UNICORE_USPACE_SUFFIX = "-uspace"
UNICORE_ROOT_URL = "https://unicore.bbp.epfl.ch:8080/BB5-CSCS"
UNICORE_ENDPOINT = f"{UNICORE_ROOT_URL}/rest/core"
UNICORE_CA_FILE = os.getenv("VMM_UNICORE_CA_FILE", "/tmp/ca.pem")

# AWS variables
AWS_JOB_ID = "fixed_job_id"
AWS_HOST = os.getenv("VMM_AWS_HOST", "localhost")

# Keycloak variables
KEYCLOAK_SERVER_URL = "https://bbpauth.epfl.ch/auth/"
KEYCLOAK_REALM_NAME = "BBP"
KEYCLOAK_CLIENT_ID = os.getenv("VMM_KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET_KEY = os.getenv("VMM_KEYCLOAK_SECRET_KEY")

# BBP Keycloak variables
BBP_KEYCLOAK_USER_INFO_URL = "https://bbpauth.epfl.ch/auth/realms/BBP/protocol/openid-connect/userinfo"
BBP_KEYCLOAK_HOST = "bbpauth.epfl.ch"

# 'X-Original-Forwarded-For'
CLIENT_IP_HEADER_FIELD = "X-Original-Forwarded-For"

CERT_CRT = os.getenv("VMM_SSL_CRT", "sslcert.crt")
CERT_KEY = os.getenv("VMM_SSL_KEY", "sslcert.key")

ERROR_RESPONSE_RETRY_AFTER_SECONDS = int(os.getenv("VMM_ERROR_RESPONSE_RETRY_AFTER_SECONDS", "1"))
ERROR_RESPONSE_PAUSE_INCREMENT_FACTOR = float(os.getenv("VMM_ERROR_RESPONSE_PAUSE_INCREMENT_FACTOR", "1.5"))
