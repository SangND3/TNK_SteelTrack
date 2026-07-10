from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Tên đăng nhập",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "Tên đăng nhập",
            }
        ),
    )
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "••••••••",
            }
        ),
    )
    remember_me = forms.BooleanField(
        required=False,
        label="Ghi nhớ đăng nhập",
    )

    def clean_username(self) -> str:
        return self.cleaned_data["username"].strip()
