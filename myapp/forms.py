from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV File (containing transaction data)")

class SingleTransactionForm(forms.Form):
    contact_num = forms.CharField(label="Contact Number")
    merchant = forms.CharField(label="Merchant Name")
    category = forms.CharField(label="Transaction Category")
    amt = forms.DecimalField(label="Amount (M)", min_value=0.01, max_digits=15, decimal_places=2)
    unix_time = forms.IntegerField(label="Unix Timestamp (Optional)", required=False, help_text="Leave blank if unavailable.")
    trans_datetime = forms.DateTimeField(label="Transaction Datetime", help_text="Format: YYYY-MM-DD HH:MM:SS")

class MultipleTransactionForm(forms.Form):
    csv_file = forms.FileField(label="Upload CSV File (containing transaction data)")

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

from django import forms

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

