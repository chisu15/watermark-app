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

class GoogleOAuthController(APIView):
    permission_classes = [AllowAny]
    client = WebApplicationClient(os.getenv('GOOGLE_CLIENT_ID'))

    def get(self, request, *args, **kwargs):
        # Check if this is a login request or a callback
        if 'code' not in request.GET:
            return self.login(request)
        else:
            return self.callback(request)

    def login(self, request):
        # Generate the Google login URL
        url = self.client.prepare_request_uri(
            "https://accounts.google.com/o/oauth2/auth",
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI'),
            scope=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
        )
        return redirect(url)

    def callback(self, request):
        code = request.GET.get('code')

        # Request access token
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

        # Request user info
        uri, headers, body = self.client.add_token("https://www.googleapis.com/oauth2/v2/userinfo")
        userinfo_response = get(uri, headers=headers, data=body)

        userinfo = userinfo_response.json()

        # Check if user already exists
        user = User.objects(email=userinfo["email"]).first()

        if not user:
            # Create a new user if not exists
            user = User(
                google_id=userinfo["id"],
                email=userinfo["email"],
                username=userinfo["name"],
                profile_picture=userinfo["picture"],
                last_login_time=datetime.utcnow()
            )
        else:
            # Update user info if user exists
            user.last_login_time = datetime.utcnow()
            user.profile_picture = userinfo["picture"]
            user.save()

        user.save()

        # Return user info
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
