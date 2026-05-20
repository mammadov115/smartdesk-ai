from django.urls import re_path

from .consumers import CustomerConsumer, OperatorConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<session_id>\d+)/$", CustomerConsumer.as_asgi()),
    re_path(r"ws/operator/chat/(?P<session_id>\d+)/$", OperatorConsumer.as_asgi()),
]
