from django.urls import path
from . import views
from .controllers.mediafile_controller import (
    Index,
    IndexSticker,
    IndexBackground,
    Delete,
    Detail,
    Edit,
    Create,
    ApplyWatermark,
    GetListFont,
    GetListImage,
    GetListVideo,
    GetListPDF
)
from .controllers.user_controller import GoogleLoginView, GoogleCallbackView, ProfileView, LogoutView, GetTokenView

from .controllers.font_controller import FontIndex, FontDetail, FontCreate

urlpatterns = [
    path('', views.api_overview, name='api-overview'),
    # MEDIAFILES
    path("mediafiles/", Index.as_view(), name="mediafile-index"),
    path("mediafiles/sticker/", IndexSticker.as_view(), name="mediafile-index-sticker"),
    path("mediafiles/background/", IndexBackground.as_view(), name="mediafile-index-background"),
    path("mediafiles/create", Create.as_view(), name="mediafile-create"),

    path("mediafiles/detail/<str:mediafile_id>", Detail.as_view(), name="mediafile-detail"),
    
    path("mediafiles/edit/<str:mediafile_id>", Edit.as_view(), name="mediafile-edit"),
    
    path("mediafiles/delete/<str:mediafile_id>", Delete.as_view(), name="mediafile-delete"),
    
    path("mediafiles/font/", GetListFont.as_view(), name="mediafile-font"),
    path("mediafiles/image/", GetListImage.as_view(), name="mediafile-image"),
    path("mediafiles/video/", GetListVideo.as_view(), name="mediafile-video"),
    path("mediafiles/pdf/", GetListPDF.as_view(), name="mediafile-pdf"),
    
    path("mediafiles/apply-watermark/<str:mediafile_id>", ApplyWatermark.as_view(), name="mediafile-apply-watermark"),
    
    # MEDIAFILES
    # AUTH
    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),
    path('auth/google/callback/', GoogleCallbackView.as_view(), name='google_callback'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('auth/get-token/', GetTokenView.as_view(), name='get-token'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    # AUTH
    
    #FONT
    # path('font/', FontIndex.as_view(), name="font-index"),
    # path("font/create", FontCreate.as_view(), name="font-create"),

    # path("font/detail/<str:font_id>", FontDetail.as_view(), name="font-detail"),
    #FONT
]
