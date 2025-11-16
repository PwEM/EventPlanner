from allauth.account.forms import SignupForm, LoginForm
from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib import messages
from django.contrib.auth.models import Group
from tailwind.validate import ValidationError


class UserProfileForm(forms.ModelForm):
    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
            'placeholder': 'New Password',
        })
    )
    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
            'placeholder': 'Confirm New Password',
        })
    )

    class Meta:
        model = get_user_model()
        fields = ['email', 'username', 'first_name', 'last_name', 'phone', 'profile_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
            })

        self.fields['email'].widget.attrs.update({
            'readonly': True,
            'placeholder': 'Email Address',
            'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed',
        })

        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['first_name'].widget.attrs['placeholder'] = 'First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Last Name'
        self.fields['phone'].widget.attrs['placeholder'] = 'Phone Number'

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 or password2:
            if password1 != password2:
                raise ValidationError("Passwords do not match.")
            if len(password1) < 8:
                raise ValidationError("Password must be at least 8 characters long.")

        return cleaned_data

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class UserRegisterForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'].widget.attrs.update({
            'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
            'placeholder': 'Email Address',
        })
        self.fields['username'].widget.attrs.update({
            'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
            'placeholder': 'Username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
            'placeholder': 'Password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
            'placeholder': 'Confirm Password',
        })

    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
        'placeholder': 'First Name',
    }))

    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
        'placeholder': 'Last Name',
    }))

    phone = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
        'placeholder': 'Phone Number',
    }))

    profile_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
    }))

    is_vendor = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
    }), label='Is Vendor')

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.profile_image = self.cleaned_data.get('profile_image')

        if self.cleaned_data['is_vendor']:
            group, created = Group.objects.get_or_create(name='Vendors')
            user.groups.add(group)
        user.save()
        return user

class UserLoginForm(LoginForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
        'placeholder': 'Password',
    }))

    remember = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-4 w-4 text-secondary',
            'id': 'remember_me',
            'data-toggle': 'remember-me',
        }),
        label="Remember me"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].widget.attrs.update({
            'class': 'w-full p-3 mb-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary',
        })
