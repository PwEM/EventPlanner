from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class AuthUser(AbstractUser):
    profile_image = models.ImageField(upload_to="users/", null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    @property
    def is_vendor(self):
        return self.groups.filter(name='Vendors').exists()
