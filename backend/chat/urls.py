from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .django_chat_api import ChatSessionViewSet, ChatHealthView

app_name = 'chat'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'sessions', ChatSessionViewSet, basename='session')

urlpatterns = [
    # API endpoints
    path('api/chat/', include(router.urls)),
    path('api/chat/health/', ChatHealthView.as_view(), name='health'),
    
    # Optional: Traditional Django views (if needed)
    # path('', views.index, name='index'),
]