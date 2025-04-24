from django import forms
from .models import Resume

class ResumeForm(forms.ModelForm):
    job_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Paste job description here (optional)', 'rows': 4})
    )
    class Meta:
        model = Resume
        fields = ['name', 'email', 'file', 'job_description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }
