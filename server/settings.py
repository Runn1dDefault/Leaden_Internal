import os
from pathlib import Path

import dj_database_url
from decouple import config
from django.utils import timezone

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool)

# ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda ah: [h.strip() for h in ah.split(',')])
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    "https://leadgen.data-ox.com",
    "http://leadgen.data-ox.com/",
    "http://31.220.94.182:9010"
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_celery_beat',

    'leadgen_management',
    'upwork_auto_login',
    'airtable_webhooks',   # This app not used! Not tested!
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'server.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

POSTGRES_DB_CONNECTION_URL = dj_database_url.config(default=config('POSTGRES_DB_CONNECTION_URL'))

DATABASES = {
    'default': POSTGRES_DB_CONNECTION_URL
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'server_static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'server_static')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redis
REDIS_CONNECTION_URL = config('REDIS_DB_CONNECTION_URL')
DEFAULT_CACHES_REDIS_DB = int(config('DEFAULT_CACHES_REDIS_DB', 1))
UPWORK_TOKENS_REDIS_DB = int(config('UPWORK_TOKENS_REDIS_DB', 15))
AIRTABLE_WEBHOOKS_REDIS_DB = int(config('AIRTABLE_WEBHOOKS_REDIS_DB', 14))
PROJECTS_NOTIFICATION_REDIS_DB = int(config('PROJECTS_NOTIFICATION_REDIS_DB', 10))
PROPOSALS_NOTIFICATION_REDIS_DB = int(config('PROPOSALS_NOTIFICATION_REDIS_DB', 11))
PRIVATE_PROPOSALS_NOTIFICATION_REDIS_DB = int(config('PRIVATE_PROPOSALS_NOTIFICATION_REDIS_DB', 12))
AIRTABLE_USER_IDS_REDIS_DB = int(config('AIRTABLE_USER_IDS_REDIS_DB', 13))

UPWORK_TOKENS_CACHE_NAME = config('UPWORK_TOKENS_CACHE_NAME', 'upwork_tokens')
AIRTABLE_WEBHOOKS_CACHE_NAME = config('AIRTABLE_WEBHOOKS_CACHE_NAME', 'airtable_webhooks')

# Notifications caches
PROJECTS_NOTIFICATION_CACHE = config('PROJECTS_NOTIFICATION_CACHE', 'projects_notification')
PROPOSALS_NOTIFICATION_CACHE = config('PROJECTS_NOTIFICATION_CACHE', 'proposals_notification')
PRIVATE_PROPOSALS_NOTIFICATION_CACHE = config('PRIVATE_PROPOSALS_NOTIFICATION_CACHE', 'private_proposals_notification')
AIRTABLE_USER_IDS_CACHE = config('AIRTABLE_USER_IDS_CACHE', 'at_users_ids')

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CONNECTION_URL + '/%s' % DEFAULT_CACHES_REDIS_DB,
        # "KEY_FUNCTION": "server.utils.get_cache_key"
    },
    UPWORK_TOKENS_CACHE_NAME: {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CONNECTION_URL + '/%s' % UPWORK_TOKENS_REDIS_DB
    },
    AIRTABLE_WEBHOOKS_CACHE_NAME: {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CONNECTION_URL + '/%s' % AIRTABLE_WEBHOOKS_REDIS_DB
    },
    PROJECTS_NOTIFICATION_CACHE: {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CONNECTION_URL + '/%s' % PROJECTS_NOTIFICATION_REDIS_DB
    },
    PROPOSALS_NOTIFICATION_CACHE: {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CONNECTION_URL + '/%s' % PROPOSALS_NOTIFICATION_REDIS_DB
    },
    PRIVATE_PROPOSALS_NOTIFICATION_CACHE: {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CONNECTION_URL + '/%s' % PRIVATE_PROPOSALS_NOTIFICATION_REDIS_DB
    },
    AIRTABLE_USER_IDS_CACHE: {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_CONNECTION_URL + '/%s' % PRIVATE_PROPOSALS_NOTIFICATION_REDIS_DB
    }
}

# Celery
CELERY_BROKER_URL = REDIS_CONNECTION_URL + '/0'
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = REDIS_CONNECTION_URL + '/0'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers.DatabaseScheduler"

# AIRTABLE
AIRTABLE_TOKEN = config("AIRTABLE_TOKEN", None)
AIRTABLE_BASE_ID = config("AIRTABLE_BASE_ID", None)
MAX_RETRIES = int(config('AIRTABLE_RETRIES', 3))

AIRTABLE_FILTERS_TABLE_VIEW = config('AIRTABLE_FILTERS_TABLE_VIEW', "Grid view")
FILTERS_TABLE_NAME = config('FILTERS_TABLE_NAME', 'Filters')
PROPOSALS_TABLE_NAME = config('PROPOSALS_TABLE_NAME', 'Proposals')
LEADS_TABLE_NAME = config('LEADS_TABLE_NAME', 'Leads')
DECLINED_INVITES_TABLE_NAME = config('DECLINED_INVITES_TABLE_NAME', 'Declined Invites')
PROJECTS_TABLE_NAME = config('PROJECTS_TABLE_NAME', 'Projects')
PROPOSALS_PRIVATE_TABLE_NAME = config('PROPOSALS_PRIVATE_TABLE_NAME', 'Private Proposals')

MODELS_FIELDS_NAMES_MAP = {
    PROJECTS_TABLE_NAME: {
        "fields": {
            "air_id": "id",
            "id": "ID",
            "shift": "Shift",
            "responsible": "Responsible",
            "proposal_added": "Proposal Added",
            "url": "URL",
            "title": "Title",
            "relevant": "Relevant",
            "proposal": "Proposal",
            "cause": "Cause",
            "missed": "Missed",
            "comment_hol": "Comment HoL",
            "keyword": "Keyword",
            "approved_by_hol": "Approved by HoL",
            "approval_time": "Approval Time",
            "country": "Country",
            "category": "Category",
            "leadgen_comment": "Leadgen Comment",
            "project_type": "Project Type",
        },
        "exclude_database_fields": (
            "description", "budget", "hourly", "responsible", "approval_time", "proposal_added", "air_id"
        ),
        "exclude_airtable_fields": ("ID",)
    },
    PROPOSALS_TABLE_NAME: {
        "fields": {
            "air_id": "id",
            "url": "URL",
            "proposal_date": "Proposal Date",
            "title": "Title",
            "shift": "Shift",
            "proposal_owner": "Proposal Owner",
            "sales_account": "Sales Account",
            "relevant": "Relevant",
            "answer": "Answer",
            "answer_date": "Answer Date",
            "client_name": "Client Name",
            "hired": "Hired",
            "initial_interviews": "Initial # interviews",
            "initial_proposals": "Proposals",
            "connects_spent": "Connects Spent",
            "cover_letter": "Cover Letter",
            "proposal_type": "Proposal Type",
            "bid": "Bid",
            "talent_type": "Talent Type",
            "keyword": "Keyword",
            "created": "Created",
            "initial_connects_required": "Initial Connects Required",
            "mark": "Mark",
        }
    },
    DECLINED_INVITES_TABLE_NAME: {
        "fields": {
            "air_id": "id",
            "url": "URL",
            "title": "Title",
            "invites_date": "Invite's date",
            "responsible": "Responsible",
            "cause": "Cause",
            "account": "Account",
            "comment": "Comment",
            "relevant": "Relevant",
            "created": "Created",
        }
    },
    LEADS_TABLE_NAME: {
        "fields": {
            "air_id": "id",
            "_id": "ID",
            "project_title": "Project Title",
            "email": "Email",
            "phone": "Phone",
            "details": "Details",
            "lead_owner": "Lead Owner",
            "created": "Created",
            "source": "Source",
            "assigned_sales": "Assigned Sales",
            "client_name": "Client Name"
        }
    },
}

TASKS_HANDLER_MAP = {
    PROJECTS_TABLE_NAME: {
        "model": "leadgen_management.models.Projects",
        "fields": [
            "air_id",
            "url",
            "category",
            "title",
            "shift",
            "country",
            "proposal_added",
            "relevant",
            "responsible",
            "proposal",
            "cause",
            "leadgen_comment",
            "missed",
            "approved_by_hol",
            "comment_hol",
            "project_type",
            "approval_time",
        ],
        "match_field": "url"
    },
    PROPOSALS_TABLE_NAME: {
        "model": "leadgen_management.models.Proposals",
        "fields": [
            "air_id",
            "url",
            "proposal_date",
            "title",
            "shift",
            "proposal_owner",
            "sales_account",
            "relevant",
            "answer",
            "answer_date",
            "client_name",
            "hired",
            "initial_interviews",
            "connects_spent",
            "cover_letter",
            "proposal_type",
            "bid",
            "talent_type",
            "keyword",
            "created",
            "initial_connects_required",
            "mark",
            "initial_proposals",
        ],
        "match_field": "url"
    },
    DECLINED_INVITES_TABLE_NAME: {
        "model": "leadgen_management.models.DeclinedInvites",
        "fields": [
            "air_id",
            "url",
            "title",
            "invites_date",
            "responsible",
            "cause",
            "account",
            "comment",
            "relevant",
            "created",
        ],
        "match_field": "url"
    },
    LEADS_TABLE_NAME: {
        "model": 'leadgen_management.models.Leads',
        "fields": [
            "air_id",
            "_id",
            "project_title",
            "email",
            "phone",
            "details",
            "lead_owner",
            "created",
            "source",
            "assigned_sales",
            "client_name"
        ],
        "match_field": "_id"
    },
}

AIRTABLE_PROPOSALS_TABLE_FIELDS = {
    'Client Name': 'client_name',
    'Answer Date': 'answer_date',
    'URL': 'url',
    'Title': 'title',
    'Relevant': 'relevant',
    "Mark": "mark",
    "Answer": 'answer',
    "Proposal Date": "proposal_date",
    "Initial # interviews": 'initial_interviews',
    "Proposal Owner": {'name': 'proposal_owner'},
    "Shift": "shift",
    "Proposals": "initial_proposals",
    "Created": "created",
    "Hired": 'hired',
    "Sales Account": "sales_account",
    "Connects Spent": "connects_spent",
    "Cover Letter": "cover_letter",
    "Proposal Type": {"name": "proposal_type"},
    "Bid": "bid",
    "Talent Type": "talent_type",
    "Keyword": "keyword",
    "Initial Connects Required": "initial_connects_required"
}
AIRTABLE_LEADS_TABLE_FIELDS = {
    'ID': '_id',
    'Client Name': 'client_name',
    'Project Title': 'project_title',
    'Email': 'email',
    'Phone': 'phone',
    "Details": "details",
    "Lead Owner": {'name': 'lead_owner'},
    "Source": "source",
    'Assigned Sales': 'assigned_sales'
}
AIRTABLE_DECLINED_INVITES_TABLE_FIELDS = {
    'URL': 'url',
    'Title': 'title',
    "Invite's date": 'invites_date',
    'Responsible': {'name': 'responsible'},
    "Comment": "comment",
    "Relevant": 'relevant',
    "Created": "created",
    "Cause": "cause",
    "Account": "account"
}
AIRTABLE_PROJECTS_TABLE_FIELDS = {
    'Shift': 'shift',
    'URL': 'url',
    'Title': 'title',
    'Comment HoL': 'comment_hol',
    'Keyword': 'keyword',
    'Country': 'country',
    'Category': 'category',
    'Project Type': 'project_type',
    'Proposal Added': 'proposal_added',
    'Approval Time': 'approval_time',
    'Relevant': 'relevant',
    'Responsible': {'name': 'responsible'},
    'Proposal': 'proposal',
    'Cause': 'cause',
    'Leadgen Comment': 'leadgen_comment',
    'Missed': 'missed',
    'Approved by HoL': 'approved_by_hol'
}

PRIVATE_JOB_REMOVED_FIELD = config("PRIVATE_JOB_REMOVED_FIELD", "Removed")
AIRTABLE_PRIVATE_PROPOSALS_TABLE_FIELDS = {
    'URL': 'url',
    "Responsible": {'name': 'proposal_owner'},
    "Project Type": "project_type",
    "Level": "level",
    "Length": "length",
    "Posted Jobs": "posted_jobs",
    "Hires": "hires",
    "Hire Rate": "hire_rate",
    "Total Spent": "total_spent",
    "Client Review": "client_review",
    "Country": "country",
    "Member Since": "member_since",
    "Account Verified": "account_verified",
    PRIVATE_JOB_REMOVED_FIELD: "job_removed",
    "Hired": "hired",
    "Hired Date": "hired_date",
    "Company Category": "company_category",
    "Company Size": "company_size"
}

# UPWORK XML scraping
HEADERS = {
    "accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
}
SUMMARY_TAGS = {
    "hourly_range": "<b>Hourly Range</b>",
    "budget": "<b>Budget</b>",
    "posted_on": "<b>Posted On</b>",
    "category": "<b>Category</b>",
    "skills": "<b>Skills</b>",
}
TEXT_TO_CLEAN = {
    "projects": {
        "xml_symbols_to_clean": ('quot;', '<br /><br />', '<.*?>', '&.*?;', r'\n&middot;', '- Upwork', 'amp;'),
        "xml_fields_to_replace": ("<b>Category</b>: ", "<b>Category</b>:", "<b>Country</b>: ", "<b>Country</b>:")
    }
}

FIELDS_TO_DATE_FORMAT = ("Created", "Answer Date", "Proposal Added", "Proposal Date", "Approval Time")
FIELDS_BOOLEAN_TYPE = ("Missed", "Approved by HoL", "Answer", "Hired")

# Proposals scraping
PROPOSALS_BACK_WATCH_UPDATE_MINUTES = int(config("PROPOSALS_BACK_WATCH_UPDATE_MINUTES", 5))
UPWORK_SCRAPING_RETRIES = int(config('PROPOSALS_SCRAPING_RETRIES', 3))
JOB_UNAVAILABLE_STATUSES = (2, 3,)
AIRTABLE_PROPOSALS_DONT_UPDATE_FIELDS = ('Created', 'Contract Date', 'Proposal Owner',)
PROPOSALS_SCRAPING_REQUIRED_FIELDS = (
    'project_type',
    'level',
    'length',
    'member_since',
    'actual_interviews',
    'hire_rate',
    'hires',
    'total_spent',
    'client_review',
    'posted_jobs',
    'country',
)
PROPOSALS_UPDATE_FIELDS = ('hired', 'actual_interviews')
CODES_TO_REMOVE_TOKENS = (401, 412, 429, 301,)

# Upwork Auto login
UPWORK_AUTH_URL = config('UPWORK_AUTH_URL', 'https://www.upwork.com/ab/account-security/login')
UPWORK_WAIT_AFTER_LOGIN_XPATH = config('UPWORK_WAIT_AFTER_LOGIN_XPATH', 'xpath=//*[@class="nav-user-info"]')
UPWORK_LOGIN_RETRIES = int(config('UPWORK_LOGIN_RETRIES', 5))
UPWORK_LOGIN_WAIT_FOR_PAGE_SECONDS = int(config('UPWORK_LOGIN_WAIT_FOR_NEXT_SECONDS', 5))
UPWORK_GOOGLE_NEXT_BTN_TEXT = config('UPWORK_GOOGLE_NEXT_BTN_TEXT', 'Next')
UPWORK_AUTH_COOKIE_KEY = config('UPWORK_AUTH_COOKIE_KEY', 'oauth2_global_js_token')
UPWORK_MASTER_COOKIE_KEY = config('UPWORK_MASTER_COOKIE_KEY', 'master_access_token')
UPWORK_COOKIES_NAME_KEY = config('UPWORK_COOKIES_NAME_KEY', 'name')
UPWORK_COOKIES_VALUE_KEY = config('COOKIES_VALUE_KEY', 'value')
UPWORK_TOKENS_EXPIRES_SECONDS = int(config('TOKENS_EXPIRES_SECONDS', 18000))  # default 5 hours

# AIRTABLE WEBHOOKS
AIRTABLE_WEBHOOKS_TABLES_SETTINGS = {
    PROPOSALS_TABLE_NAME: {
        'table_id': config('PROPOSALS_TABLE_ID', 'tblkWz5GMdpX7mC1n'),
        'fields': AIRTABLE_PROPOSALS_TABLE_FIELDS,
        'model': 'leadgen_management.models.Proposals'
    },
    LEADS_TABLE_NAME: {
        'table_id': config('LEADS_TABLE_ID', 'tblBzBlPPRPnjkZIU'),
        'fields': AIRTABLE_LEADS_TABLE_FIELDS,
        'model': 'leadgen_management.models.Leads'
    },
    DECLINED_INVITES_TABLE_NAME: {
        'table_id': config('DECLINED_INVITES_TABLE_ID', 'tblFaNSWTnfq9RzOp'),
        'fields': AIRTABLE_DECLINED_INVITES_TABLE_FIELDS,
        'model': 'leadgen_management.models.DeclinedInvites'
    },
    PROJECTS_TABLE_NAME: {
        'table_id': config('PROJECTS_TABLE_ID', 'tbl1QfinjooIp3bv1'),
        'fields': AIRTABLE_PROJECTS_TABLE_FIELDS,
        'model': 'leadgen_management.models.Projects'
    },
}

# Slack
SLACK_BOT_TOKEN = config('SLACK_BOT_TOKEN')
SLACK_CHANNEL_ID = config('SLACK_CHANNEL_ID')
ERROR_MSG_SNIPPED = {
    "message": "Error",
    "details": [],
    "error_time_utc": timezone.now().utcnow(),
    "links": []
}

SLACK_LEVELS = {
    # level: smile
    'info': ':information_source:',
    'error': ':exclamation:',
    'warning': ':warning:',
    'critical': ':broken_heart:'
}


# Logging
MONGO_DB_CONNECTION_URL = config('MONGO_DB_CONNECTION_URL')
LOG_MONGO_DATABASE_NAME = config('LOG_MONGO_DATABASE_NAME')
LOG_MONGO_COLLECTION_NAME = config('LOG_MONGO_COLLECTION_NAME')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'console': {
            'format': '%(levelname)s | %(asctime)s | %(module)s | %(message)s'
        }
    },
    'handlers': {
        'mongolog': {
            'level': 'INFO',
            'class': 'mongo_logger.handlers.CustomMongoLogHandler',
            'connection': MONGO_DB_CONNECTION_URL,
            'collection': LOG_MONGO_COLLECTION_NAME,
            'database': LOG_MONGO_DATABASE_NAME
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        '': {
            'handlers': ['mongolog', 'console'],
            'level': 'INFO',
            'propagate': True
        },
        'leadgen_management': {
            'handlers': ['mongolog', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'django': {
            'handlers': ['console', 'mongolog'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console', 'mongolog'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'mongolog'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['mail_admins', 'console', 'mongolog'],
            'level': 'ERROR',
            'propagate': False,
        }
    },
}
