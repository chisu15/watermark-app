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
        oauth_client = GoogleOAuthClient()
        oauth_client.get_access_token(request)
        userinfo = oauth_client.get_user_info()

        # Kiểm tra xem người dùng đã tồn tại chưa
        user = User.objects(email=userinfo["email"]).first()

        if not user:
            # Tạo người dùng mới nếu chưa tồn tại
            user = User(
                google_id=userinfo["id"],
                email=userinfo["email"],
                username=userinfo["name"],
                profile_picture=userinfo["picture"],
                last_login_time=datetime.utcnow()
            )
        else:
            # Cập nhật thông tin người dùng nếu đã tồn tại
            user.last_login_time = datetime.utcnow()
            user.profile_picture = userinfo["picture"]
            user.save()

        user.save()

        # Trả về thông tin người dùng
        return Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'profile_picture': user.profile_picture,
            'last_login_time': user.last_login_time
        }, status=status.HTTP_200_OK)

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
