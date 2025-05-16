from django import forms
from .models import Document, Keyword

class DocumentUploadForm(forms.ModelForm):
    keywords = forms.CharField(
        max_length=255,
        required=False,
        help_text="Enter keywords separated by commas (e.g., Minutes, Event Planning, Map)"
    )

    class Meta:
        model = Document
        fields = ['upload', 'title', 'description', 'keywords'] 

