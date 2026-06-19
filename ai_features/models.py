from django.db import models
from django.contrib.auth.models import User


class Summary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='summaries')
    isi_materi = models.TextField()
    hasil_summary = models.TextField()
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']

    def __str__(self):
        return f"Summary - {self.user.username} - {self.isi_materi[:50]}"


class Qna(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qnas')
    pertanyaan = models.TextField()
    jawaban = models.TextField()
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']

    def __str__(self):
        return f"QnA - {self.user.username} - {self.pertanyaan[:50]}"


class QuizMateri(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_materis')
    isi_materi = models.TextField()
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']

    def __str__(self):
        return f"QuizMateri - {self.user.username} - {self.isi_materi[:50]}"


class Quiz(models.Model):
    materi = models.ForeignKey(QuizMateri, on_delete=models.CASCADE, related_name='quizzes')
    soal = models.TextField()
    opsi_a = models.TextField()
    opsi_b = models.TextField()
    opsi_c = models.TextField()
    opsi_d = models.TextField()
    jawaban_benar = models.CharField(max_length=1)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Quiz - {self.materi.user.username} - {self.soal[:30]}"