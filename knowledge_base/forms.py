from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Select CSV or Excel File (.csv, .xlsx, .xls)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv, .xlsx, .xls'})
    )

class SingleURLForm(forms.Form):
    url = forms.URLField(
        label="Single URL to Ingest",
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.wikipedia.com'
        })
    )
