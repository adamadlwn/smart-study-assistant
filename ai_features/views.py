import os
import re
import json
from urllib import response
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

            qna = Qna.objects.create(user=request.user, pertanyaan=question, jawaban=response.text)
            
            return JsonResponse({'result': response.text, 'history_id': qna.id})

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

            prompt = f"""Buatkan 10 soal pilihan ganda berdasarkan materi berikut.
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

(dan seterusnya sampai Soal 10)

Materi:
{material}"""

            response = model.generate_content(prompt)
            questions = parse_quiz_text(response.text)

            if not questions:
                return JsonResponse({'error': 'Gagal memproses hasil dari AI, coba generate ulang.'}, status=500)

            materi = QuizMateri.objects.create(user=request.user, isi_materi=material)
            quiz_objects = []
            for q in questions:
                quiz_objects.append(Quiz.objects.create(materi=materi, **q))

            quiz_data = [{
                'id': q.id,
                'soal': q.soal,
                'opsi_a': q.opsi_a,
                'opsi_b': q.opsi_b,
                'opsi_c': q.opsi_c,
                'opsi_d': q.opsi_d,
            } for q in quiz_objects]

            return JsonResponse({'questions': quiz_data, 'materi_id': materi.id})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)


@login_required(login_url='/login/')
def quiz_submit_api(request):
    """Terima semua jawaban sekaligus, simpan ke DB, hitung skor."""
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            materi_id = body.get('materi_id')
            answers = body.get('answers', {})  # { "quiz_id": "A" }

            if not materi_id:
                return JsonResponse({'error': 'materi_id tidak boleh kosong.'}, status=400)

            materi = get_object_or_404(QuizMateri, id=materi_id, user=request.user)
            quizzes = materi.quizzes.all()

            if not quizzes:
                return JsonResponse({'error': 'Belum ada soal untuk materi ini.'}, status=404)

            results = []
            correct_count = 0

            for q in quizzes:
                user_answer = answers.get(str(q.id))
                is_correct = (user_answer == q.jawaban_benar)
                if is_correct:
                    correct_count += 1

                q.user_answer = user_answer
                q.save()

                results.append({
                    'id': q.id,
                    'soal': q.soal,
                    'opsi_a': q.opsi_a,
                    'opsi_b': q.opsi_b,
                    'opsi_c': q.opsi_c,
                    'opsi_d': q.opsi_d,
                    'user_answer': user_answer,
                    'jawaban_benar': q.jawaban_benar,
                    'is_correct': is_correct,
                })

            total = quizzes.count()
            score = round((correct_count / total) * 100) if total > 0 else 0

            materi.is_completed = True
            materi.score = score
            materi.save()

            return JsonResponse({
                'score': score,
                'correct_count': correct_count,
                'total': total,
                'results': results,
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method tidak diizinkan.'}, status=405)


@login_required(login_url='/login/')
def get_quiz_history(request, history_id):
    """Load history lama, kembalikan dalam format terstruktur."""
    try:
        materi = get_object_or_404(QuizMateri, id=history_id, user=request.user)
        quizzes = materi.quizzes.all()

        questions = [{
            'id': q.id,
            'soal': q.soal,
            'opsi_a': q.opsi_a,
            'opsi_b': q.opsi_b,
            'opsi_c': q.opsi_c,
            'opsi_d': q.opsi_d,
            'user_answer': q.user_answer,
            'jawaban_benar': q.jawaban_benar,
        } for q in quizzes]

        return JsonResponse({
            'material': materi.isi_materi,
            'materi_id': materi.id,
            'is_completed': materi.is_completed,
            'score': materi.score,
            'questions': questions,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
