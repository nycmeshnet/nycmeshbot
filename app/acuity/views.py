from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import status
from django.conf import settings
from django.template.loader import render_to_string

from .models import Appointments
from .serializers import AcuityWebhookSerializer, AppointmentsSerializer
import lib.slackapi as slackapi

import requests, sys, traceback, dateutil.parser

class CreateAppointmentView(generics.CreateAPIView):
    """
    POST acuity/
    """

    def post(self, request, *args, **kwargs):
        serializer = AcuityWebhookSerializer(data=request.data)
        if serializer.is_valid():
            if 'HTTP_X_ACUITY_SIGNATURE' in request.META:
                action = serializer.validated_data['action']
                if action in ["scheduled","canceled","rescheduled","changed"]:
                    if action == "scheduled":
                        createAppt = self._createAppointmentTask(serializer.validated_data)
                    else:
                        cancel = True if action == "canceled" else False
                        updateAppt = self._updateAppointmentTask(serializer.validated_data, cancel)
                    return Response(
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        status=status.HTTP_200_OK
                    )
            else:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED
                )

        else:
            return Response(
                data={
                    "message": "There were validation errors. {0}".format(serializer.errors)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def _createAppointmentTask(self, serializer):
        try:
            appt = self._getApptById(serializer['id'])
            slackTemplate = render_to_string("acuity/acuity_slack.j2", 
                    { 
                        "appt": appt,
                        "date": appt.datetime.strftime("%A, %B %d, %Y"),
                        "time": appt.datetime.strftime("%I:%M %p")
                    }
                )
            message = slackapi.post_to_channel(slackTemplate, settings.SLACK_CHANNEL, False)
            pin = slackapi.pin_to_channel(message['channel'], message['ts'])
            return appt
        except:
            traceback.print_exc()

    def _updateAppointmentTask(self, serializer, cancel):
        try:
            appt = self._getApptById(serializer['id'], cancel)
            slackTemplate = render_to_string("acuity/acuity_slack.j2", 
                    { 
                        "appt": appt,
                        "date": appt.datetime.strftime("%A, %B %d, %Y"),
                        "time": appt.datetime.strftime("%I:%M %p")
                    }
                )
            pins = slackapi.get_pinned_messages(settings.SLACK_CHANNEL)
            for pinned in pins['items']:
                if "channel" in pinned.keys():
                    messageChannel = pinned['channel']
                else:
                    messageChannel = None
                messageText = pinned['message']['text']
                messageTS = pinned['message']['ts']
                if str(appt.appt_id) in messageText:
                    message = slackapi.edit_message(slackTemplate, settings.SLACK_CHANNEL, messageTS)
                    #print(message)
                    if appt.cancel:
                        slackapi.delete_pin(settings.SLACK_CHANNEL, messageTS)
        except:
            traceback.print_exc()

    def _getApptById(self, appt_id, cancel=False):
        try:
            appt = Appointments.objects.get(appt_id=appt_id)
            apptExists = True
        except Appointments.DoesNotExist:
            print("Appointment doesn't exist in db. Creating from Acuity")
            apptExists = False
        try:
            acuity = requests.get("https://acuityscheduling.com/api/v1/appointments/" + str(appt_id),
                                auth=(settings.ACUITY_USER_ID, settings.ACUITY_API_KEY),
                                )
            acuityJson = acuity.json()
            for form in acuityJson['forms']:
                for field in form['values']:
                    if field['name'] == "Node Number":
                        node_id = field['value']
                    elif field['name'] == "Address and Apartment #":
                        address = field['value']
                    elif field['name'] == "Notes":
                        notes = field['value']
            dateTime = dateutil.parser.parse(acuityJson['datetime'])

            meshapi = requests.get("https://api.nycmesh.net/v1/nodes/"+ node_id)
            meshapiJson = meshapi.json()

            if apptExists:
                appt = appt
                appt.datetime = dateTime
                appt.appt_type = acuityJson['type']
                appt.duration = acuityJson['duration']
                appt.notes = notes
                appt.private_notes = acuityJson['notes']
                appt.cancel = cancel
                appt.save()
                appt = appt
            else:
                appt_data = {
                    'appt_id': acuityJson['id'],
                    'name': acuityJson['firstName'] + " " + acuityJson['lastName'],
                    'phone': acuityJson['phone'],
                    'datetime': dateTime,
                    'appt_type': acuityJson['type'],
                    'duration': acuityJson['duration'],
                    'node_id': node_id,
                    'address': meshapiJson['location'],
                    'notes': notes,
                    'cancel': cancel,
                    'private_notes': acuityJson['notes'] 
                }
                appt_serializer = AppointmentsSerializer(data=appt_data)

                if appt_serializer.is_valid(raise_exception=True):
                    appt = appt_serializer.save(**appt_data)
        except:
            traceback.print_exc()
        return appt
