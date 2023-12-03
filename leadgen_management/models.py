from django.db import models
from django.utils import timezone
from bulk_update_or_create import BulkUpdateOrCreateQuerySet


class BaseModel(models.Model):
    """
    This is the base model. All models will import this table to insert timestamp
    by default automatically.
    """

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name='Created Time',
    )
    modified_at = models.DateTimeField(
        auto_now_add=False,
        auto_now=True,
        db_index=True,
        verbose_name='Modified Time',
    )

    class Meta:
        abstract = True


class Projects(BaseModel):
    objects = BulkUpdateOrCreateQuerySet.as_manager()

    air_id = models.CharField(max_length=17, blank=True, null=True)
    shift = models.CharField(max_length=10, null=True)
    responsible = models.CharField(max_length=100, null=True, blank=True)
    proposal_added = models.DateTimeField(null=True, blank=True)
    url = models.TextField(unique=True)
    title = models.TextField(null=True, blank=True)
    relevant = models.TextField(null=True, blank=True)
    proposal = models.TextField(null=True, blank=True)
    cause = models.TextField(null=True, blank=True)
    missed = models.BooleanField(null=True, blank=True)
    comment_hol = models.TextField(null=True, blank=True)
    keyword = models.CharField(max_length=100, blank=True)
    approved_by_hol = models.BooleanField(null=True, blank=True)
    approval_time = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True)
    category = models.CharField(max_length=100, null=True)
    budget = models.IntegerField(null=True, blank=True)
    hourly = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    leadgen_comment = models.TextField(null=True, blank=True)
    project_type = models.CharField(max_length=30, null=True)

    def __str__(self):
        return f"ID {self.id}"

    class Meta:
        verbose_name = 'Projects'
        verbose_name_plural = 'Projects'


class Proposals(BaseModel):
    objects = BulkUpdateOrCreateQuerySet.as_manager()

    air_id = models.CharField(max_length=17, blank=True, null=True)
    url = models.TextField(unique=True)
    proposal_date = models.DateField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    shift = models.CharField(max_length=10, null=True, blank=True)
    proposal_owner = models.TextField(null=True, blank=True)
    sales_account = models.TextField(null=True, blank=True)
    relevant = models.CharField(max_length=10, null=True, blank=True)
    answer = models.BooleanField(default=False)
    answer_date = models.DateField(null=True, blank=True)
    client_name = models.TextField(null=True, blank=True)
    contract = models.BooleanField(default=False)
    contract_date = models.DateField(null=True, blank=True)
    hired = models.BooleanField(default=False)
    hired_date = models.DateField(null=True, blank=True)
    initial_interviews = models.IntegerField(null=True, blank=True)
    actual_interviews = models.IntegerField(null=True, blank=True)
    initial_proposals = models.TextField(null=True, blank=True)
    level = models.CharField(max_length=50, null=True, blank=True)
    length = models.CharField(max_length=100, null=True, blank=True)
    total_spent = models.IntegerField(null=True, blank=True)
    connects_spent = models.IntegerField(null=True, blank=True)
    cover_letter = models.TextField(null=True, blank=True)
    proposal_type = models.CharField(max_length=100, null=True, blank=True)
    project_type = models.CharField(max_length=50, null=True, blank=True)
    bid = models.IntegerField(null=True, blank=True)
    posted_jobs = models.IntegerField(null=True, blank=True)
    hires = models.IntegerField(null=True, blank=True)
    hire_rate = models.IntegerField(null=True, blank=True)
    member_since = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=200, null=True, blank=True)
    client_review = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    talent_type = models.TextField(null=True, blank=True)
    keyword = models.CharField(max_length=300, null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)
    initial_connects_required = models.IntegerField(null=True, blank=True)
    account_verified = models.BooleanField(default=False)
    outbid = models.BooleanField(default=False)
    mark = models.IntegerField(null=True, blank=True)
    no_link = models.BooleanField(default=False)
    job_removed = models.BooleanField(default=False)
    job_removed_date = models.DateField(null=True, blank=True)
    scraped = models.BooleanField(default=False)
    invalid_url = models.BooleanField(default=False)
    job_private = models.BooleanField(default=False)  # for 403
    industry_size = models.IntegerField(null=True, verbose_name='Company Employee Size')
    company_size = models.CharField(max_length=255, null=True, blank=True, verbose_name='Company Size')
    company_category = models.CharField(max_length=255, null=True, blank=True, verbose_name='Company Category')

    def __str__(self):
        return f"ID {self.id}"

    def save_invalid_url(self, job_removed: bool = None):
        self.invalid_url = True
        update_fields = {'invalid_url'}

        if job_removed is True:
            self.job_removed = job_removed
            self.job_removed_date = timezone.now().date()
            update_fields |= {'job_removed', 'job_removed_date'}

        self.save(update_fields=update_fields)

    class Meta:
        verbose_name = 'Proposals'
        verbose_name_plural = 'Proposals'


class DeclinedInvites(BaseModel):
    objects = BulkUpdateOrCreateQuerySet.as_manager()

    air_id = models.CharField(max_length=17, blank=True, null=True)
    url = models.TextField(unique=True)
    title = models.TextField(null=True, blank=True)
    invites_date = models.DateField(null=True, blank=True)
    responsible = models.CharField(max_length=100, null=True, blank=True)
    cause = models.TextField(null=True, blank=True)
    account = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    relevant = models.CharField(max_length=50, null=True, blank=True)
    created = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"ID {self.id}"

    class Meta:
        verbose_name = 'Declined Invites'
        verbose_name_plural = 'Declined Invites'


class Leads(BaseModel):
    objects = BulkUpdateOrCreateQuerySet.as_manager()

    air_id = models.CharField(max_length=17, blank=True, null=True)
    _id = models.IntegerField()
    client_name = models.CharField(max_length=200, null=True, blank=True)
    project_title = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    lead_owner = models.CharField(max_length=200, null=True, blank=True)
    created = models.DateField(null=True, blank=True)
    source = models.TextField(null=True, blank=True)
    assigned_sales = models.TextField(null=True, blank=True)
    contract = models.BooleanField(null=True, blank=True)
    contract_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"ID {self.id}"

    class Meta:
        verbose_name = 'Leads'
        verbose_name_plural = 'Leads'
