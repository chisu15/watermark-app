from oauthlib.oauth2 import WebApplicationClient
from requests import get, post
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

    def get_token_and_userinfo(self, request):
        code = request.GET.get('code')

        # Prepare token request
        token_url, headers, body = self.client.prepare_token_request(
            "https://oauth2.googleapis.com/token",
            authorization_response=request.build_absolute_uri(),
            code=code  # Đảm bảo không truyền thêm `redirect_uri` ở đây
        )

        # Thêm `redirect_uri` vào payload token request sau khi chuẩn bị body
        body['redirect_uri'] = os.getenv('GOOGLE_REDIRECT_URI')

        # Request access token
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
        return userinfo_response.json()
