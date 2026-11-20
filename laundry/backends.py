from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import CustomerProfile


class EmailOrPhoneBackend(ModelBackend):
    """Позволяет входить по username, email или номеру телефона."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("email")
        if not identifier or password is None:
            return None
        UserModel = get_user_model()
        user = UserModel.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier)).first()
        if user is None:
            profile = CustomerProfile.objects.select_related("user").filter(phone__iexact=identifier).first()
            user = profile.user if profile else None
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
