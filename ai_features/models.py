from django.db import models
from django.contrib.auth.models import User


class Materi(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='materis')
    isi_materi = models.TextField()
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']

    def __str__(self):
        return f"{self.user.username} - {self.isi_materi[:50]}"


class HasilAI(models.Model):
    materi = models.ForeignKey(Materi, on_delete=models.CASCADE, related_name='hasil_ai')
    hasil_summary = models.TextField(blank=True, null=True)
    pertanyaan = models.TextField(blank=True, null=True)
    jawaban = models.TextField(blank=True, null=True)
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']

    def __str__(self):
        return f"HasilAI - {self.materi.user.username} - {self.tanggal:%Y-%m-%d %H:%M}"


class QuizSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_sessions')
    materi_input = models.TextField()
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-tanggal']

    def __str__(self):
        return f"Quiz - {self.user.username} - {self.tanggal:%Y-%m-%d %H:%M}"


class QuizQuestion(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='questions')
    nomor_soal = models.IntegerField()
    pertanyaan = models.TextField()
    opsi_a = models.TextField()
    opsi_b = models.TextField()
    opsi_c = models.TextField()
    opsi_d = models.TextField()
    jawaban_benar = models.CharField(max_length=1)
    penjelasan = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['nomor_soal']

    def __str__(self):
        return f"Q{self.nomor_soal} - {self.session}"