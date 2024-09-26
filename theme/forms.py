from django import forms

class PhoneLoginForm(forms.Form):
    phone = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        'placeholder': '10-digit number',
        'class': 'border border-gray-500 rounded-lg py-1 text-center'
    }))

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={
        'placeholder': '6 digit OTP',
        'class': 'border border-gray-500 rounded-lg py-1 text-center'
    }))
