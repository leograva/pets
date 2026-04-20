from django import forms
from django.contrib.auth import get_user_model
from .models import Pet, CheckIn


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Senha')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirme a senha')

    class Meta:
        model = get_user_model()
        fields = ['username', 'email']
        labels = {
            'username': 'Nome de usuário',
            'email': 'E-mail',
        }
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'username', 'class': 'ui-input'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'ui-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'ui-input')
        self.fields['password'].widget.attrs.update({'class': 'ui-input'})
        self.fields['password_confirm'].widget.attrs.update({'class': 'ui-input'})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'As senhas não coincidem.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['name', 'species', 'birth_date']
        labels = {
            'name': 'Nome do pet',
            'species': 'Espécie',
            'birth_date': 'Data de nascimento',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'ui-input'}),
            'species': forms.TextInput(attrs={'class': 'ui-input'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'ui-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InviteTutorForm(forms.Form):
    invitee_email = forms.EmailField(label='E-mail do tutor', widget=forms.EmailInput(attrs={'class': 'ui-input'}))


class CheckInForm(forms.ModelForm):
    class Meta:
        model = CheckIn
        fields = ['checkin_type', 'description']
        labels = {
            'checkin_type': 'Tipo de registro',
            'description': 'Observações',
        }
        widgets = {
            'checkin_type': forms.Select(attrs={'class': 'ui-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'ui-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['checkin_type'].widget.attrs.setdefault('class', 'ui-select')
