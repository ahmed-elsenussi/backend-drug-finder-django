from rest_framework import serializers
from .models import Review

# REVIEW SERLIALIZER
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'