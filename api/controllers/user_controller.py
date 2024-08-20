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

class GoogleOAuthClient:
    def __init__(self):
        self.client = WebApplicationClient(os.getenv('GOOGLE_CLIENT_ID'))

    def get_login_url(self):
        return self.client.prepare_request_uri(
            "https://accounts.google.com/o/oauth2/auth",
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI'),
            scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        )

    def fetch_token(self, request):
        code = request.GET.get('code')
        token_url, headers, body = self.client.prepare_token_request(
            "https://oauth2.googleapis.com/token",
            authorization_response=request.build_absolute_uri(),
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI'),
            code=code
        )
        token_response = post(
            token_url,
            headers=headers,
            data=body,
            auth=(os.getenv('GOOGLE_CLIENT_ID'), os.getenv('GOOGLE_CLIENT_SECRET')),
        )
        self.client.parse_request_body_response(token_response.text)

    def fetch_user_info(self):
        uri, headers, body = self.client.add_token("https://www.googleapis.com/oauth2/v2/userinfo")
        userinfo_response = get(uri, headers=headers, data=body)
        return userinfo_response.json()


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        oauth_client = GoogleOAuthClient()
        login_url = oauth_client.get_login_url()
        return redirect(login_url)


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            oauth_client = GoogleOAuthClient()
            oauth_client.fetch_token(request)
            userinfo = oauth_client.fetch_user_info()

            user = User.objects(email=userinfo["email"]).first()
            if not user:
                user = User(
                    google_id=userinfo["id"],
                    email=userinfo["email"],
                    username=userinfo["name"],
                    profile_picture=userinfo["picture"],
                    last_login_time=datetime.utcnow()
                )
            else:
                user.last_login_time = datetime.utcnow()
                user.profile_picture = userinfo["picture"]

            user.save()

            return Response({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'profile_picture': user.profile_picture,
                'last_login_time': user.last_login_time
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Callback failed", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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


class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            user_profile = User.objects.get(email=user.email)
            user_profile.username = request.data.get("username", user_profile.username)
            user_profile.save()
            return Response({"detail": "Profile updated"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        django_logout(request)
        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)
