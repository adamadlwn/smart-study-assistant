from django.contrib import admin
from django.urls import path

from account.views import *
from dashboard.views import *
from ai_features.views import *

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('', dashboard_view, name='home'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('account-ready/', account_ready, name='account_ready'),

    # Dashboard
    path('dashboard/', dashboard_view, name='dashboard'),

    # AI Features
    path('summary/', summary_view, name='summary'),
    path('qna/', qna_view, name='qna'),
    path('quiz/', quiz_view, name='quiz'),
]