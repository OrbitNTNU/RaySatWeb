# In groundstation/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/latest-data/', views.get_latest_data, name='latest_data'),
    path('api/historical-data/', views.get_historical_data, name='historical_data'),
    path('api/send-command/', views.send_command, name='send_command'),
]

