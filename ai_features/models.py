from django.db import models
from django.contrib.auth.models import User

class AIHistory(models.Model):
    FEATURE_CHOICES = [
        ('summary', 'AI Summary'),
        ('qna', 'AI Q&A'),
        ('quiz', 'Quiz Generator'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_histories')
    feature_type = models.CharField(max_length=10, choices=FEATURE_CHOICES)
    prompt = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.feature_type} - {self.created_at:%Y-%m-%d %H:%M}"