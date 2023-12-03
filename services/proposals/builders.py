from typing import Any

from dateutil.parser import parse
from django.utils import timezone
from django.conf import settings

from services.proposals.items import ProposalsItem


def build_proposals_item(job_details: dict[str, Any]) -> ProposalsItem:
    buyer = job_details.get('buyer')
    job_info = job_details.get('job')

    assert isinstance(buyer, dict), 'Not found key buyer or value is not a dict!'
    assert isinstance(job_info, dict), 'Not found key job or value is not a dict!'

    proposals_item = ProposalsItem(
        project_type='Hourly',
        level=job_info.get('contractorTier', 0),
        account_verified=buyer.get('isPaymentMethodVerified', False),
        length=job_info.get('durationLabel', 'N/A')
    )

    match job_info.get('extendedBudgetInfo'):
        case {
            'hourlyBudgetType': None,
            'hourlyBudgetMin': None,
            'hourlyBudgetMax': None
        }:
            proposals_item.project_type = 'Fixed'
            proposals_item.length = 'N/A'

    match job_info.get('clientActivity'):
        case {
            "totalInvitedToInterview": int() as total_interviews,
            "totalHired": int() as total_hired,
            **other_client_activity_fields
        } if total_hired > 0:
            proposals_item.hired = True
            proposals_item.hired_date = timezone.now().date()
            proposals_item.actual_interviews = total_interviews

    match buyer.get('jobs'):
        case {
            "postedCount": int() as total_jobs,
            **other_jobs_fields
        }:
            proposals_item.posted_jobs = total_jobs

    match buyer.get('stats'):
        case {
            "totalAssignments": int() as hires,
            "totalCharges": {
                "currencyCode": "USD",
                "amount": float() | int() as total_spent
            },
            "score": float() | int() as score,
            "totalJobsWithHires": int() as total_hires_jobs,
            **other_stats_fields
        }:
            proposals_item.hires = hires
            proposals_item.total_spent = total_spent
            proposals_item.client_review = score

            if total_hires_jobs == 0:
                proposals_item.hire_rate = 0
            elif total_hires_jobs > 0 and proposals_item.posted_jobs > 0:
                hire_rate = round((total_hires_jobs * 100) / proposals_item.posted_jobs)
                hire_rate = hire_rate if hire_rate <= 100 else 100
                proposals_item.hire_rate = hire_rate

    company_data = buyer.get('company', {})
    match company_data:
        case {
            "contractDate": str() as date_time_string,
            **other_company_fields,
        }:
            proposals_item.member_since = parse(date_time_string).date()

    profile_data = company_data.get('profile')
    match profile_data:
        case {"industry": str() as company_category, **other_fields} if company_category.strip():
            proposals_item.company_category = company_category

    match profile_data:
        case {"size": str() as industry_size, **other_fields} if industry_size.isdigit():
            proposals_item.industry_size = int(industry_size)
            proposals_item.set_company_size()
        case {"size": None, **other_fields}:
            proposals_item.company_size = 'N/A'

    match buyer.get('location'):
        case {
            "country": str() as client_country,
            **other_location_fields
        }:
            proposals_item.country = client_country

    if job_info.get("status", 0) in settings.JOB_UNAVAILABLE_STATUSES:
        proposals_item.job_removed = True
        proposals_item.job_removed_date = timezone.now().date()
    return proposals_item
