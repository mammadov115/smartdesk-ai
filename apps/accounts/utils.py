from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.is_email_verified}{user.is_active}{timestamp}"


email_verification_token_generator = EmailVerificationTokenGenerator()


def encode_uid(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def decode_uid(uidb64):
    return force_str(urlsafe_base64_decode(uidb64))
