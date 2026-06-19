import os
import re
import json
import google.generativeai as genai
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Summary, Qna, QuizMateri, Quiz


genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')


@login_required(login_url='/login/')
def summary_view(request):
    histories = Summary.objects.filter(user=request.user)
    return render(request, 'summary.html', {'histories': histories})


@login_required(login_url='/login/')
def qna_view(request):
    histories = Qna.objects.filter(user=request.user)
    return render(request, 'qna.html', {'histories': histories})


@login_required(login_url='/login/')
def quiz_view(request):
    histories = QuizMateri.objects.filter(user=request.user, quizzes__isnull=False).distinct()
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

            summary = Summary.objects.create(user=request.user, isi_materi=material, hasil_summary=response.text)
            
            return JsonResponse({'result': response.text, 'history_id': summary.id})

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

            Qna.objects.create(user=request.user, pertanyaan=question, jawaban=response.text)

            return JsonResponse({'result': response.text})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)


def parse_quiz_text(text):
    """Pecah teks hasil AI jadi list dict per soal."""
    pattern = re.compile(
        r'Soal\s*\d+:\s*(.*?)\n'
        r'A\)\s*(.*?)\n'
        r'B\)\s*(.*?)\n'
        r'C\)\s*(.*?)\n'
        r'D\)\s*(.*?)\n'
        r'Jawaban:\s*([A-D])',
        re.DOTALL
    )
    questions = []
    for m in pattern.findall(text):
        questions.append({
            'soal': m[0].strip(),
            'opsi_a': m[1].strip(),
            'opsi_b': m[2].strip(),
            'opsi_c': m[3].strip(),
            'opsi_d': m[4].strip(),
            'jawaban_benar': m[5].strip(),
        })
    return questions


def format_quiz_for_display(questions):
    lines = []
    for i, q in enumerate(questions, start=1):
        lines.append(f"Question {i}: {q['soal']}")
        lines.append(f"A. {q['opsi_a']}")
        lines.append(f"B. {q['opsi_b']}")
        lines.append(f"C. {q['opsi_c']}")
        lines.append(f"D. {q['opsi_d']}")
        lines.append("")
    return "\n".join(lines).strip()


@login_required(login_url='/login/')
def quiz_api(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            material = body.get('material', '').strip()

            if not material:
                return JsonResponse({'error': 'Materi tidak boleh kosong.'}, status=400)

            prompt = f"""Buatkan 5 soal pilihan ganda berdasarkan materi berikut.
Gunakan format PERSIS seperti contoh di bawah ini untuk setiap soal, tanpa markdown dan tanpa simbol bintang (**):

Soal 1: [pertanyaan]
A) [pilihan]
B) [pilihan]
C) [pilihan]
D) [pilihan]
Jawaban: [A/B/C/D]

Soal 2: [pertanyaan]
A) [pilihan]
B) [pilihan]
C) [pilihan]
D) [pilihan]
Jawaban: [A/B/C/D]

(dan seterusnya sampai Soal 5)

Materi:
{material}"""

            response = model.generate_content(prompt)
            questions = parse_quiz_text(response.text)

            if not questions:
                return JsonResponse({'error': 'Gagal memproses hasil dari AI, coba generate ulang.'}, status=500)

            materi = QuizMateri.objects.create(user=request.user, isi_materi=material)
            for q in questions:
                Quiz.objects.create(materi=materi, **q)

            quiz_text = format_quiz_for_display(questions)

            return JsonResponse({'result': quiz_text, 'materi_id': materi.id})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)


@login_required(login_url='/login/')
def quiz_answer_api(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            materi_id = body.get('materi_id')

            if not materi_id:
                return JsonResponse({'error': 'materi_id tidak boleh kosong.'}, status=400)

            materi = get_object_or_404(QuizMateri, id=materi_id, user=request.user)
            quizzes = materi.quizzes.all()

            if not quizzes:
                return JsonResponse({'error': 'Belum ada soal untuk materi ini.'}, status=404)

            lines = [f"Question {i}: {q.jawaban_benar}" for i, q in enumerate(quizzes, start=1)]
            return JsonResponse({'result': "\n".join(lines)})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)


@login_required(login_url='/login/')
def get_summary_history(request, history_id):
    hasil = get_object_or_404(Summary, id=history_id, user=request.user)
    return JsonResponse({
        'material': hasil.isi_materi,
        'result': hasil.hasil_summary
    })


@login_required(login_url='/login/')
def get_qna_history(request, history_id):
    hasil = get_object_or_404(Qna, id=history_id, user=request.user)
    return JsonResponse({
        'question': hasil.pertanyaan,
        'result': hasil.jawaban
    })


@login_required(login_url='/login/')
def get_quiz_history(request, history_id):
    materi = get_object_or_404(QuizMateri, id=history_id, user=request.user)
    quizzes = materi.quizzes.all()

    quiz_lines = []
    answer_lines = []
    for i, q in enumerate(quizzes, start=1):
        quiz_lines += [f"Question {i}: {q.soal}", f"A. {q.opsi_a}", f"B. {q.opsi_b}",
                       f"C. {q.opsi_c}", f"D. {q.opsi_d}", ""]
        answer_lines.append(f"Question {i}: {q.jawaban_benar}")

    return JsonResponse({
        'material': materi.isi_materi,
        'quiz': "\n".join(quiz_lines).strip(),
        'answer': "\n".join(answer_lines)
    })