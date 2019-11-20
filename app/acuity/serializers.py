from rest_framework import serializers

class AcuityWebhookSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    action = serializers.CharField(max_length=20)
    calendarID = serializers.IntegerField()
    appointmentTypeID = serializers.IntegerField()
