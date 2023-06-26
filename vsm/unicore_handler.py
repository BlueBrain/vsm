from aiohttp import ContentTypeError

from . import settings
from .logger import logger


class UnicoreHandler:
    __shared_state = {}
    session = None

    def __init__(self):
        self.__dict__ = self.__shared_state

    def set_session(self, session):
        self.session = session

    @staticmethod
    def get_job_url(job_id):
        return f"{settings.UNICORE_ENDPOINT}/jobs/{job_id}"

    @staticmethod
    def get_auth_headers(token):
        return {"Authorization": f"{token}"}

    @staticmethod
    def get_json_headers(token):
        return {
            "Authorization": f"{token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def get_job_details(self, job_id, token):
        headers = self.get_json_headers(token)
        try:
            async with self.session.get(f"{self.get_job_url(job_id)}/details", headers=headers) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Unicore status check: {response}, exception: {e}")
            raise e

    async def get_file(self, token, working_dir, file_name):
        headers = self.get_auth_headers(token)
        url = f"{working_dir}/files/{file_name}"
        headers.update({"Accept": "application/octet-stream"})
        async with self.session.get(url, headers=headers) as r:
            if r.status == 404:
                raise FileNotFoundError
            return await r.read()

    async def core(self, token):
        url = f"{settings.UNICORE_ENDPOINT}"
        headers = self.get_json_headers(token)

        async with self.session.get(url, headers=headers) as r:
            return await r.json()

    async def create_job(self, token, payload):
        url = f"{settings.UNICORE_ENDPOINT}/jobs"
        headers = self.get_json_headers(token)
        async with self.session.post(url, json=payload, headers=headers) as unicore_response:
            return unicore_response

    async def update_job(self, payload, job_id, token):
        url = f"{settings.UNICORE_ENDPOINT}/jobs/{job_id}"
        headers = self.get_json_headers(token)

        async with self.session.put(url, json=payload, headers=headers) as unicore_response:
            return unicore_response

    async def get_job_info(self, job_id, token):
        url = f"{settings.UNICORE_ENDPOINT}/jobs/{job_id}"
        headers = self.get_json_headers(token)

        async with self.session.get(url, headers=headers) as unicore_response:
            return await unicore_response.json()

    async def update_file(self, file_url, payload, token):
        url = f"{settings.UNICORE_ENDPOINT}/storages/{file_url}"
        headers = self.get_auth_headers(token)
        headers.update({"Accept": "application/octet-stream"})
        headers.update({"Content-Type": "text/plain"})

        async with self.session.put(url, data=payload, headers=headers) as unicore_response:
            return unicore_response

    async def trigger_actions(self, action_url, token):
        url = f"{settings.UNICORE_ENDPOINT}/jobs/{action_url}"
        headers = self.get_json_headers(token)

        async with self.session.post(url, json={}, headers=headers) as unicore_response:
            return unicore_response

    async def get_jobs(self, query_params, token, user_id):
        # get only the jobs from the user
        query_params = f"{query_params},{user_id}"
        url = f"{settings.UNICORE_ENDPOINT}/jobs?{query_params}"
        headers = self.get_json_headers(token)

        async with self.session.get(url, headers=headers) as unicore_response:
            return await unicore_response.json()

    async def delete_job(self, job_id, token):
        url = f"{settings.UNICORE_ENDPOINT}/jobs/{job_id}"
        headers = self.get_json_headers(token)

        async with self.session.delete(url, headers=headers) as unicore_response:
            return unicore_response

    async def fetch_file_list(self, file_url, token):
        url = f"{settings.UNICORE_ENDPOINT}/storages/{file_url}"
        headers = self.get_json_headers(token)

        try:
            async with self.session.get(url, headers=headers) as unicore_response:
                return await unicore_response.json()
        except ContentTypeError as e:
            logger.error(str(e))
            raise

    async def start_job(self, start_url, headers):
        payload = {}
        new_headers = headers.copy()
        new_headers.update({"Content-Type": "application/json"})
        async with self.session.post(start_url, json=payload, headers=headers) as r:
            return r

    async def _upload_file(self, headers, file_name, working_dir, content):
        url = f"{working_dir}/files/{file_name}"
        payload = content
        new_headers = headers.copy()
        new_headers.update({"Content-Type": "application/json"})
        new_headers.update({"Accept": "application/octet-stream"})
        async with self.session.put(url, data=payload, headers=headers) as r:
            return r
