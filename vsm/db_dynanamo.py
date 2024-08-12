import boto3

from .db import DbConnection, Job, DbConnector, parse_job
from .settings import DBD_TABLE_NAME


from boto3.dynamodb.types import TypeDeserializer


def dynamo_obj_to_python_obj(dynamo_obj: dict) -> dict:
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in dynamo_obj.items()}


class DynamoConnection(DbConnection):
    def __init__(self, client) -> None:
        self.client = client

    async def close(self) -> None:
        pass

    async def get_jobs(self) -> list[Job]:
        jobs = self.client.scan(TableName=DBD_TABLE_NAME)["Items"]
        return [parse_job(dynamo_obj_to_python_obj(job)) for job in jobs]

    async def get_job(self, id: str) -> Job | None:
        job = dynamo_obj_to_python_obj(self.client.get_item(
            TableName=DBD_TABLE_NAME,
            Key={'job_id': {'S': id}},
        )["Item"])
        return parse_job(job)

    async def insert_job(self, job: Job) -> None:
        self.client.put_item(
            TableName=DBD_TABLE_NAME,
            Item={
                'job_id': {'S': job.id},
                'user_id': {'S': job.user},
                'start_time': {'S': job.start_time},
                'end_time': {'S': job.end_time},
                'hostname': {'S': job.host},
            },
        )

    async def update_job(self, id: str, host: str) -> None:
        self.client.update_item(
            TableName=DBD_TABLE_NAME,
            Key={'job_id': {'S': id}},
            UpdateExpression="SEThostname = :hostname",
            ExpressionAttributeValues={
                ':hostname': {'S': host},
            }
        )

    async def delete_job(self, id: str) -> None:
        self.client.delete_item(
            TableName=DBD_TABLE_NAME,
            Key={'job_id': {'S': id}}
        )


class DynamodbClient(DbConnector):
    def __init__(self):
        self.client = boto3.client("dynamodb")

    async def connect(self) -> DbConnection:
        return DynamoConnection(self.client)

