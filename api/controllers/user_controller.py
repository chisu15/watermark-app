from datetime import datetime
from oauthlib.oauth2 import WebApplicationClient
from requests import get, post
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from django.contrib.auth import logout as django_logout
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..models.user_model import User
import os
from google.oauth2 import id_token
from google.auth.transport import requests

class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    client = WebApplicationClient(os.getenv('GOOGLE_CLIENT_ID'))

    def get(self, request, *args, **kwargs):
        # Generate the Google login URL
        url = self.client.prepare_request_uri(
            "https://accounts.google.com/o/oauth2/auth",
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI'),
            scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        )
        return redirect(url)

class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            code = request.GET.get('code')
            if not code:
                return Response({'error': 'Code is missing from query parameters'}, status=400)

            client = WebApplicationClient(os.getenv('GOOGLE_CLIENT_ID'))

            # Exchange code for access token
            token_url, headers, body = client.prepare_token_request(
                "https://oauth2.googleapis.com/token",
                authorization_response=request.build_absolute_uri(),
                code=code
            )

            data = {
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI')
            }

            token_response = post(token_url, headers=headers, data=data)
            tokens = token_response.json()

            if 'id_token' not in tokens:
                return Response({'error': 'Failed to obtain ID token from Google'}, status=400)

            # Verify the ID token
            id_info = id_token.verify_oauth2_token(tokens['id_token'], requests.Request(), os.getenv('GOOGLE_CLIENT_ID'))

            # Find or create the user
            user = User.objects(google_id=id_info['sub']).first()

            if not user:
                # If user doesn't exist, create a new user
                user = User(
                    google_id=id_info['sub'],
                    email=id_info['email'],
                    username=id_info['name'],
                    profile_picture=id_info.get('picture'),
                    last_login_time=datetime.utcnow()
                )
            else:
                # Update user info if user exists
                user.email = id_info['email']
                user.username = id_info['name']
                user.profile_picture = id_info.get('picture')
                user.last_login_time = datetime.utcnow()

            user.save()
            # Set the token as a cookie (if required)
            response = redirect(os.getenv('GOOGLE_REDIRECT_URI_FE'))
            response.set_cookie('token', tokens.get('id_token'), httponly=True, secure=True, samesite='None')

            return response

        except Exception as error:
            print(f'Error in callback: {error}')
            return Response({'error': 'Callback failed', 'message': str(error)}, status=400)

class ProfileView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            # Lấy token từ cookie
            token = request.COOKIES.get('token')
            if not token:
                return Response({"detail": "Token not provided"}, status=status.HTTP_401_UNAUTHORIZED)

            # Verify token với Google
            idInfo = id_token.verify_oauth2_token(token, requests.Request(), os.getenv('GOOGLE_CLIENT_ID'))

            # Tìm người dùng bằng google_id từ payload
            user = User.objects.get(google_id=idInfo['sub'])
            data = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "profile_picture": user.profile_picture,
                "last_login_time": user.last_login_time,
            }
            return Response({
                "code": 200,
                "message": "Media file updated",
                "user": data
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        
class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            django_logout(request)
            response = Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)
            response.delete_cookie('token')  # Xóa cookie chứa token
        except Exception as error:
            response = Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        
        return response