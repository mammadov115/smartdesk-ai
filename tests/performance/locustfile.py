"""
Locust performance test suite for the SmartDesk AI API.

Covers:
  - REST API endpoints (auth, company profile, billing, chat, knowledge, analytics)
  - WebSocket connections (customer chat consumer)

Usage:
  # Interactive web UI — open http://localhost:8089 in a browser
  make perf-test

  # Headless — 100 users, 10 spawns/s, 60 s duration
  make perf-test-headless

Environment variables:
  LOCUST_HOST       Base URL of the server        (default: http://localhost:8000)
  LOCUST_EMAIL      Test account email             (default: alice@example.com)
  LOCUST_PASSWORD   Test account password          (default: StrongPass1!)
"""

import os
import random
import time

import websocket
from locust import HttpUser, between, events, task

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TEST_EMAIL = os.getenv("LOCUST_EMAIL", "alice@example.com")
TEST_PASSWORD = os.getenv("LOCUST_PASSWORD", "NewStrongPass1!")

SAMPLE_QUESTIONS = [
    "What is your return policy?",
    "How do I reset my password?",
    "What are your business hours?",
    "Can I get a refund?",
    "How do I contact support?",
    "Tell me about your pricing plans.",
    "Do you offer a free trial?",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fire_ws_event(
    name: str, start: float, exc: Exception | None = None, length: int = 0
) -> None:
    """Report a WebSocket timing to Locust's event system."""
    events.request.fire(
        request_type="WebSocket",
        name=name,
        response_time=(time.time() - start) * 1000,
        response_length=length,
        exception=exc,
    )


# ---------------------------------------------------------------------------
# REST API user  (80 % of virtual users)
# ---------------------------------------------------------------------------


class ApiUser(HttpUser):
    """
    Simulates a logged-in company owner working through the REST API.

    Task weights reflect a realistic mix:
      - Reading chat sessions and asking questions is the hottest path.
      - Profile / billing / analytics are read much less frequently.
    """

    weight = 4  # 4 : 1 ratio vs WebSocketUser
    wait_time = between(1, 3)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_start(self) -> None:
        self.token: str | None = None
        self.session_id: int | None = None
        self._login()

    def _login(self) -> None:
        with self.client.post(
            "/api/auth/login/",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json()["access"]
                resp.success()
            else:
                resp.failure(
                    f"Login failed {resp.status_code} — "
                    f"check LOCUST_EMAIL / LOCUST_PASSWORD and that the account is active"
                )

    @property
    def _auth(self) -> dict | None:
        if not self.token:
            return None
        return {"Authorization": f"Bearer {self.token}"}

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @task(3)
    def get_company_profile(self) -> None:
        if not self._auth:
            return
        self.client.get("/api/company/me/", headers=self._auth)

    @task(2)
    def get_billing_usage(self) -> None:
        if not self._auth:
            return
        self.client.get("/api/billing/usage/", headers=self._auth)

    @task(1)
    def get_invoices(self) -> None:
        if not self._auth:
            return
        self.client.get("/api/billing/invoices/", headers=self._auth)

    @task(4)
    def list_chat_sessions(self) -> None:
        if not self._auth:
            return
        self.client.get("/api/chat/sessions/", headers=self._auth)

    @task(6)
    def create_session_and_ask(self) -> None:
        """Create a chat session and immediately send one question."""
        if not self._auth:
            return
        resp = self.client.post(
            "/api/chat/sessions/",
            headers=self._auth,
            json={},
        )
        if not resp.ok:
            return

        session_id = resp.json().get("id")
        if not session_id:
            return

        self.session_id = session_id
        self.client.post(
            f"/api/chat/sessions/{session_id}/ask/",
            headers=self._auth,
            json={"question": random.choice(SAMPLE_QUESTIONS)},
            name="/api/chat/sessions/[id]/ask/",
        )

    @task(2)
    def list_knowledge_documents(self) -> None:
        if not self._auth:
            return
        self.client.get("/api/knowledge/documents/", headers=self._auth)

    @task(2)
    def get_analytics_stats(self) -> None:
        if not self._auth:
            return
        self.client.get("/api/analytics/stats/", headers=self._auth)

    @task(1)
    def get_analytics_conversations(self) -> None:
        if not self._auth:
            return
        self.client.get("/api/analytics/conversations/", headers=self._auth)


# ---------------------------------------------------------------------------
# WebSocket user  (20 % of virtual users)
# ---------------------------------------------------------------------------


class WebSocketUser(HttpUser):
    """
    Simulates a customer connecting to the chat widget via WebSocket.

    Flow per task execution:
      1. Create a new chat session (HTTP).
      2. Open ws://…/ws/chat/<session_id>/?token=<jwt>.
      3. Stay connected for ~3 s (mimicking a user reading the greeting).
      4. Close the connection.
    """

    weight = 1
    wait_time = between(2, 5)

    def on_start(self) -> None:
        self.token: str | None = None
        self._login()

    def _login(self) -> None:
        with self.client.post(
            "/api/auth/login/",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json()["access"]
                resp.success()
            else:
                resp.failure(
                    f"Login failed {resp.status_code} — "
                    f"check LOCUST_EMAIL / LOCUST_PASSWORD and that the account is active"
                )

    @task
    def websocket_chat_session(self) -> None:
        if not self.token:
            return

        # Step 1 — create a session over HTTP
        resp = self.client.post(
            "/api/chat/sessions/",
            headers={"Authorization": f"Bearer {self.token}"},
            json={},
        )
        if not resp.ok:
            return

        session_id = resp.json().get("id")
        if not session_id:
            return

        # Step 2 — open WebSocket
        ws_base = self.host.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        url = f"{ws_base}/ws/chat/{session_id}/?token={self.token}"
        start = time.time()

        try:
            ws = websocket.create_connection(url, timeout=10)
        except Exception as exc:
            _fire_ws_event("ws/chat/[id]/ connect", start, exc)
            return

        _fire_ws_event("ws/chat/[id]/ connect", start)

        # Step 3 — stay connected briefly; drain any server-pushed frames
        read_start = time.time()
        ws.settimeout(3)
        try:
            raw = ws.recv()
            _fire_ws_event(
                "ws/chat/[id]/ receive", read_start, length=len(raw)
            )
        except websocket.WebSocketTimeoutException:
            pass  # no push within timeout — normal when session just opened
        except Exception as exc:
            _fire_ws_event("ws/chat/[id]/ receive", read_start, exc)

        # Step 4 — close
        ws.close()
