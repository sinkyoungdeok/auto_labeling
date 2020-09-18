from django import forms

class UploadFileForm(forms.Form):
    project_name = forms.CharField(max_length = 15)
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
