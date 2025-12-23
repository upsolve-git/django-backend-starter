from django.db import models
from . import constants
from datetime import date, datetime


class OrganizationTag(models.Model):
        tagId = models.AutoField(primary_key=True)
        organizationName = models.CharField()
        tagName = models.CharField(default="core", unique=True)
        expirationDate = models.DateField(default=date.today) 





class UserDetails(models.Model):
    userId = models.AutoField(primary_key=True)
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phoneNumber = models.CharField(null=False, default="0000000000")
    role = models.CharField(default=constants.USER)
    encryptedPassword = models.CharField()
    tag = models.ForeignKey(
        "OrganizationTag", 
        to_field="tagId", 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(default=datetime.now)
    updated_at = models.DateTimeField(auto_now=True)
    isDeleted = models.BooleanField(default=False)
    blockedTimestamp = models.DateField(default=date.today)
    created_date = models.DateField(default=date.today)
    blocked = models.BooleanField()




    