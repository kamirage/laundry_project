from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order, OrderItem, GarmentType, ServiceType, Material, CustomerProfile

class OrderRequestForm(forms.Form):
    garment_type = forms.ModelChoiceField(queryset=GarmentType.objects.all(), label="Тип вещи")
    service = forms.ModelChoiceField(queryset=ServiceType.objects.filter(is_active=True), label="Услуга")
    material = forms.ModelChoiceField(queryset=Material.objects.all(), label="Материал")
    description = forms.CharField(label="Комментарий к вещи", required=False,
                                  widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Опишите пятна или особенности вещи"}))
    urgency = forms.ChoiceField(label="Срочность", choices=[("1.00","Обычная"),("1.30","Срочная")])

    def clean_description(self):
        value = self.cleaned_data.get("description", "")
        if len(value) > 255:
            raise forms.ValidationError("Не более 255 символов.")
        return value

class RegistrationForm(forms.Form):
    full_name = forms.CharField(label="ФИО", max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "Фамилия Имя Отчество", "autocomplete": "name"}))
    phone = forms.CharField(label="Телефон", max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "+7 900 000-00-00", "autocomplete": "tel"}))
    email = forms.EmailField(label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "name@example.ru", "autocomplete": "email"}))
    password = forms.CharField(label="Пароль", min_length=8,
        widget=forms.PasswordInput(attrs={"placeholder": "Не менее 8 символов", "autocomplete": "new-password"}))

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if CustomerProfile.objects.filter(phone=phone).exists() or User.objects.filter(username=phone.strip()).exists():
            raise forms.ValidationError("Пользователь с таким телефоном уже зарегистрирован.")
        return phone

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def save(self, commit=True):
        full_name = " ".join(self.cleaned_data["full_name"].split())
        parts = full_name.split(" ", 2)
        last_name = parts[0] if parts else ""
        first_name = parts[1] if len(parts) > 1 else ""
        username = self.cleaned_data["phone"].strip()
        user = User(username=username, first_name=first_name, last_name=last_name,
                    email=self.cleaned_data["email"])
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            CustomerProfile.objects.create(user=user, phone=self.cleaned_data["phone"])
        return user

class InspectionForm(forms.Form):
    defect = forms.CharField(label="Дефект", max_length=150, required=False,
        widget=forms.TextInput(attrs={"placeholder": "Например, разрыв подкладки"}))
    comment = forms.CharField(label="Комментарий", required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Описание состояния вещи"}))
    estimated_price = forms.DecimalField(label="Стоимость после осмотра", min_value=0,
        max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={"placeholder": "0.00"}))
