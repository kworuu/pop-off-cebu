from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class CustomUserRegisterForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.Select(attrs={"class": "form-input", "id": "reg-role"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-input", "id": "reg-password", "placeholder": "Enter password"})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-input", "id": "reg-confirm-password", "placeholder": "Repeat password"})
    )

    class Meta:
        model = User
        fields = ["username", "email", "role"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-input", "id": "reg-username", "placeholder": "e.g., kiko_artisan"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "id": "reg-email", "placeholder": "name@example.com"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Passwords do not match.")
        elif p1:
            candidate = User(
                username=cleaned_data.get("username", ""),
                email=cleaned_data.get("email", ""),
            )
            try:
                validate_password(p1, user=candidate)
            except ValidationError as exc:
                self.add_error("password", exc)
        return cleaned_data