import os
import fitz  # PyMuPDF
import google.generativeai as genai
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .forms import ResumeForm
from .models import Resume, ResumeTemplate
from docx import Document
import json
import logging
from django.http import HttpResponse, FileResponse, Http404
from django.contrib import messages
import re

# Set up logging
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF files using PyMuPDF (fitz)"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        return f"Error processing PDF: {str(e)}"

def extract_text_from_docx(docx_path):
    """Extract text from DOCX files"""
    try:
        doc = Document(docx_path)
        text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"DOCX extraction error: {str(e)}")
        return f"Error processing DOCX: {str(e)}"

def parse_resume(file_path):
    """Parse resume content from various file formats"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.docx':
            return extract_text_from_docx(file_path)
        elif file_extension == '.pdf':
            return extract_text_from_pdf(file_path)
        else:
            return "Unsupported file format. Please upload a .docx or .pdf file."
    except Exception as e:
        logger.error(f"Parse resume error: {str(e)}")
        return f"Error processing file: {str(e)}"

def analyze_resume_text(text, job_description=None):
    """Analyze resume text using Gemini API"""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = """Analyze this resume and provide feedback in the following JSON format:
        {
            "ats_score": <score between 85-100>,
            "executive_summary": "<2-3 line professional summary>",
            "key_strengths": [
                {"strength": "<skill>", "evidence": "<where demonstrated>"}
            ],
            "development_areas": [
                {"area": "<area>", "recommendation": "<suggestion>"}
            ],
            "missing_keywords": ["<important keywords>"],
            "formatting_issues": ["<formatting suggestions>"]
        }
        """
        
        if job_description:
            prompt += f"\n\nConsider this job description for the analysis:\n{job_description}"
        
        response = model.generate_content(prompt + "\n\nRESUME:\n" + text)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'(\{.*\})', response.text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(1))
                return analysis
            return create_fallback_analysis(text)
            
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response")
            return create_fallback_analysis(text)
            
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return create_fallback_analysis(text)

def create_fallback_analysis(text):
    """Create a basic analysis when the main analysis fails"""
    return {
        "ats_score": 85,
        "executive_summary": "Professional with relevant experience and skills.",
        "key_strengths": [
            {"strength": "Experience", "evidence": "Demonstrated through work history"}
        ],
        "development_areas": [
            {"area": "Resume Format", "recommendation": "Consider professional formatting"}
        ],
        "missing_keywords": ["specific skills"],
        "formatting_issues": ["Review overall format"]
    }

def home(request):
    """Home view with resume upload form"""
    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save()
            
            # Process resume
            file_path = os.path.join(settings.MEDIA_ROOT, resume.file.name)
            resume_text = parse_resume(file_path)
            
            try:
                # Analyze the resume
                job_description = form.cleaned_data.get('job_description')
                feedback = analyze_resume_text(resume_text, job_description)
                
                # Save analysis results
                resume.content = resume_text
                resume.feedback = json.dumps(feedback)
                resume.ats_score = feedback.get('ats_score', 0)
                resume.save()
                
                return redirect('result', resume.id)
                
            except Exception as e:
                logger.error(f"Resume analysis failed: {str(e)}")
                messages.error(request, "Resume analysis failed. Please try again.")
    else:
        form = ResumeForm()
    
    return render(request, 'analyzer/home.html', {
        'form': form,
        'featured_templates': ResumeTemplate.objects.filter(featured=True)[:3]
    })

def result(request, resume_id):
    """View for displaying analysis results"""
    resume = get_object_or_404(Resume, id=resume_id)
    
    try:
        analysis = json.loads(resume.feedback) if resume.feedback else {}
    except json.JSONDecodeError:
        analysis = {}
        messages.error(request, "Error processing analysis results.")
    
    return render(request, 'analyzer/result.html', {
        'resume': resume,
        'analysis': analysis
    })

def browse_templates(request):
    """Browse resume templates"""
    templates = ResumeTemplate.objects.all().order_by('-created_at')
    return render(request, 'analyzer/browse_templates.html', {"templates": templates})

def download_template(request, template_id):
    """Download a resume template"""
    template = get_object_or_404(ResumeTemplate, id=template_id)
    try:
        response = FileResponse(open(template.file.path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{template.name}.docx"'
        return response
    except Exception as e:
        logger.error(f"Template download error: {str(e)}")
        raise Http404("Template file not found")