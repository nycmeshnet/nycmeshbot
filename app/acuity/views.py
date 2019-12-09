import logging
import requests
import traceback
import dateutil.parser
import json

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import status
from django.conf import settings
from django.template.loader import render_to_string

from .models import Appointments
from .serializers import AcuityWebhookSerializer, AppointmentsSerializer
from lib.nycmeshapi import NYCMeshApi
import lib.slackapi as slackapi

logger = logging.getLogger(__name__)
meshapi = NYCMeshApi()


class CreateAppointmentView(generics.CreateAPIView):
    """
    POST acuity/
    """

    def post(self, request, *args, **kwargs):
        """Accepts and processes the inbound API Request
        Parameters
        ----------
        request : object
            This is the DRF Request object

        Returns
        -------
        Response
            HTTP Response with specified **kwargs
        """

        serializer = AcuityWebhookSerializer(data=request.data)
        if serializer.is_valid():
            logger.debug("Webhook data was valid")
            if 'HTTP_X_ACUITY_SIGNATURE' in request.META:
                logger.debug("Acuity Authorization Succeeded")
                action = serializer.validated_data['action']
                if action in ["scheduled", "canceled", "rescheduled", "changed"]:
                    if action == "scheduled":
                        logger.info(f"New Appointment Request: {serializer.validated_data}")
                        self._createAppointmentTask(serializer.validated_data)
                    else:
                        if action == "canceled":
                            logger.info(f"Cancel Appointment: {serializer.validated_data}")
                            self._updateAppointmentTask(serializer.validated_data, True)
                        else:
                            logger.info(f"Update Appointment: {serializer.validated_data}")
                            self._updateAppointmentTask(serializer.validated_data, False)
                    logger.debug("Return 200 OK")
                    return Response(
                        status=status.HTTP_200_OK
                    )
                else:
                    logger.debug(f"Acuity Webhook Action not valid. Return 200 OK to make the webhook detection at Acuity happy. Action was \"{action}\"")
                    return Response(
                        status=status.HTTP_200_OK
                    )
            else:
                logger.debug("Acuity Webhook Signature missing or incorrect. Return 401 Not Authorized")
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED
                )

        else:
            logger.debug(f"There were validation errors: {serializer.errors}. Return 400 BAD REQUEST")
            return Response(
                data={
                    "message": f"There were validation errors. {serializer.errors}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def _createAppointmentTask(self, serializer):
        """Handles the creation and Slack post of a newly scheduled Appointment
        Parameters
        ----------
        serializer : object
            Serializer Instance of AcuityWebhookSerializer

        Returns
        -------
        appt : object
            Model Instance of Appointment model
        """

        try:
            appt, meshapiJson = self._getApptById(serializer['id'])
            slackTemplate = render_to_string("acuity/acuity_slack.j2", {
                "appt": appt,
                "date": appt.datetime.strftime("%A, %B %d, %Y"),
                "time": appt.datetime.strftime("%I:%M %p"),
                "meshapi": meshapiJson}
            )
            logger.debug(slackTemplate)
            message = slackapi.post_to_channel(f"New {appt.appt_type}! - ID: {appt.appt_id}", settings.SLACK_CHANNEL, False, blocks=json.loads(slackTemplate))
            slackapi.pin_to_channel(message['channel'], message['ts'])
            return appt
        except Exception:
            traceback.print_exc()

    def _updateAppointmentTask(self, serializer, cancel):
        """Handles the update and Slack post of a rescheduled, changed, or cancelled Appointment
        Parameters
        ----------
        serializer : object
            Serializer Instance of AcuityWebhookSerializer
        cancel : bool
            Flag to cancel or not cancel an Appointment (default: False)

        Returns
        -------
        None
        """

        try:
            appt, meshapiJson = self._getApptById(serializer['id'], cancel)
            slackTemplate = render_to_string("acuity/acuity_slack.j2", {
                "appt": appt,
                "date": appt.datetime.strftime("%A, %B %d, %Y"),
                "time": appt.datetime.strftime("%I:%M %p"),
                "meshapi": meshapiJson}
            )
            pins = slackapi.get_pinned_messages(settings.SLACK_CHANNEL)
            for pinned in pins['items']:
                """
                if "channel" in pinned.keys():
                    messageChannel = pinned['channel']
                else:
                    messageChannel = None
                """
                messageText = pinned['message']['text']
                messageTS = pinned['message']['ts']
                if str(appt.appt_id) in messageText:
                    slackapi.edit_message(f"New {appt.appt_type}! - ID: {appt.appt_id}", settings.SLACK_CHANNEL, messageTS, blocks=json.loads(slackTemplate))
                    if appt.cancel:
                        slackapi.delete_pin(settings.SLACK_CHANNEL, messageTS)
        except Exception:
            traceback.print_exc()

    def _getApptById(self, appt_id, cancel=False):
        """Accepts and processes the inbound API Request
        Parameters
        ----------
        appt_id : int
            Acuity Appointment ID
        cancel : bool
            Flag to cancel or not cancel an Appointment (default: False)

        Returns
        -------
        appt : object
            Model Instance of Appointment model
        """

        try:
            logger.debug(f"Attempt to get existing Appointment from the db: appt_id={appt_id}")
            appt = Appointments.objects.get(appt_id=appt_id)
            logger.debug(f"Appointment from the db: {appt}")
            apptExists = True
        except Appointments.DoesNotExist:
            logger.debug("Appointment doesn't exist in db. Creating from Acuity")
            apptExists = False
        try:
            acuity = requests.get("https://acuityscheduling.com/api/v1/appointments/" + str(appt_id),
                                  auth=(settings.ACUITY_USER_ID, settings.ACUITY_API_KEY))
            acuityJson = acuity.json()
            logger.debug(f"Appointment data from Acuity: {acuityJson}")
            for form in acuityJson['forms']:
                for field in form['values']:
                    if field['name'] == "Node Number":
                        node_id = field['value']
                    elif field['name'] == "Request Number":
                        request_id = field['value']
                    elif field['name'] == "Address and Apartment #":
                        address = field['value']
                    elif field['name'] == "Notes":
                        notes = field['value']
            dateTime = dateutil.parser.parse(acuityJson['datetime'])

            if not node_id:
                logger.debug("Join Request Appointment")
                meshapiJson = meshapi.getRequest(request_id)
            else:
                logger.debug("Support Appointment")
                meshapiJson = meshapi.getNode(node_id)
            logger.debug(f"Node data from NYC Mesh API: {meshapiJson}")

            if apptExists:
                appt = appt
                appt.datetime = dateTime
                appt.appt_type = acuityJson['type']
                appt.duration = acuityJson['duration']
                appt.notes = notes.encode("unicode_escape").decode("utf-8")
                appt.private_notes = acuityJson['notes'].encode("unicode_escape").decode("utf-8")
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
                    'request_id': request_id if request_id else None,
                    'node_id': node_id if node_id else None,
                    'address': meshapiJson['building']['address'],
                    'notes': notes.encode("unicode_escape").decode("utf-8"),
                    'cancel': cancel,
                    'private_notes': acuityJson['notes'].encode("unicode_escape").decode("utf-8")
                }
                appt_serializer = AppointmentsSerializer(data=appt_data)

                if appt_serializer.is_valid(raise_exception=True):
                    logger.debug(f"Appointment validation complete")
                    appt = appt_serializer.save(**appt_data)
        except Exception:
            logging.exception("Trying to refresh Appointment has failed")
            traceback.print_exc()
        logger.debug(f"Appointment: {appt}")
        return (appt, meshapiJson)
