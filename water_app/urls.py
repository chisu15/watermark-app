from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


# Định nghĩa URL patterns
urlpatterns = [
    path('api/v1/', include('api.urls')),  # Đường dẫn tới các API trong ứng dụng của bạn
]
