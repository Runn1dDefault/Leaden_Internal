from django.db import models


class UpworkAccount(models.Model):
    username = models.CharField(max_length=255, verbose_name='Username or Email', unique=True)
    password = models.CharField(max_length=255, verbose_name='Password')

    invalid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    @classmethod
    def add_invalid(cls, username: str) -> None:
        account = cls.objects.get(username=username)
        account.invalid = True
        account.save()
