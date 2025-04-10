from django.db import models

class Resume(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    file = models.FileField(upload_to='resumes/')
    feedback = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name