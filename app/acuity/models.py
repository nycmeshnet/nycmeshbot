from django.db import models

class Appointments(models.Model):
    # Name of Requestor
    name = models.CharField(max_length=255,null=False)
    phone = models.CharField(max_length=20)
    datetime = models.DateTimeField()
    appt_type = models.CharField(max_length=50)
    duration = models.IntegerField()
    node_number = models.IntegerField()
    address = models.CharField(max_length=255)
    notes = models.TextField()
    cancel = models.BooleanField(default=False)
    private_notes = models.TextField()

