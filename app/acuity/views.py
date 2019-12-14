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
                        else:
                            logger.info(f"Update Appointment: {serializer.validated_data}")
                        self._updateAppointmentTask(serializer.validated_data)
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
            appt, created, meshapiJson = Appointments.objects.update_and_retrieve(serializer['id'])
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
            logger.exception("Could not create new Appointment or post to slack")

    def _updateAppointmentTask(self, serializer):
        """Handles the update and Slack post of a rescheduled, changed, or cancelled Appointment
        Parameters
        ----------
        serializer : object
            Serializer Instance of AcuityWebhookSerializer

        Returns
        -------
        None
        """

        try:
            appt, created, meshapiJson = Appointments.objects.update_and_retrieve(serializer['id'])
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
            logger.exception("Could not update Appointment or post to slack")