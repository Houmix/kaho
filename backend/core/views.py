from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    PasswordResetConfirmSerializer, PasswordResetRequestSerializer, RegisterSerializer, UserSerializer,
)
from .tasks import send_password_reset_email


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh), 'user': UserSerializer(user).data}


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(_tokens_for(serializer.save()), status=status.HTTP_201_CREATED)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = PasswordResetRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=s.validated_data['email'], is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            send_password_reset_email.delay(user.email, f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}")
        # Même réponse qu'un compte existe ou non (pas d'énumération d'emails)
        return Response({'detail': 'Si un compte existe pour cet email, un lien de réinitialisation a été envoyé.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = PasswordResetConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(s.validated_data['uid'])))
        except (ValueError, User.DoesNotExist):
            user = None
        if user is None or not default_token_generator.check_token(user, s.validated_data['token']):
            return Response({'detail': 'Lien invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(s.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response(_tokens_for(user))
