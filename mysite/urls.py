from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # admin
    path('accounts/', include('allauth.urls')), #allauth
    path('', include('b04.urls')),  # home page  
]
