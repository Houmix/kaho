from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Connexion par email insensible à la casse (le nom d'utilisateur est l'email)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        ident = (username or kwargs.get(User.USERNAME_FIELD) or '').strip()
        if not ident or password is None:
            return None
        user = User.objects.filter(username__iexact=ident).first() or User.objects.filter(email__iexact=ident).first()
        if user is None:
            User().set_password(password)  # temps constant
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
