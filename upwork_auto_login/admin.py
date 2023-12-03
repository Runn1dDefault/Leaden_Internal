from django.contrib import admin

from upwork_auto_login.models import UpworkAccount


@admin.register(UpworkAccount)
class UpworkAccountAdmin(admin.ModelAdmin):
    list_filter = ('invalid',)
    list_display = ('username', 'created_at')
    search_fields = ('username',)
