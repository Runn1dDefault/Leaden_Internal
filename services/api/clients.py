from json import JSONDecodeError
from typing import Any

from pyairtable import Api

from services.api.base import BaseAPIClient


class AirTableClient(Api):
    def schema(self, base_id: str):
        return self._request(method='GET', url=f'https://api.airtable.com/v0/meta/bases/{base_id}/tables')


class AirTableWebHooksClient(BaseAPIClient):
    base_url = 'https://api.airtable.com/v0/bases/{}'

    def __init__(self, base_id: str, oauth_token: str):
        super().__init__()
        self.base_id = base_id
        self.base_url = self.base_url.format(self.base_id) + '/'
        self._oauth_token = oauth_token

    def process_request(self, request) -> None:
        request.headers['Authorization'] = 'Bearer ' + self._oauth_token
        request.headers['Content-Type'] = 'application/json'

    @staticmethod
    def process_response(response) -> dict[str, Any] | list[dict[str, Any]] | None:
        if response.status_code in (200, 204):
            try:
                return response.json()
            except JSONDecodeError:
                return

        response.raise_for_status()

    def list_webhooks(self) -> dict:
        return self.send_request(method='GET', path='/webhooks')

    def create_webhook(self, notification_url: str, specification: dict[str, Any]) -> dict[str, str]:
        return self.send_request(method='POST', path='/webhooks',
                                 json={'notificationUrl': notification_url, 'specification': specification})

    def webhook_payloads(self, webhook_id: str, cursor: int = None, limit: int = None):
        assert cursor is None or cursor > 1
        assert limit is None or 0 < limit <= 50

        request_kwargs = dict()
        if cursor:
            request_kwargs['params'] = dict(cursor=cursor)

        if limit:
            limit_params = dict(limit=limit)

            if not request_kwargs.get('params'):
                request_kwargs['params'] = limit_params
            else:
                request_kwargs['params'].update(limit_params)

        return self.send_request(method='GET', path=f'/webhooks/{webhook_id}/payloads', **request_kwargs)

    def refresh_webhook(self, webhook_id: str) -> dict[str, str]:
        return self.send_request(method='POST', path=f'/webhooks/{webhook_id}/refresh')

    def notifications_enable(self, webhook_id: str, enable: bool) -> None:
        self.send_request(method='POST', path=f'/webhooks/{webhook_id}/enableNotifications', json={'enable': enable})

    def delete_webhook(self, webhook_id: str) -> None:
        self.send_request(method='DELETE', path=f'/webhooks/{webhook_id}')


class UpworkCustomAPI(BaseAPIClient):
    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
    base_url = 'https://www.upwork.com'

    def __init__(self, auth_token: str, master_token: str):
        super().__init__()
        self._auth_token = auth_token
        self._master_token = master_token

    @staticmethod
    def process_response(response) -> dict[str, Any] | list[dict[str, Any]]:
        if response.status_code == 200:
            return response.json()

        response.raise_for_status()

    def process_request(self, request) -> None:
        request.headers['user-agent'] = self.USER_AGENT
        request.headers['x-requested-with'] = 'XMLHttpRequest'

        if self._auth_token and self._master_token:
            request.headers['authorization'] = 'Bearer ' + self._auth_token
            request.headers['cookie'] = f'master_access_token={self._master_token};'


class UpworkJob(UpworkCustomAPI):
    JOB_DETAILS_PATH = '/job-details/jobdetails/api/job/{}/summary'

    def job_details(self, job_ciphertext: str) -> dict[str, Any]:
        path = self.JOB_DETAILS_PATH.format(job_ciphertext)
        return self.send_request('GET', path)
