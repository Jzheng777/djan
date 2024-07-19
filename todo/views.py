from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .serializers import UserSerializer, UserProfileSerializer
from .models import UserProfile

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Please provide all required fields.'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already taken.'}, status=400)

        user = User.objects.create_user(username=username, password=password)
        UserProfile.objects.create(user=user)  # Create a profile for the new user
        user.save()

        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            'message': 'User registered successfully.',
            'access': str(refresh.access_token),
        }, status=201)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                'access': str(refresh.access_token),
            }, status=200)
        else:
            return JsonResponse({'error': 'Invalid credentials.'}, status=400)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@csrf_exempt
@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserSerializer(user)
        profile_data = serializer.data
        profile = user.profile  # Access the profile object

        if profile:
            profile_data['profile']['profile_picture_base64'] = serializer.data['profile']['profile_picture_base64']
        else:
            profile_data['profile']['profile_picture_base64'] = None

        return Response({'profile': profile_data}, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        user_data = request.data.get('username')
        profile_data = request.data.get('profile')

        if user_data:
            user.username = user_data
            if request.data.get('password'):
                user.set_password(request.data.get('password'))

        # Update profile information
        profile = user.profile
        if profile:
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']

            if profile_data:
                profile_serializer = UserProfileSerializer(profile, data=profile_data, partial=True)
                if profile_serializer.is_valid():
                    profile_serializer.save()
                else:
                    return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Save the profile with the updated picture
                profile.save()
        else:
            return Response({'error': 'Profile does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        user.save()
        return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        todo = request.data.get('todo')
        if todo:
            profile = user.profile
            profile.todos.append(todo)
            profile.save()
            return Response({'message': 'Todo added successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        todo_index = request.data.get('index')
        if todo_index is not None:
            profile = user.profile
            if 0 <= todo_index < len(profile.todos):
                profile.todos.pop(todo_index)
                profile.save()
                return Response({'message': 'Todo removed successfully'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid index'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

