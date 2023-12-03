import httpx
import time
import logging

logger = logging.getLogger('leadgen_management')


class Fetcher:

    def get_xml(self, feed_url: str, keyword: str, max_retries: int = 3, headers: dict = None) -> dict:
        response = self.get_http_response(url=feed_url, headers=headers, max_retries=max_retries)
        if response.get("response"):
            return {"xml": response['response'].text, "keyword": keyword}
        else:
            return response

    @staticmethod
    def get_http_response(url: str, headers: dict = None, max_retries: int = 3):
        retries = 0
        while retries < max_retries:
            response = httpx.get(url, headers=headers)
            if response.status_code == 200:
                return {"response": response}
            retries += 1
            time.sleep(0.5)
        logger.error(f"[ERROR] status code {response.status_code}")
        return {"error": f"[ERROR] status code {response.status_code}"}
