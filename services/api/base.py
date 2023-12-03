from typing import Any
from urllib.parse import urljoin

from httpx import Client, Response, Request


class BaseAPIClient:
    base_url: str

    def __init__(self):
        self.client = Client()

    def process_request(self, request: Request) -> None:
        pass

    @staticmethod
    def process_response(response: Response) -> dict[str, Any] | list[dict[str, Any]]:
        pass

    def send_request(self, method: str, path: str = None, **kwargs) -> dict[str, Any] | list[dict[str, Any]]:
        if path.startswith('/'):
            path = path[1:]

        request = self.client.build_request(method, urljoin(self.base_url, path), **kwargs)
        self.process_request(request)
        response = self.client.send(request)
        return self.process_response(response)
