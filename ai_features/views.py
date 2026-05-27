from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login/')
def summary_view(request):
    return render(request, 'ai_features/summary.html')


@login_required(login_url='/login/')
def qna_view(request):
    return render(request, 'ai_features/qna.html')


@login_required(login_url='/login/')
def quiz_view(request):
    return render(request, 'ai_features/quiz.html')