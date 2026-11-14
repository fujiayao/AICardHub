"""对运行中的本地API进行真实HTTP验收，不替换鉴权或数据库。"""

from __future__ import annotations

import json
import os
import secrets
import unittest
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("AICARD_API_URL", "http://127.0.0.1:8000")


def request(
    method: str, path: str, body: dict[str, Any] | None = None, token: str = ""
) -> tuple[int, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = Request(BASE + path, data=data, headers=headers, method=method)
    try:
        response = urlopen(req, timeout=40)
    except HTTPError as exc:
        response = exc
    with response:
        raw = response.read().decode("utf-8-sig")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw
        return response.status, payload


class LocalAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        credentials = json.loads(
            (ROOT / "server/local-credentials.json").read_text(encoding="utf-8-sig")
        )
        cls.credentials = credentials
        cls.tokens: dict[str, str] = {}
        for role in ("admin", "employee", "colleague"):
            account = credentials[role]
            endpoint = "/admin/auth/login" if role == "admin" else "/auth/login"
            status, payload = request(
                "POST",
                "/api/v1" + endpoint,
                {"phone": account["phone"], "password": account["password"]},
            )
            if status != 200:
                raise AssertionError(f"{role}登录失败：HTTP {status}，{payload}")
            cls.tokens[role] = payload["token"]

    def visitor(self) -> dict[str, Any]:
        status, payload = request("POST", "/api/v1/public/visitor/init", {})
        self.assertEqual(status, 200, payload)
        return payload

    def test_health_and_public_card(self) -> None:
        status, health = request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")
        status, card = request("GET", "/api/v1/public/cards/demo")
        self.assertEqual(status, 200, card)
        self.assertEqual(card["code"], "demo")
        self.assertEqual(card["status"], "active")
        for key in ("company", "assistant", "name", "products"):
            self.assertIn(key, card)

    def test_authentication_and_role_boundaries(self) -> None:
        for path in ("/me/card", "/me/leads", "/admin/employees"):
            status, _ = request("GET", "/api/v1" + path)
            self.assertIn(status, (401, 403))
        status, _ = request(
            "GET", "/api/v1/admin/employees", token=self.tokens["employee"]
        )
        self.assertEqual(status, 403)
        account = self.credentials["employee"]
        status, _ = request(
            "POST",
            "/api/v1/admin/auth/login",
            {"phone": account["phone"], "password": account["password"]},
        )
        self.assertIn(status, (401, 403))

    def test_visitor_token_cannot_be_staff_token(self) -> None:
        visitor = self.visitor()
        status, _ = request(
            "GET", "/api/v1/me/card", token=visitor["visitor_token"]
        )
        self.assertIn(status, (401, 403))
        status, _ = request(
            "POST",
            "/api/v1/public/chat/sessions",
            {"card_code": "demo"},
            self.tokens["employee"],
        )
        self.assertIn(status, (401, 403))

    def test_anonymous_id_does_not_restore_identity(self) -> None:
        first = self.visitor()
        status, other = request(
            "POST", "/api/v1/public/visitor/init", {"anon_id": first["anon_id"]}
        )
        if status == 200:
            self.assertNotEqual(other["anon_id"], first["anon_id"])
        else:
            self.assertIn(status, (400, 401, 422))

    def test_chat_history_isolated_between_visitors(self) -> None:
        first, other = self.visitor(), self.visitor()
        status, session = request(
            "POST",
            "/api/v1/public/chat/sessions",
            {"card_code": "demo"},
            first["visitor_token"],
        )
        self.assertEqual(status, 200, session)
        path = f"/api/v1/public/chat/sessions/{session['session_id']}/messages"
        status, _ = request("GET", path, token=other["visitor_token"])
        self.assertEqual(status, 404)
        status, _ = request(
            "POST", path, {"content": "测试"}, other["visitor_token"]
        )
        self.assertEqual(status, 404)

    def test_lead_requires_consent_and_employee_ownership(self) -> None:
        visitor = self.visitor()
        lead = {
            "card_code": "demo",
            "name": "本地验收访客",
            "phone": "13900009999",
            "company_name": "合成测试单位",
            "need": "本地自动验收，不是真实业务资料",
        }
        for consent in (None, False):
            data = dict(lead)
            if consent is not None:
                data["consent"] = consent
            status, _ = request(
                "POST", "/api/v1/public/leads", data, visitor["visitor_token"]
            )
            self.assertIn(status, (400, 422))
        lead["consent"] = True
        status, created = request(
            "POST", "/api/v1/public/leads", lead, visitor["visitor_token"]
        )
        self.assertIn(status, (200, 201), created)
        path = f"/api/v1/me/leads/{created['id']}"
        status, detail = request("GET", path, token=self.tokens["employee"])
        self.assertEqual(status, 200, detail)
        status, _ = request("GET", path, token=self.tokens["colleague"])
        self.assertEqual(status, 404)
        status, _ = request(
            "PATCH", path, {"status": "converted"}, self.tokens["colleague"]
        )
        self.assertEqual(status, 404)

    def test_lead_cannot_reference_another_visitors_session(self) -> None:
        first, other = self.visitor(), self.visitor()
        status, session = request(
            "POST",
            "/api/v1/public/chat/sessions",
            {"card_code": "demo"},
            first["visitor_token"],
        )
        self.assertEqual(status, 200, session)
        status, _ = request(
            "POST",
            "/api/v1/public/leads",
            {
                "card_code": "demo",
                "session_id": session["session_id"],
                "name": "隔离验收",
                "phone": "13900008888",
                "company_name": "合成数据",
                "need": "隔离验收",
                "consent": True,
            },
            other["visitor_token"],
        )
        self.assertEqual(status, 404)

    def test_sse_phone_only_prompts_without_creating_lead(self) -> None:
        status, before = request(
            "GET", "/api/v1/me/leads", token=self.tokens["employee"]
        )
        self.assertEqual(status, 200, before)
        visitor = self.visitor()
        status, session = request(
            "POST",
            "/api/v1/public/chat/sessions",
            {"card_code": "demo"},
            visitor["visitor_token"],
        )
        self.assertEqual(status, 200, session)
        status, stream = request(
            "POST",
            f"/api/v1/public/chat/sessions/{session['session_id']}/messages",
            {"content": "我的电话是13900007777，想了解演示功能"},
            visitor["visitor_token"],
        )
        self.assertEqual(status, 200, stream)
        self.assertIsInstance(stream, str)
        self.assertIn("event: done", stream)
        self.assertIn("event: lead_prompt", stream)
        status, after = request(
            "GET", "/api/v1/me/leads", token=self.tokens["employee"]
        )
        self.assertEqual(status, 200, after)
        self.assertEqual(after["total"], before["total"])

    def test_vcard_and_missing_card(self) -> None:
        status, card = request("GET", "/api/v1/public/cards/demo/vcard")
        self.assertEqual(status, 200)
        self.assertIn("BEGIN:VCARD", card)
        status, _ = request("GET", "/api/v1/public/cards/no-such-card")
        self.assertEqual(status, 404)

    def test_admin_creates_staff_and_requires_first_password_change(self) -> None:
        suffix = secrets.randbelow(100_000_000)
        phone = f"138{suffix:08d}"
        password = "Aa9" + secrets.token_hex(7)
        status, created = request(
            "POST",
            "/api/v1/admin/employees",
            {
                "name": "自动验收员工",
                "phone": phone,
                "dept": "合成测试",
                "title": "测试账号",
                "password": password,
            },
            self.tokens["admin"],
        )
        self.assertIn(status, (200, 201), created)
        status, login = request(
            "POST", "/api/v1/auth/login", {"phone": phone, "password": password}
        )
        self.assertEqual(status, 200, login)
        self.assertTrue(login["must_change_pwd"])
        token = login["token"]
        status, _ = request("GET", "/api/v1/me/leads", token=token)
        self.assertEqual(status, 403)
        new_password = "Bb8" + secrets.token_hex(7)
        status, changed = request(
            "POST",
            "/api/v1/auth/change-password",
            {"old_password": password, "new_password": new_password},
            token,
        )
        self.assertEqual(status, 200, changed)
        status, _ = request("GET", "/api/v1/me/card", token=token)
        self.assertEqual(status, 401, "改密后旧会话必须失效")
        status, relogin = request(
            "POST", "/api/v1/auth/login", {"phone": phone, "password": new_password}
        )
        self.assertEqual(status, 200, relogin)
        self.assertFalse(relogin["must_change_pwd"])
        token = relogin["token"]
        status, card = request("GET", "/api/v1/me/card", token=token)
        self.assertEqual(status, 200, card)
        self.assertEqual(card["name"], "自动验收员工")
        status, _ = request(
            "POST",
            f"/api/v1/admin/employees/{created['id']}/disable",
            {},
            self.tokens["admin"],
        )
        self.assertEqual(status, 200)
        status, _ = request("GET", "/api/v1/me/card", token=token)
        self.assertIn(status, (401, 403))

    def test_staff_card_changes_are_visible_publicly(self) -> None:
        status, original = request(
            "GET", "/api/v1/me/card", token=self.tokens["employee"]
        )
        self.assertEqual(status, 200, original)
        fields = ("display_title", "mobile", "email", "intro")
        previous = {key: original.get(key, "") for key in fields}
        changed = {**previous, "intro": "本地自动验收修改，测试完成后恢复。"}
        try:
            status, result = request(
                "PUT", "/api/v1/me/card", changed, self.tokens["employee"]
            )
            self.assertEqual(status, 200, result)
            status, public = request("GET", "/api/v1/public/cards/demo")
            self.assertEqual(status, 200)
            self.assertEqual(public["intro"], changed["intro"])
        finally:
            request("PUT", "/api/v1/me/card", previous, self.tokens["employee"])

    def test_knowledge_publish_revoke_and_staff_isolation(self) -> None:
        status, created = request(
            "POST",
            "/api/v1/admin/kb/files",
            {
                "title": "合成公开知识验收",
                "content": "合成验收资料：测试蓝鲸项目代号为验收专用，不代表公司业务。",
                "public": True,
                "approved": True,
            },
            self.tokens["admin"],
        )
        self.assertIn(status, (200, 201), created)
        file_id = created["file_id"]
        try:
            status, _ = request(
                "PUT",
                f"/api/v1/admin/kb/files/{file_id}",
                {
                    "title": created["title"],
                    "content": created["content"],
                    "public": False,
                    "approved": False,
                },
                self.tokens["admin"],
            )
            self.assertEqual(status, 200)
            status, revoked = request(
                "GET",
                f"/api/v1/admin/kb/files/{file_id}",
                token=self.tokens["admin"],
            )
            self.assertEqual(status, 200)
            self.assertFalse(revoked["public"])
            self.assertFalse(revoked["approved"])
        finally:
            request(
                "DELETE",
                f"/api/v1/admin/kb/files/{file_id}",
                token=self.tokens["admin"],
            )
        status, note = request(
            "POST",
            "/api/v1/me/kb/notes",
            {"title": "员工隔离验收", "content": "合成私有笔记"},
            self.tokens["employee"],
        )
        self.assertIn(status, (200, 201), note)
        try:
            status, _ = request(
                "GET",
                f"/api/v1/me/kb/notes/{note['file_id']}",
                token=self.tokens["colleague"],
            )
            self.assertEqual(status, 404)
        finally:
            request(
                "DELETE",
                f"/api/v1/me/kb/notes/{note['file_id']}",
                token=self.tokens["employee"],
            )


if __name__ == "__main__":
    import sys

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(LocalAcceptance)
    )
    report = {
        "scope": "真实本地HTTP与MySQL；模型按服务当前配置运行",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "passed": result.wasSuccessful(),
    }
    output = ROOT / "tasks/reports/local-api-acceptance.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(0 if result.wasSuccessful() else 1)
