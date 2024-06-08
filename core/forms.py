from django import forms
from django.contrib.auth.forms import UserCreationForm
from userauths.models import User

class NewsletterForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control border-white',
        'placeholder': 'Your email address'
    }))

class UserQueryForm(forms.Form):
    name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Name *"}),
        max_length=100,
        required=True,
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email address *"}),
        required=True,
    )
    phone = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number *"}),
        max_length=15,
        required=True,
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control form-control_gray", "placeholder": "Your Message", "cols": 30, "rows": 8}),
        required=True,
    )