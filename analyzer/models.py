from django.db import models
from django.core.validators import EmailValidator

class Resume(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(validators=[EmailValidator()])
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(blank=True)
    feedback = models.JSONField(null=True, blank=True)
    ats_score = models.IntegerField(default=0)
    optimized_file = models.FileField(upload_to='optimized_resumes/', null=True, blank=True)

    def __str__(self):
        return f"{self.name}'s Resume"

class ResumeTemplate(models.Model):
    CATEGORY_CHOICES = [
        ('Professional', 'Professional'),
        ('Creative', 'Creative'),
        ('Technical', 'Technical'),
    ]
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Professional')
    preview_image = models.ImageField(upload_to='template_previews/', blank=True, null=True)
    file = models.FileField(upload_to='templates/')
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name