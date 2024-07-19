from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile
import base64

class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture_base64 = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['profile_picture_base64', 'todos']

    def get_profile_picture_base64(self, obj):
        if obj.profile_picture:
            with open(obj.profile_picture.path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        return None

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'profile']
