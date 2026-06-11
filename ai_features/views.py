import os
import json
import google.generativeai as genai
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# Konfigurasi Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')


@login_required(login_url='/login/')
def summary_view(request):
    return render(request, 'summary.html')


@login_required(login_url='/login/')
def qna_view(request):
    return render(request, 'ai_features/qna.html')


@login_required(login_url='/login/')
def quiz_view(request):
    return render(request, 'ai_features/quiz.html')


@login_required(login_url='/login/')
def summary_api(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            material = body.get('material', '').strip()

            if not material:
                return JsonResponse({'error': 'Materi tidak boleh kosong.'}, status=400)

            prompt = f"""Rangkum materi berikut dalam poin-poin yang jelas dan mudah dipahami.
Gunakan format plain text biasa tanpa markdown, tanpa bintang (**), tanpa simbol khusus.
Format output:
- Poin 1
- Poin 2
- dst...

Materi:
{material}"""

            response = model.generate_content(prompt)
            return JsonResponse({'result': response.text})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)