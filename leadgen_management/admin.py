from django.contrib import admin

from leadgen_management.models import Projects, Proposals, Leads, DeclinedInvites
from leadgen_management.utils import model_verbose_fields


class ProjectAdmin(admin.ModelAdmin):
    list_per_page = 30
    list_display = ('title', 'keyword', 'category', 'project_type', 'created_at')
    search_fields = (
        'url',
        'title',
        'responsible',
        'comment_hol',
        'description',
        'country',
        'category',
        'budget',
        'hourly',
        'leadgen_comment'
    )
    search_help_text = "search by fields %s" % ', '.join(model_verbose_fields(Projects, search_fields))
    list_filter = (
        'missed',
        'relevant',
        'shift',
        'keyword',
        'project_type',
        'proposal',
        'cause',
        'approved_by_hol',
        'approval_time',
        'proposal_added',
    )


class LeadsAdmin(admin.ModelAdmin):
    list_per_page = 30
    list_display = ('_id', 'client_name', 'project_title', 'lead_owner', 'created', 'contract')
    search_fields = (
        '_id',
        'client_name',
        'project_title',
        'email',
        'phone',
        'details',
        'lead_owner',
    )
    search_help_text = "search by fields %s" % ', '.join(model_verbose_fields(Leads, search_fields))
    list_filter = (
        'contract',
        'source',
        'assigned_sales',
        'created',
        'contract_date',
    )


class DeclinedInvitesAdmin(admin.ModelAdmin):
    list_per_page = 30
    list_display = ('title', 'account', 'responsible', 'created', 'invites_date', 'relevant')
    search_fields = (
        'url',
        'title',
        'responsible',
        'account',
        'comment',
    )
    search_help_text = "search by fields %s" % ', '.join(model_verbose_fields(DeclinedInvites, search_fields))
    list_filter = (
        'cause',
        'relevant',
        'invites_date',
        'created',
    )


class ProposalsAdmin(admin.ModelAdmin):
    list_per_page = 30
    list_display = ('title', 'proposal_owner', 'client_name', 'sales_account', 'keyword', 'answer')
    search_fields = (
        'url',
        'title',
        'proposal_owner',
        'sales_account',
        'client_name',
        'initial_proposals',
        'cover_letter',
        'country',
        'talent_type',
        'keyword',
        'level',
        'length',
        'country',
    )
    search_help_text = "search by fields %s" % ', '.join(model_verbose_fields(Proposals, search_fields))
    list_filter = (
        'relevant',
        'answer',
        'contract',
        'hired',
        'account_verified',
        'no_link',
        'job_removed',
        'outbid',
        'proposal_type',
        'shift',
        'keyword',
        'created',
        'member_since',
        'hired_date',
        'answer_date',
        'contract_date',
        'proposal_date',
        'job_removed_date',
        'scraped',
        'invalid_url',
        'company_size'
    )


admin.site.register(Projects, ProjectAdmin)
admin.site.register(Leads, LeadsAdmin)
admin.site.register(DeclinedInvites, DeclinedInvitesAdmin)
admin.site.register(Proposals, ProposalsAdmin)
