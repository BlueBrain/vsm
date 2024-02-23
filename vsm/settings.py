import os

BASE_HOST = "127.0.0.1"
MASTER_PORT = 4444
SLAVE_PORT = 8888
BRAYNS_PORT = 5000
BCSB_PORT = 8000

CERT_CRT = os.getenv("VSM_SSL_CRT", "sslcert.crt")
CERT_KEY = os.getenv("VSM_SSL_KEY", "sslcert.key")

# Debug/logging
LOG_LEVEL = os.getenv("VSM_LOG_LEVEL", "INFO").upper()

# DB
DB_HOST = os.getenv("VSM_DB_HOST", "localhost:5432")
DB_NAME = os.getenv("VSM_DB_NAME")
DB_USERNAME = os.getenv("VSM_DB_USERNAME")
DB_PASSWORD = os.getenv("VSM_DB_PASSWORD")

# Job allocation (UNICORE or AWS)
JOB_ALLOCATOR = os.getenv("VSM_JOB_ALLOCATOR", "UNICORE")

# UNICORE
UNICORE_ENDPOINT = os.getenv("VSM_UNICORE_ENDPOINT", "https://unicore.bbp.epfl.ch:8080/BB5-CSCS/rest/core")
UNICORE_CA_FILE = os.getenv("VSM_UNICORE_CA_FILE", "/tmp/ca.pem")

# AWS
AWS_TASK_DEFINITION = os.getenv("VSM_BRAYNS_TASK_DEFINITION")
AWS_SECURITY_GROUPS = os.getenv("VSM_BRAYNS_TASK_SECURITY_GROUPS", "").split(",")
AWS_SUBNETS = os.getenv("VSM_BRAYNS_TASK_SUBNETS", "").split(",")
AWS_CLUSTER = os.getenv("VSM_BRAYNS_TASK_CLUSTER", "viz_ecs_cluster")
AWS_CAPACITY_PROVIDER = os.getenv("VSM_BRAYNS_TASK_CAPACITY_PROVIDER", "viz_ECS_CapacityProvider")

# Keycloak
USE_KEYCLOAK = bool(int(os.getenv("VSM_USE_KEYCLOAK", "1")))
KEYCLOAK_USER_INFO_URL = os.getenv(
    "VSM_KEYCLOAK_URL", "https://bbpauth.epfl.ch/auth/realms/BBP/protocol/openid-connect/userinfo"
)
KEYCLOAK_HOST = os.getenv("VSM_KEYCLOAK_HOST", "bbpauth.epfl.ch")
