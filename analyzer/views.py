import os
import fitz  # PyMuPDF
import google.generativeai as genai
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .forms import ResumeForm
from .models import Resume, ResumeTemplate
from docx import Document
from PyPDF2 import PdfReader
import requests, textwrap
import json

from django.http import HttpResponse, FileResponse
import io
from docx.shared import Pt

# Configure Gemini API Key with a supported model name
genai.configure(api_key='AIzaSyDKuqEZcNm6B4gLy66XqHcSMq2sJTfz2ps')
model = genai.GenerativeModel(model_name="models/text-bison-002")

# List available models
models = genai.list_models()
print(models)

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def parse_resume(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()
    try:
        if file_extension == '.docx':
            # Handle DOCX files
            doc = Document(file_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            return text
        elif file_extension == '.pdf':
            # Handle PDF files via PyPDF2 if needed
            reader = PdfReader(file_path)
            text = ''
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
            return text
        else:
            return "Unsupported file format. Please upload a .docx or .pdf file."
    except Exception as e:
        return f"Error processing file: {str(e)}"

def analyze_resume_text(text):
    prompt = f"""
Please provide a professional resume analysis with the following sections:

Key Strengths:
1. First strength with brief explanation
2. Second strength with brief explanation
3. Third strength with brief explanation

Development Areas:
1. First area with specific details
2. Second area with specific details
3. Third area with specific details

Strategic Recommendations:
1. First actionable recommendation
2. Second actionable recommendation
3. Third actionable recommendation

Please provide concise, clear feedback without using asterisks, bullet points, or markdown formatting.

Resume:
{text}
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Debug the response structure
        print("API Response:", data)  # This will help see the exact response structure
        
        if "candidates" in data and data["candidates"]:
            candidate = data["candidates"][0]
            
            # Try to get text from different possible response structures
            if isinstance(candidate.get("content"), dict) and "parts" in candidate["content"]:
                parts = candidate["content"]["parts"]
                if parts and isinstance(parts[0], dict):
                    return parts[0].get("text", "No feedback generated")
                    
            elif isinstance(candidate.get("content"), dict) and "text" in candidate["content"]:
                return candidate["content"]["text"]
                
            elif "text" in candidate:
                return candidate["text"]
                
            else:
                return f"Unable to extract feedback. Response structure: {candidate}"
        else:
            return "No feedback received from the AI model."
            
    except Exception as e:
        print(f"Error details: {str(e)}")  # Debug information
        return f"Error generating feedback: {str(e)}"

def home(request):
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save()
            file_path = os.path.join(settings.MEDIA_ROOT, resume.file.name)
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.pdf':
                resume_text = extract_text_from_pdf(file_path)
            elif ext == '.docx':
                resume_text = parse_resume(file_path)
            else:
                resume_text = "Unsupported file format. Please upload a .docx or .pdf file."

            feedback = analyze_resume_text(resume_text)
            resume.feedback = feedback
            resume.save()
            return redirect('result', resume.id)
    else:
        form = ResumeForm()
    return render(request, 'analyzer/home.html', {'form': form})

def result(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id)
    return render(request, 'analyzer/result.html', {'resume': resume})


  

def browse_templates(request):
    templates = ResumeTemplate.objects.all().order_by('-created_at')
    return render(request, 'analyzer/browse_templates.html', {"templates": templates})

def download_template(request, template_id):
    template = get_object_or_404(ResumeTemplate, id=template_id)
    response = FileResponse(open(template.file.path, 'rb'))
    # Set filename based on template name (e.g. template_name.docx or pdf)
    filename = f"{template.name.replace(' ', '_')}{os.path.splitext(template.file.name)[1]}"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response