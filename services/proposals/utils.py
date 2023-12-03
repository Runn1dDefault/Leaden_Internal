import re
from urllib.parse import unquote


def search_job_ciphertext(some_text: str) -> str:
    match = re.search(r'~\w{18}', unquote(some_text))
    if match:
        return match.group()


def get_level_by_status(status: int) -> str:
    match status:
        case 1:
            return 'Entry Level'
        case 2:
            return 'Intermediate'
        case 3:
            return 'Expert'
        case _:
            return 'N/A'
