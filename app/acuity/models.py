from django.db import models
from django.conf import settings

class AppointmentsQuerySet(models.query.QuerySet):
    def update_or_create(self, **kwargs):
        return super().update_or_create(**kwargs)

class AppointmentsManager(models.Manager):
    def get_queryset(self):
        return AppointmentsQuerySet(self.model)

class Appointments(models.Model):
    objects = AppointmentsManager()

    # Name of Requestor
    appt_id = models.BigIntegerField()
    name = models.CharField(max_length=255,null=False)
    phone = models.CharField(max_length=20)
    datetime = models.DateTimeField()
    appt_type = models.CharField(max_length=50)
    duration = models.IntegerField()
    node_id = models.IntegerField()
    address = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    cancel = models.BooleanField(default=False)
    private_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

