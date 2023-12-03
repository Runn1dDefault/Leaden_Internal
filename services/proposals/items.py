from dataclasses import dataclass, asdict
from datetime import date

from services.proposals.utils import get_level_by_status


@dataclass
class ProposalsItem:
    project_type: str
    level: str | int
    account_verified: bool
    hired: bool = False
    length: str = 'N/A'
    member_since: date = None
    hired_date: date = None
    hire_rate: int = None
    actual_interviews: int = 0
    posted_jobs: int = 0
    hires: int = 0
    total_spent: int = 0
    client_review: float = None
    country: str = None
    job_removed: bool = False
    job_removed_date: date = None
    industry_size: int = None
    company_size: str = None
    company_category: str = 'N/A'

    def __post_init__(self):
        if isinstance(self.level, int):
            self.level = get_level_by_status(self.level)

    dict = asdict

    def set_company_size(self) -> None:
        if self.industry_size == 1:
            self.company_size = 'N/A'
        elif 2 <= self.industry_size <= 9:
            self.company_size = 'Small company (2-9 people)'
        elif 10 <= self.industry_size <= 99:
            self.company_size = 'Mid-sized company (10-99 people)'
        elif 100 <= self.industry_size <= 1000:
            self.company_size = 'Large company (100-1,000 people)'
        elif self.industry_size >= 1001:
            self.company_size = 'Corporation 1000+'
