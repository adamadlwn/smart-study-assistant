import os
import json
import google.generativeai as genai
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Materi, HasilAI, QuizSession, QuizQuestion


# Konfigurasi Gemini API
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')


@login_required(login_url='/login/')
def summary_view(request):
    histories = HasilAI.objects.filter(
        materi__user=request.user,
        hasil_summary__isnull=False
    ).select_related('materi')
    return render(request, 'summary.html', {'histories': histories})


@login_required(login_url='/login/')
def qna_view(request):
    histories = HasilAI.objects.filter(
        materi__user=request.user,
        pertanyaan__isnull=False
    ).select_related('materi')
    return render(request, 'qna.html', {'histories': histories})


@login_required(login_url='/login/')
def quiz_view(request):
    histories = QuizSession.objects.filter(user=request.user)
    return render(request, 'quiz.html', {'histories': histories})


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

            # Simpan ke database
            materi = Materi.objects.create(user=request.user, isi_materi=material)
            HasilAI.objects.create(materi=materi, hasil_summary=response.text)

            return JsonResponse({'result': response.text})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)


@login_required(login_url='/login/')
def qna_api(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            question = body.get('question', '').strip()

            if not question:
                return JsonResponse({'error': 'Pertanyaan tidak boleh kosong.'}, status=400)

            prompt = f"""Jawab pertanyaan berikut dengan jelas dan mudah dipahami.
Gunakan format plain text biasa tanpa markdown, tanpa bintang (**), tanpa simbol khusus.
Jawab dalam Bahasa Indonesia.

Pertanyaan:
{question}"""

            response = model.generate_content(prompt)

            # Simpan ke database
            materi = Materi.objects.create(user=request.user, isi_materi=question)
            HasilAI.objects.create(materi=materi, pertanyaan=question, jawaban=response.text)

            return JsonResponse({'result': response.text})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)


@login_required(login_url='/login/')
def quiz_api(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            material = body.get('material', '').strip()
            session_id = body.get('session_id')  # NEW

            if not material:
                return JsonResponse({'error': 'Materi tidak boleh kosong.'}, status=400)

            prompt = f"""Buatkan 5 soal pilihan ganda berdasarkan materi berikut.
Gunakan format plain text biasa tanpa markdown, tanpa bintang (**), tanpa simbol khusus.
Format output:
Question 1: [pertanyaan]
A. [pilihan]
B. [pilihan]
C. [pilihan]
D. [pilihan]

Question 2: [pertanyaan]
A. [pilihan]
B. [pilihan]
C. [pilihan]
D. [pilihan]

(dan seterusnya sampai 5 soal)

Materi:
{material}"""

            response = model.generate_content(prompt)

            # Reuse existing session if one was passed in, otherwise create a new one
            session = None
            if session_id:
                session = QuizSession.objects.filter(id=session_id, user=request.user).first()

            if session:
                session.materi_input = material
                session.save()
                # old quiz/answer no longer matches the new material, clear it out
                session.questions.all().delete()
            else:
                session = QuizSession.objects.create(user=request.user, materi_input=material)

            return JsonResponse({'result': response.text, 'session_id': session.id})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)


@login_required(login_url='/login/')
def quiz_answer_api(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            quiz = body.get('quiz', '').strip()
            session_id = body.get('session_id')

            if not quiz:
                return JsonResponse({'error': 'Soal tidak boleh kosong.'}, status=400)

            prompt = f"""Berikan kunci jawaban untuk soal pilihan ganda berikut beserta penjelasan singkat.
Gunakan format plain text biasa tanpa markdown, tanpa bintang (**), tanpa simbol khusus.
Format output:
Question 1: [jawaban yang benar] - [penjelasan singkat]
Question 2: [jawaban yang benar] - [penjelasan singkat]
(dan seterusnya)

Soal:
{quiz}"""

            response = model.generate_content(prompt)

            # Simpan jawaban ke session
            if session_id:
                try:
                    session = QuizSession.objects.get(id=session_id, user=request.user)
                    QuizQuestion.objects.update_or_create(
                        session=session,
                        nomor_soal=1,
                        defaults={
                            'pertanyaan': quiz,
                            'opsi_a': '', 'opsi_b': '', 'opsi_c': '', 'opsi_d': '',
                            'jawaban_benar': '',
                            'penjelasan': response.text
                        }
                    )
                except QuizSession.DoesNotExist:
                    pass

            return JsonResponse({'result': response.text})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)


@login_required(login_url='/login/')
def get_summary_history(request, history_id):
    hasil = get_object_or_404(HasilAI, id=history_id, materi__user=request.user)
    return JsonResponse({
        'material': hasil.materi.isi_materi,
        'result': hasil.hasil_summary
    })


@login_required(login_url='/login/')
def get_qna_history(request, history_id):
    hasil = get_object_or_404(HasilAI, id=history_id, materi__user=request.user)
    return JsonResponse({
        'question': hasil.pertanyaan,
        'result': hasil.jawaban
    })


@login_required(login_url='/login/')
def get_quiz_history(request, history_id):
    session = get_object_or_404(QuizSession, id=history_id, user=request.user)
    question = session.questions.first()
    return JsonResponse({
        'material': session.materi_input,
        'quiz': question.pertanyaan if question else '',
        'answer': question.penjelasan if question else ''
    })