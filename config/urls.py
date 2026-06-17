from django.contrib import admin
from django.urls import path
from ai_features.views import summary_api, qna_api, quiz_api, quiz_answer_api

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
    path('logout/', logout_view, name='logout'),

    # Dashboard
    path('dashboard/', dashboard_view, name='dashboard'),

    # AI Features
    path('summary/', summary_view, name='summary'),
    path('qna/', qna_view, name='qna'),
    path('quiz/', quiz_view, name='quiz'),
    path('api/summary/', summary_api, name='summary_api'),
    path('api/qna/', qna_api, name='qna_api'),
    path('api/quiz/', quiz_api, name='quiz_api'),
    path('api/quiz-answer/', quiz_answer_api, name='quiz_answer_api'),

    # History API
    path('api/history/summary/<int:history_id>/', get_summary_history, name='get_summary_history'),
    path('api/history/qna/<int:history_id>/', get_qna_history, name='get_qna_history'),
    path('api/history/quiz/<int:history_id>/', get_quiz_history, name='get_quiz_history'),
]