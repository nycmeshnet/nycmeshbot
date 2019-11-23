from rest_framework import serializers
from .models import Appointments

class AcuityWebhookSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    action = serializers.CharField(max_length=20)
    calendarID = serializers.IntegerField()
    appointmentTypeID = serializers.IntegerField()


class AppointmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointments
        fields = '__all__'
