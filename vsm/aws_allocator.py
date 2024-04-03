import logging
from typing import Any

import boto3
from aiohttp import ClientSession

from vsm.settings import (
    AWS_CAPACITY_PROVIDER,
    AWS_CLUSTER,
    AWS_SECURITY_GROUPS,
    AWS_SUBNETS,
    AWS_TASK_DEFINITION,
)
from . import settings

from .allocator import AllocationError, JobAllocator, JobDetails, JobNotFound


class AwsAllocator(JobAllocator):
    def __init__(self, session: ClientSession) -> None:
        self._session = session
        self._ecs_client = boto3.client("ecs")
        boto3.set_stream_logger(level=logging.INFO)

    async def create_job(self, token: str, payload: dict[str, Any]) -> str:
        project = payload["project"]
        bucket_path = f"{settings.AWS_BUCKET_NAME}/{project}"
        root_folder = f"{settings.AWS_BUCKET_MOUNT_PATH}/{project}"

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
                        "environment": [
                            {
                                # TODO
                                'name': "S3_FULL_PATH",
                                'value': bucket_path
                            },
                            {
                                #TODO ->
                                'name': "S3_ROOT_FOLDER",
                                'value': root_folder
                            }
                        ]}
                ]}
        )

        logging.debug(f"AWS response {response}")

        try:
            task_arn = response["tasks"][0]["taskArn"]
        except (KeyError, IndexError):
            raise AllocationError("Invalid response type from AWS client")

        if not isinstance(task_arn, str):
            raise AllocationError("Invalid task ARN from AWS client")

        task_id = task_arn.rsplit("/", 1)[-1]

        if len(task_id) != 32:
            raise AllocationError("Invalid task ID from AWS client")

        return task_id

    async def destroy_job(self, token: str, job_id: str) -> None:
        try:
            response = self._ecs_client.stop_task(cluster=AWS_CLUSTER, task=job_id)
        except Exception as e:
            raise JobNotFound(str(e))

        logging.debug(f"AWS stop response {response}")

    async def get_job_details(self, token: str, job_id: str) -> JobDetails:
        try:
            response = self._ecs_client.describe_tasks(cluster=AWS_CLUSTER, tasks=[job_id])
        except Exception as e:
            raise JobNotFound(str(e))

        try:
            host_ip = response["tasks"][0]["containers"][0]["networkInterfaces"][0]["privateIpv4Address"]
        except (KeyError, IndexError) as e:
            logging.error(f"Cannot get host_ip from AWS response {e}")
            return JobDetails(job_running=False)

        if not await self._check_brayns_responds(host_ip):
            return JobDetails(job_running=False)

        return JobDetails(job_running=True, host=host_ip)

    async def _check_brayns_responds(self, host_ip: str) -> bool:
        try:
            response = await self._session.get(f"http://{host_ip}:5000/healthz")
            return response.ok
        except Exception as e:
            logging.error(f"Cannot talk to brayns {e}")
            return False
