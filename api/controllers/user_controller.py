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
from .google_oauth_client import GoogleOAuthClient

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

            # Thay vì chỉnh sửa trực tiếp 'body', ta xây dựng thủ công request data
            data = {
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI_FE')
            }

            token_response = post(token_url, headers=headers, data=data)
            tokens = token_response.json()

            client.parse_request_body_response(token_response.text)

            # Verify the ID token
            uri, headers, body = client.add_token("https://www.googleapis.com/oauth2/v2/userinfo")
            userinfo_response = get(uri, headers=headers, data=body)
            userinfo = userinfo_response.json()

            # Find or create the user
            user, created = User.objects.update_or_create(
                google_id=userinfo['id'],
                defaults={
                    'email': userinfo['email'],
                    'username': userinfo['name'],
                    'profile_picture': userinfo['picture'],
                    'last_login_time': datetime.utcnow()
                }
            )

            # Set the token as a cookie (if required)
            response = redirect('/profile')
            response.set_cookie('token', tokens.get('id_token'), httponly=True, secure=True, samesite='None')

            return response

        except Exception as error:
            print(f'Error in callback: {error}')
            return Response({'error': 'Callback failed', 'message': str(error)}, status=400)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            user_profile = User.objects.get(email=user.email)
            data = {
                "id": str(user_profile.id),
                "username": user_profile.username,
                "email": user_profile.email,
                "profile_picture": user_profile.profile_picture,
                "last_login_time": user_profile.last_login_time,
            }
            return Response(data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        django_logout(request)
        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)
