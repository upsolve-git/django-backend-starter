from django.db import models
from . import constants
import datetime


class OrganizationTag(models.Model):
        tagId = models.AutoField(primary_key=True)
        organizationName = models.CharField()
        tagName = models.CharField(default="core", unique=True)
        expirationDate = models.DateField(default=datetime.date.today)





class UserDetails(models.Model):
    userId = models.AutoField(primary_key=True)
    first_Name = models.CharField(max_length=50)
    last_Name = models.CharField(max_length=50)
    phone_Number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    phoneNumber = models.CharField(null=False, default="0000000000")
    role = models.CharField(default=constants.USER)
    Password = models.CharField()
    tag = models.ForeignKey("OrganizationTag", to_field="tagId", null=True, on_delete=models.CASCADE, default=1)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    updated_at = models.DateTimeField(auto_now=True)
    isDeleted = models.BooleanField(default=False)
    blockedTimestamp = models.DateField(default=datetime.date.today)
    created_date = models.DateField()
    blocked = models.BooleanField()




    