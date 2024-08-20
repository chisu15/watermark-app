from django.urls import path, include
from . import views
from .controllers.mediafile_controller import (
    Index,
    Delete,
    Detail,
    Edit,
    Create,
    ApplyWatermark
)
from .controllers.user_controller import GoogleLoginView, GoogleCallbackView, GoogleLogoutView


urlpatterns = [
    path('', views.api_overview, name='api-overview'),
    # MEDIAFILES
    path("mediafiles/", Index.as_view(), name="mediafile-index"),
    
    path("mediafiles/create", Create.as_view(), name="mediafile-create"),

    path("mediafiles/detail/<str:mediafile_id>", Detail.as_view(), name="mediafile-detail"),
    
    path("mediafiles/edit/<str:mediafile_id>", Edit.as_view(), name="mediafile-edit"),
    
    path("mediafiles/delete/<str:mediafile_id>", Delete.as_view(), name="mediafile-delete"),
    
    path("mediafiles/apply-watermark/<str:mediafile_id>", ApplyWatermark.as_view(), name="mediafile-apply-watermark"),
    # MEDIAFILES
    # AUTH
    path('auth/google/', GoogleLoginView.as_view(), name='google-login'),
    path('auth/google/callback/', GoogleCallbackView.as_view(), name='google-callback'),
    path('auth/google/logout/', GoogleLogoutView.as_view(), name='logout'),
    
    path('accounts/', include('allauth.urls')),
    # AUTH
]
