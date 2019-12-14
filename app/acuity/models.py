import logging
import requests
import json
import dateutil.parser

from django.conf import settings
from django.db import models

from lib.nycmeshapi import NYCMeshApi

logger = logging.getLogger(__name__)
meshapi = NYCMeshApi()


class AppointmentsBaseManager(models.Manager):
    def retrieve_from_acuity(self, appt_id):
        """Simply returns the sanitized json of the Acuity API call"""
        acuity = requests.get("https://acuityscheduling.com/api/v1/appointments/" + str(appt_id),
                              auth=(settings.ACUITY_USER_ID, settings.ACUITY_API_KEY))
        acuityJson = acuity.json()
        logger.debug(f"Appointment data from Acuity: {acuityJson}")
        return self.__unify_key_values__(acuityJson)

    def __unify_key_values__(self, acuityJson):
        """Unified method to pluck only the needed keys from the Acuity API"""
        request_id = None
        node_id = None

        for form in acuityJson['forms']:
            for field in form['values']:
                if field['name'] == "Node Number":
                    node_id = field['value']
                elif field['name'] == "Request Number":
                    request_id = field['value']
                elif field['name'] == "Address and Apartment #":
                    address = field['value']
                elif field['name'] == "Notes":
                    notes = field['value'].encode("unicode_escape").decode("utf-8")
        dateTime = dateutil.parser.parse(acuityJson['datetime'])

        try:
            meshapiJson = meshapi.getRequest(node_id)
            if "installed" in meshapiJson['status']:
                raise self.model.DoesNotExist
        except self.model.DoesNotExist:
            logger.debug("Join Request didn't exist or was already installed. Checking nodedb instead.")
            meshapiJson = meshapi.getNode(node_id)

        logger.debug(f"Node data from NYC Mesh API: {meshapiJson}")

        appt = {
            'appt_id': acuityJson['id'],
            'name': acuityJson['firstName'] + " " + acuityJson['lastName'],
            'phone': acuityJson['phone'],
            'datetime': dateTime,
            'appt_type': acuityJson['type'],
            'duration': acuityJson['duration'],
            'request_id': request_id if request_id else None,
            'node_id': node_id if node_id else None,
            'address': meshapiJson['building']['address'],
            'notes': notes.encode("unicode_escape").decode("utf-8"),
            'cancel': acuityJson['canceled'],
            'private_notes': acuityJson['notes'].encode("unicode_escape").decode("utf-8")
        }

        return appt, meshapiJson

    def __update_and_retrieve_singleton__(self, **kwargs):
        """This little sucker will retrieve an appointment record from Acuity
           then attempt to update or create the local record
        """
        assert len(kwargs.keys())==2, \
                'update_and_retrieve() must be passed at one keyword argument'
        callback = kwargs.pop('callback', None)
        try:
            obj = self.get(**kwargs)
            if obj:
                appt, meshapiJson = self.retrieve_from_acuity(kwargs['appt_id'])
                obj.datetime = appt['datetime']
                obj.appt_type = appt['appt_type']
                obj.duration = appt['duration']
                obj.notes = appt['notes'].encode("unicode_escape").decode("utf-8")
                obj.private_notes = appt['private_notes'].encode("unicode_escape").decode("utf-8")
                obj.cancel = appt['cancel']
                obj.save()
                logger.debug(f"Appointment save complete")
            return obj, False, meshapiJson
        except self.model.DoesNotExist:
            logger.exception("Trying to refresh Appointment has failed. We didn't have it in the db")
            appt, meshapiJson = self.retrieve_from_acuity(kwargs['appt_id'])
            if callback:
                params = callback(appt)
            obj = self.model(**appt)
            obj.save()
            logger.debug(f"Appointment save complete")
            return obj, True, meshapiJson
        except IntegrityError as e:
            logger.exception("Seems there was an issue with saving the Appointment.")
            try:
                return self.get(**kwargs), False
            except self.model.DoesNotExist:
                raise e


class AppointmentsManager(AppointmentsBaseManager):
    """
    A Generic Appointments Manager which adds a retrieve functionality
    """
    def update_and_retrieve(self, appt_id):
        kwargs = { 'callback' : self.__apptProcess__ ,
                   'appt_id': appt_id }
        return self.__update_and_retrieve_singleton__(**kwargs)

    def __apptProcess__(self, args):
        if not 'appt_type' in args:
          raise self.model.DoesNotExist()
        return args


class Appointments(models.Model):
    objects = AppointmentsManager()

    appt_id = models.BigIntegerField()
    name = models.CharField(max_length=255, null=False)
    phone = models.CharField(max_length=20)
    datetime = models.DateTimeField()
    appt_type = models.CharField(max_length=50)
    duration = models.IntegerField()
    request_id = models.IntegerField(null=True)
    node_id = models.IntegerField(null=True)
    address = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    cancel = models.BooleanField(default=False)
    private_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
