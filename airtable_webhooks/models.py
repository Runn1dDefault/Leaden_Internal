from django.db import models


class AirTableWebHook(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    base_id = models.CharField(max_length=25)
    webhook_id = models.CharField(max_length=25)
    cursor = models.IntegerField(default=1)
    table_name = models.CharField(max_length=250, unique=True)
    mac_secret = models.TextField()

    def update_cursor(self, cursor: int) -> None:
        if cursor != self.cursor:
            self.cursor = cursor
            self.save(update_fields=('cursor',))
