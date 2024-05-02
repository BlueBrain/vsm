from logging import INFO, Logger
from typing import Any

import boto3
from aiohttp import ClientSession, web

from .allocator import JobAllocator, JobDetails
from .settings import (
    AWS_BUCKET_MOUNT_PATH,
    AWS_BUCKET_NAME,
    AWS_CAPACITY_PROVIDER,
    AWS_CLUSTER,
    AWS_SECURITY_GROUPS,
    AWS_SUBNETS,
    AWS_TASK_DEFINITION,
)


class AwsAllocator(JobAllocator):
    def __init__(self, session: ClientSession, logger: Logger) -> None:
        self._session = session
        self._logger = logger
        self._ecs_client = boto3.client("ecs")
        boto3.set_stream_logger(level=INFO)

    async def close(self) -> None:
        pass

    async def create_job(self, token: str, payload: dict[str, Any]) -> str:
        self._logger.info("Creating new AWS task")

        project = payload.get("project")

        if project is None:
            raise web.HTTPBadRequest(text="No projects provided in request body")

        self._logger.info(f"Project name {project}")

        try:
            return await self._run_aws_task(project)
        except Exception as e:
            self._logger.error(f"Error in AWS call: {e}")
            raise web.HTTPInternalServerError(text="Job allocation failed")

    async def destroy_job(self, job_id: str) -> None:
        try:
            response = self._ecs_client.stop_task(cluster=AWS_CLUSTER, task=job_id)
        except Exception as e:
            self._logger.error(f"Failed to stop task {job_id}, assuming invalid ID: {e}")
            raise web.HTTPBadRequest(text=f"Invalid job ID {job_id}")

        self._logger.debug(f"AWS stop response {response}")

    async def get_job_details(self, token: str, job_id: str) -> JobDetails:
        try:
            response = self._ecs_client.describe_tasks(cluster=AWS_CLUSTER, tasks=[job_id])
        except Exception as e:
            self._logger.error(f"Failed to describe task {job_id}, assuming invalid ID: {e}")
            raise web.HTTPBadRequest(text=f"Invalid job ID {job_id}")

        self._logger.debug(f"AWS describe tasks response {response}")

        try:
            host_ip = response["tasks"][0]["containers"][0]["networkInterfaces"][0]["privateIpv4Address"]
        except (KeyError, IndexError) as e:
            self._logger.warn(f"Cannot get host_ip from AWS response {e}")
            return JobDetails(job_running=False)

        self._logger.info(f"Host IP: {host_ip}")

        if not await self._check_brayns_responds(host_ip):
            return JobDetails(job_running=False)

        return JobDetails(job_running=True, host=host_ip)

    async def _run_aws_task(self, project: str) -> str:
        bucket_path = f"{AWS_BUCKET_NAME}:/{project}"
        root_folder = f"{AWS_BUCKET_MOUNT_PATH}/{project}"

        self._logger.info(f"Starting new ECS task mounting {bucket_path} at {root_folder}")

        response = self._ecs_client.run_task(
            cluster=AWS_CLUSTER,
            taskDefinition=AWS_TASK_DEFINITION,
            enableExecuteCommand=True,
            networkConfiguration={
                "awsvpcConfiguration": {
                    "assignPublicIp": "DISABLED",
                    "securityGroups": AWS_SECURITY_GROUPS,
                    "subnets": AWS_SUBNETS,
                }
            },
            capacityProviderStrategy=[
                {
                    "capacityProvider": AWS_CAPACITY_PROVIDER,
                    "weight": 1,
                    "base": 0,
                }
            ],
            overrides={
                "containerOverrides": [
                    {
                        "name": "viz_brayns",
                        "environment": [
                            {"name": "S3_BUCKET_PATH", "value": bucket_path},
                            {"name": "FUSE_MOUNT_POINT", "value": root_folder},
                        ],
                    }
                ]
            },
        )

        self._logger.debug(f"AWS start response {response}")

        task_arn = response["tasks"][0]["taskArn"]

        if not isinstance(task_arn, str):
            self._logger.error("Task ARN is not a string")
            raise ValueError("Invalid task ARN from AWS client")

        task_id = task_arn.rsplit("/", 1)[-1]

        if len(task_id) != 32:
            self._logger.error("Task ARN is not 32 chars")
            raise ValueError("Invalid task ID from AWS client")

        self._logger.info(f"Task ID: {task_id}")

        return task_id

    async def _check_brayns_responds(self, host_ip: str) -> bool:
        try:
            response = await self._session.get(f"http://{host_ip}:5000/healthz")
            return response.ok
        except Exception as e:
            self._logger.warn(f"Brayns healthcheck failed: {e}")
            return False
