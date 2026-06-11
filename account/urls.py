from django.urls import path
from . import views

app_name = 'account'
urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('account-ready/', account_ready, name='account_ready'),
    path('logout/', logout_view, name='logout'),
]
