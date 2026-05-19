import json
import textwrap
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from rest_framework.test import APIClient

from .models import CompanyProfile
from .models import User
from .utils import email_verification_token_generator
from .utils import encode_uid

# ---------------------------------------------------------------------------
# Request / response log — populated by LoggingAPIClient during each test
# ---------------------------------------------------------------------------
_REQUEST_LOG: list[dict] = []


def tearDownModule():
    """Write the full request/response report after all tests finish."""
    report_path = Path(__file__).resolve().parent.parent.parent / "test_report.txt"
    lines = [
        "=" * 80,
        "  AUTH API — TEST REPORT",
        f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 80,
        "",
    ]

    current_class = None
    for entry in _REQUEST_LOG:
        if entry["class"] != current_class:
            current_class = entry["class"]
            lines += [f"\n{'─' * 80}", f"  {current_class}", f"{'─' * 80}"]

        payload_str = (
            json.dumps(entry["payload"], indent=4) if entry["payload"] else "(empty)"
        )
        response_str = (
            json.dumps(entry["response"], indent=4)
            if isinstance(entry["response"], (dict, list))
            else str(entry["response"])
        )

        lines += [
            f"\n  TEST      : {entry['test']}",
            f"  ENDPOINT  : {entry['method']} {entry['url']}",
            "  PAYLOAD   :",
            textwrap.indent(payload_str, "    "),
            f"  STATUS    : {entry['status_code']}",
            "  RESPONSE  :",
            textwrap.indent(response_str, "    "),
        ]

    lines.append("\n" + "=" * 80 + "\n")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Report written → {report_path}")


class LoggingAPIClient(APIClient):
    """APIClient that records every request/response into _REQUEST_LOG."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._test_name = "unknown"
        self._class_name = "unknown"

    def _record(self, method, url, payload, response):
        try:
            response_data = response.data
        except AttributeError:
            response_data = None
        _REQUEST_LOG.append({
            "class": self._class_name,
            "test": self._test_name,
            "method": method,
            "url": url,
            "payload": payload,
            "status_code": response.status_code,
            "response": response_data,
        })

    def post(self, path, data=None, **kwargs):
        response = super().post(path, data, **kwargs)
        self._record("POST", path, data, response)
        return response

    def get(self, path, data=None, **kwargs):
        response = super().get(path, data, **kwargs)
        self._record("GET", path, data, response)
        return response

    def patch(self, path, data=None, **kwargs):
        response = super().patch(path, data, **kwargs)
        self._record("PATCH", path, data, response)
        return response


def _make_verified_user(email="user@example.com", password="StrongPass1!", name="Test User"):
    """Create an active, email-verified user with a company profile."""
    user = User.objects.create_user(
        email=email,
        password=password,
        name=name,
        is_active=True,
        is_email_verified=True,
    )
    CompanyProfile.objects.create(owner=user, name=name)
    return user


class RegisterViewTests(TestCase):
    url = "/api/auth/register/"

    def setUp(self):
        self.client = LoggingAPIClient()
        self.client._class_name = self.__class__.__name__
        self.client._test_name = self._testMethodName

    @patch("apps.accounts.services._send_mail")
    def test_register_success_returns_201(self, mock_mail):
        payload = {"name": "Alice", "email": "alice@example.com", "password": "StrongPass1!"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn("detail", response.data)

    @patch("apps.accounts.services._send_mail")
    def test_register_creates_inactive_unverified_user(self, mock_mail):
        payload = {"name": "Alice", "email": "alice@example.com", "password": "StrongPass1!"}
        self.client.post(self.url, payload)
        user = User.objects.get(email="alice@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_email_verified)

    @patch("apps.accounts.services._send_mail")
    def test_register_creates_company_profile(self, mock_mail):
        payload = {"name": "Alice", "email": "alice@example.com", "password": "StrongPass1!"}
        self.client.post(self.url, payload)
        user = User.objects.get(email="alice@example.com")
        self.assertTrue(CompanyProfile.objects.filter(owner=user).exists())

    @patch("apps.accounts.services._send_mail")
    def test_register_sends_verification_email(self, mock_mail):
        payload = {"name": "Alice", "email": "alice@example.com", "password": "StrongPass1!"}
        self.client.post(self.url, payload)
        mock_mail.assert_called_once()
        subject, _, recipient = mock_mail.call_args[0]
        self.assertIn("Verify", subject)
        self.assertEqual(recipient, "alice@example.com")

    def test_register_duplicate_email_returns_400(self):
        _make_verified_user(email="alice@example.com")
        payload = {"name": "Alice2", "email": "alice@example.com", "password": "StrongPass1!"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 400)

    def test_register_missing_fields_returns_400(self):
        response = self.client.post(self.url, {"email": "alice@example.com"})
        self.assertEqual(response.status_code, 400)

    def test_register_weak_password_returns_400(self):
        payload = {"name": "Alice", "email": "alice@example.com", "password": "123"}
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 400)


class VerifyEmailViewTests(TestCase):
    url = "/api/auth/verify-email/"

    def setUp(self):
        self.client = LoggingAPIClient()
        self.client._class_name = self.__class__.__name__
        self.client._test_name = self._testMethodName
        self.user = User.objects.create_user(
            email="bob@example.com",
            password="StrongPass1!",
            name="Bob",
            is_active=False,
            is_email_verified=False,
        )

    def _valid_params(self):
        return {
            "uid": encode_uid(self.user),
            "token": email_verification_token_generator.make_token(self.user),
        }

    def test_verify_email_success_returns_200(self):
        response = self.client.post(self.url, self._valid_params())
        self.assertEqual(response.status_code, 200)

    def test_verify_email_activates_user(self):
        self.client.post(self.url, self._valid_params())
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)

    def test_verify_email_invalid_token_returns_400(self):
        response = self.client.post(self.url, {"uid": encode_uid(self.user), "token": "bad-token"})
        self.assertEqual(response.status_code, 400)

    def test_verify_email_invalid_uid_returns_400(self):
        response = self.client.post(self.url, {"uid": "notauid", "token": "sometoken"})
        self.assertEqual(response.status_code, 400)

    def test_verify_email_token_reuse_returns_400(self):
        params = self._valid_params()
        self.client.post(self.url, params)
        # second use of same token must fail (user state changed, token invalidated)
        response = self.client.post(self.url, params)
        self.assertEqual(response.status_code, 400)


class LoginViewTests(TestCase):
    url = "/api/auth/login/"

    def setUp(self):
        self.client = LoggingAPIClient()
        self.client._class_name = self.__class__.__name__
        self.client._test_name = self._testMethodName
        self.user = _make_verified_user()

    def test_login_success_returns_200(self):
        response = self.client.post(self.url, {"email": "user@example.com", "password": "StrongPass1!"})
        self.assertEqual(response.status_code, 200)

    def test_login_wrong_password_returns_400(self):
        response = self.client.post(self.url, {"email": "user@example.com", "password": "WrongPass1!"})
        self.assertEqual(response.status_code, 400)

    def test_login_unverified_user_returns_400(self):
        unverified = User.objects.create_user(
            email="unverified@example.com",
            password="StrongPass1!",
            name="Unverified",
            is_active=False,
            is_email_verified=False,
        )
        response = self.client.post(self.url, {"email": unverified.email, "password": "StrongPass1!"})
        self.assertEqual(response.status_code, 400)

    def test_login_nonexistent_user_returns_400(self):
        response = self.client.post(self.url, {"email": "ghost@example.com", "password": "StrongPass1!"})
        self.assertEqual(response.status_code, 400)

    def test_login_missing_fields_returns_400(self):
        response = self.client.post(self.url, {"email": "user@example.com"})
        self.assertEqual(response.status_code, 400)


class LogoutViewTests(TestCase):
    url = "/api/auth/logout/"

    def setUp(self):
        self.client = LoggingAPIClient()
        self.client._class_name = self.__class__.__name__
        self.client._test_name = self._testMethodName
        self.user = _make_verified_user()

    def test_logout_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

    def test_logout_unauthenticated_returns_403(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)


class ForgotPasswordViewTests(TestCase):
    url = "/api/auth/password/forgot/"

    def setUp(self):
        self.client = LoggingAPIClient()
        self.client._class_name = self.__class__.__name__
        self.client._test_name = self._testMethodName
        self.user = _make_verified_user()

    @patch("apps.accounts.services._send_mail")
    def test_forgot_password_existing_email_returns_200(self, mock_mail):
        response = self.client.post(self.url, {"email": "user@example.com"})
        self.assertEqual(response.status_code, 200)

    @patch("apps.accounts.services._send_mail")
    def test_forgot_password_sends_reset_email(self, mock_mail):
        self.client.post(self.url, {"email": "user@example.com"})
        mock_mail.assert_called_once()
        subject, _, recipient = mock_mail.call_args[0]
        self.assertIn("reset", subject.lower())
        self.assertEqual(recipient, "user@example.com")

    @patch("apps.accounts.services._send_mail")
    def test_forgot_password_nonexistent_email_still_returns_200(self, mock_mail):
        # Enum prevents email enumeration
        response = self.client.post(self.url, {"email": "nobody@example.com"})
        self.assertEqual(response.status_code, 200)
        mock_mail.assert_not_called()

    def test_forgot_password_missing_email_returns_400(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)


class ResetPasswordViewTests(TestCase):
    url = "/api/auth/password/reset/"

    def setUp(self):
        self.client = LoggingAPIClient()
        self.client._class_name = self.__class__.__name__
        self.client._test_name = self._testMethodName
        self.user = _make_verified_user()

    def _valid_params(self):
        return {
            "uid": encode_uid(self.user),
            "token": default_token_generator.make_token(self.user),
            "password": "NewStrongPass1!",
        }

    def test_reset_password_success_returns_200(self):
        response = self.client.post(self.url, self._valid_params())
        self.assertEqual(response.status_code, 200)

    def test_reset_password_actually_changes_password(self):
        self.client.post(self.url, self._valid_params())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass1!"))

    def test_reset_password_invalid_token_returns_400(self):
        response = self.client.post(self.url, {
            "uid": encode_uid(self.user),
            "token": "bad-token",
            "password": "NewStrongPass1!",
        })
        self.assertEqual(response.status_code, 400)

    def test_reset_password_invalid_uid_returns_400(self):
        response = self.client.post(self.url, {
            "uid": "notauid",
            "token": "sometoken",
            "password": "NewStrongPass1!",
        })
        self.assertEqual(response.status_code, 400)

    def test_reset_password_weak_password_returns_400(self):
        params = self._valid_params()
        params["password"] = "123"
        response = self.client.post(self.url, params)
        self.assertEqual(response.status_code, 400)

    def test_reset_password_token_reuse_returns_400(self):
        params = self._valid_params()
        self.client.post(self.url, params)
        response = self.client.post(self.url, params)
        self.assertEqual(response.status_code, 400)
