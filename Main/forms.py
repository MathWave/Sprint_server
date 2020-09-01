from django import forms


class PasswordField(forms.CharField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widget = forms.PasswordInput()


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={"class": "input_simple"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input_simple"}))


class FileForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'input_simple'}), required=False)


class TestsForm(forms.Form):
    tests = forms.FileField(widget=forms.FileInput(), required=False)


class ChangePasswordForm(forms.Form):
    old = PasswordField(label='Старый пароль')
    new = PasswordField(label='Новый пароль')
    again = PasswordField(label='Еще раз')


class ResetPasswordForm(forms.Form):
    new = PasswordField(label='Новый пароль')
    again = PasswordField(label='Еще раз')
