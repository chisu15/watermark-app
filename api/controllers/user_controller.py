from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from oauthlib.oauth2 import WebApplicationClient
import os
import requests

# Cấu hình Google OAuth2 client
client = WebApplicationClient(os.getenv('GOOGLE_CLIENT_ID'))

class GoogleLoginView(APIView):
    def get(self, request):
        # Tạo URL đăng nhập Google
        authorization_url, _ = client.prepare_authorization_request(
            "https://accounts.google.com/o/oauth2/auth",
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI'),
            scope=["openid", "email", "profile"],
        )
        return redirect(authorization_url)

class GoogleCallbackView(APIView):
    def get(self, request):
        code = request.GET.get("code")

        if not code:
            return Response({"error": "Code is missing"}, status=status.HTTP_400_BAD_REQUEST)

        # Lấy access token từ Google
        token_url, headers, body = client.prepare_token_request(
            "https://oauth2.googleapis.com/token",
            authorization_response=request.build_absolute_uri(),
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI'),
            code=code
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(os.getenv('GOOGLE_CLIENT_ID'), os.getenv('GOOGLE_CLIENT_SECRET')),
        )

        client.parse_request_body_response(token_response.text)

        # Lấy thông tin người dùng từ Google
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if userinfo_response.status_code == 200:
            userinfo = userinfo_response.json()
            # Trả về thông tin người dùng dưới dạng JSON
            return Response(userinfo, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to fetch user info"}, status=status.HTTP_400_BAD_REQUEST)

class GoogleLogoutView(APIView):
    def post(self, request):
        # Xử lý logout nếu cần, ví dụ xóa session
        return Response({"message": "Logged out"}, status=status.HTTP_200_OK)
