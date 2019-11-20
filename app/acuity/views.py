from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import status

#from .models import Appointments
from .serializers import AcuityWebhookSerializer

class CreateAppointmentView(generics.CreateAPIView):
    """
    POST acuity/
    """

    def post(self, request, *args, **kwargs):
        serializer = AcuityWebhookSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                data=AcuityWebhookSerializer(request.data).data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                data={
                    "message": "There were validation errors. {0}".format(serializer.errors)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
