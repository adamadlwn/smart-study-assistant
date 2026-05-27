from django.urls import path
from . import views

app_name = 'account'
urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),# Define your account-related URL patterns here
]
