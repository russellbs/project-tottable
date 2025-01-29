# blog/forms.py
from django import forms

class EmailSignupForm(forms.Form):
    day = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(1, 32)],
        label="Day",
        required=True,
    )
    month = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(1, 13)],
        label="Month",
        required=True,
    )
    year = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(1900, 2024)],  # Update range as needed
        label="Year",
        required=True,
    )
    email = forms.EmailField(
        label="Your email address",
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Your email address'}),
    )
