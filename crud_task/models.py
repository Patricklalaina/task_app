from django.db import models
from datetime import timedelta

# Create your models here.
class   User(models.Model):
    user_id = models.CharField(max_length=100, primary_key=True)
    user_mail = models.EmailField(max_length=200, unique=True)
    user_pd = models.CharField(max_length=200)
    user_log = models.BooleanField(default=False)
    def __str__(self):
        return self.user_id

class Project(models.Model):
    p_id = models.AutoField(primary_key=True)
    p_name = models.CharField(max_length=100)
    p_description = models.TextField(blank=True, null=True)
    p_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project")
    def __str__(self):
        return self.p_name

class Task(models.Model):
    task_id = models.AutoField(primary_key=True)
    task_title = models.CharField(max_length=200)
    task_desc = models.TextField(blank=True, null=True)
    task_status = models.BooleanField(default=False)
    task_project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="task")
    task_creation = models.DateTimeField(auto_now_add=True, null=True)
    task_duration = models.DurationField(blank=True, null=True, help_text="Durée estimée (HH:MM:SS)")
    task_finish = models.BooleanField(default=False)
    def __str__(self):
        return self.task_title
    
    def set_duration(self, minutes: int):
        self.task_duration = timedelta(minutes=minutes)
        self.save(update_fields=["task_duration"])

    def duration_to_minutes(self) -> int:
        """Retourne la durée en minutes (0 si None)."""
        return int(self.task_duration.total_seconds() // 60) if self.task_duration else 0
        