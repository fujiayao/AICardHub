"""Manual, real-provider black-box acceptance. Never imports application settings.

Run with the server environment's Python (httpx is an existing dependency).
No retries, provider/configuration writes, business-document reads or raw output.
"""
from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import time
from urllib.parse import quote, urlsplit

import httpx

ROOT = Path(__file__).resolve().parents[1]
API = "/api/v1"
CAP = 2 * 1024 * 1024
LOG = logging.getLogger("responses_acceptance")


class Failure(Exception):
    """Only fixed, non-sensitive codes may be supplied."""


class Blocked(Failure):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Failure(code)


def loopback_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        # Numeric IPs only: no DNS rebinding or proxy/localhost resolution.
        valid = ipaddress.ip_address(host).is_loopback
        port = parsed.port
        if not (valid and parsed.scheme in {"http", "https"} and port != 0):
            raise ValueError
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError
        if parsed.path not in {"", "/"} or "\\" in value:
            raise ValueError
        return value.rstrip("/")
    except ValueError:
        raise argparse.ArgumentTypeError("base-url must be a numeric loopback HTTP(S) origin") from None


def masked(value: object) -> bool:
    return value in (None, "") or (
        isinstance(value, str) and len(value) >= 3 and set(value) <= {"*", "•", "●"}
    )


def safe_configuration(value: object) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            name = str(key).lower()
            if any(word in name for word in ("api_key", "password", "secret", "token", "authorization")):
                if not masked(item):
                    return False
            elif not safe_configuration(item):
                return False
    elif isinstance(value, list):
        return all(safe_configuration(item) for item in value)
    return True


def real_model(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not any(
        marker in value.lower() for marker in ("fake", "policy", "演示", "mock")
    )


class Acceptance:
    def __init__(self, client: httpx.AsyncClient, report: dict, expect_mode: str = "real"):
        self.client = client
        self.report = report
        self.admin = ""
        self.file_id: str | None = None
        self.create_attempted = False
        self.models: set[str] = set()
        self.phase = "initialization"
        self.expect_mode = expect_mode
        self.primary_model = ""

    async def request(self, method: str, path: str, body=None, token="", statuses=(200,), capability=False):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with asyncio.timeout(15):
            async with self.client.stream(method, path, json=body, headers=headers) as response:
                if capability and response.status_code in (404, 405, 501):
                    raise Blocked("runtime_capability_endpoint_unavailable")
                require(response.status_code in statuses, "http_status_unexpected")
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    require(len(raw) <= CAP, "response_too_large")
        payload = json.loads(raw)
        require(isinstance(payload, dict), "json_object_required")
        return payload

    async def login(self, credentials: dict, role: str) -> str:
        account = credentials.get(role)
        require(isinstance(account, dict), "credential_role_missing")
        require(all(isinstance(account.get(k), str) and account[k] for k in ("phone", "password")),
                "credential_fields_invalid")
        endpoint = "/admin/auth/login" if role == "admin" else "/auth/login"
        result = await self.request("POST", API + endpoint,
                                    {k: account[k] for k in ("phone", "password")})
        require(result.get("must_change_pwd") is False, "password_change_required")
        token = result.get("token")
        require(isinstance(token, str) and bool(token), "login_token_missing")
        return token

    async def configuration(self) -> None:
        self.phase = "health"
        health = await self.request("GET", "/health")
        safe = safe_configuration(health)
        self.report["checks"]["health_secrets_masked"] = safe
        require(safe, "health_secret_exposure")
        require(health.get("status") == "ok", "health_not_ok")
        self.phase = "runtime_configuration"
        runtime = await self.request("GET", API + "/admin/runtime-settings",
                                     token=self.admin, capability=True)
        safe = safe_configuration(runtime)
        self.report["checks"]["runtime_secrets_masked"] = safe
        require(safe, "runtime_secret_exposure")
        settings = runtime.get("settings")
        if not isinstance(settings, dict):
            raise Blocked("runtime_settings_missing")
        for key in ("llm_api_key", "llm_fallback_api_key", "llm_tertiary_api_key"):
            require(key in settings and masked(settings[key]), "runtime_key_mask_contract")
            single = await self.request("GET", API + "/admin/settings/" + key, token=self.admin)
            require(single.get("key") == key and "value" in single, "setting_contract_invalid")
            safe = safe_configuration(single) and masked(single["value"])
            self.report["checks"][key + "_masked"] = safe
            require(safe, "setting_secret_exposure")
        is_real = settings.get("llm_mode") == "openai" and health.get("llm_mode") == "openai"
        self.report["checks"]["real_mode"] = is_real
        if self.expect_mode == "fake":
            if settings.get("llm_mode") != "fake" or health.get("llm_mode") != "fake":
                raise Blocked("fake_mode_not_enabled")
            self.report["checks"]["fake_configuration_only"] = True
            return
        if not is_real:
            raise Blocked("real_mode_not_enabled")
        # Explicit runtime evidence only. No inference from model names or SSE 200.
        protocol = settings.get("llm_api_mode")
        self.report["checks"]["responses_configured"] = protocol == "responses"
        if protocol != "responses":
            raise Blocked("responses_protocol_missing_or_not_enabled")
        self.report["protocol"] = "responses"
        require(real_model(settings.get("llm_model")), "primary_model_not_real")
        self.models.add(settings["llm_model"])
        self.primary_model = settings["llm_model"]
        fallback = settings.get("llm_fallback_enabled")
        require(isinstance(fallback, bool), "fallback_configuration_missing")
        if fallback:
            if settings.get("llm_fallback_api_mode") != "responses":
                raise Blocked("fallback_responses_protocol_unconfirmed")
            require(real_model(settings.get("llm_fallback_model")), "fallback_model_not_real")
            self.models.add(settings["llm_fallback_model"])
        tertiary = settings.get("llm_tertiary_enabled")
        require(isinstance(tertiary, bool), "tertiary_configuration_missing")
        if tertiary:
            if settings.get("llm_tertiary_api_mode") != "responses":
                raise Blocked("tertiary_responses_protocol_unconfirmed")
            require(real_model(settings.get("llm_tertiary_model")), "tertiary_model_not_real")
            self.models.add(settings["llm_tertiary_model"])
        self.report["runtime_models"] = sorted(self.models)
        self.report["checks"]["health_model_matches_runtime"] = health.get("model") in self.models
        require(health.get("model") in self.models, "health_runtime_model_mismatch")

    async def session(self) -> tuple[str, str]:
        visitor = await self.request("POST", API + "/public/visitor/init", {})
        token = visitor.get("visitor_token")
        require(isinstance(token, str) and bool(token), "visitor_token_missing")
        result = await self.request("POST", API + "/public/chat/sessions", {"card_code": "demo"}, token)
        session_id = result.get("session_id")
        require(isinstance(session_id, int) and not isinstance(session_id, bool) and session_id > 0,
                "session_id_invalid")
        self.report["created_session_ids"].append(session_id)
        return str(session_id), token

    async def stream(self, session_id: str, token: str, question: str, label: str) -> tuple[str, dict]:
        events: list[tuple[str, dict]] = []
        name, data = "message", []
        total = 0

        def dispatch() -> None:
            nonlocal name, data
            if data:
                value = json.loads("\n".join(data))
                require(isinstance(value, dict), "sse_data_not_object")
                events.append((name, value))
                require(len(events) <= 10000, "sse_event_limit")
            name, data = "message", []

        async with asyncio.timeout(55):
            async with self.client.stream(
                "POST", API + f"/public/chat/sessions/{session_id}/messages",
                json={"content": question},
                headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"},
            ) as response:
                require(response.status_code == 200, "sse_http_status_unexpected")
                require(response.headers.get("content-type", "").split(";")[0].strip() == "text/event-stream",
                        "sse_content_type_invalid")
                # Bound bytes before line parsing, including a malicious unterminated line.
                buffer = bytearray()
                first_line, after_cr = True, False
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    require(total <= CAP, "sse_too_large")
                    for byte in chunk:
                        if after_cr:
                            after_cr = False
                            if byte == 10:
                                continue
                        if byte not in (10, 13):
                            buffer.append(byte)
                            continue
                        after_cr = byte == 13
                        text = buffer.decode("utf-8")
                        buffer.clear()
                        if first_line:
                            text = text.removeprefix("﻿")
                            first_line = False
                        if not text:
                            dispatch()
                        elif not text.startswith(":"):
                            field, _, value = text.partition(":")
                            value = value[1:] if value.startswith(" ") else value
                            if field == "event":
                                name = value
                            elif field == "data":
                                data.append(value)
                require(not buffer and not data and name == "message", "sse_incomplete_final_frame")
        names = [event for event, _ in events]
        deltas = [payload.get("text") for event, payload in events if event == "delta"]
        dones = [payload for event, payload in events if event == "done"]
        summary = {
            "event_count": len(events), "delta_count": len(deltas),
            "done_count": len(dones), "error_count": names.count("error"),
            "complete_stream": True,
        }
        self.report["streams"][label] = summary
        require(not any(event not in {"delta", "done", "error", "lead_prompt"} for event in names),
                "sse_unknown_event")
        require("error" not in names, "sse_error_event")
        require(len(dones) == 1 and names[-1] == "done", "sse_done_count_or_order")
        require(bool(deltas) and all(isinstance(text, str) for text in deltas)
                and any(text.strip() for text in deltas), "sse_delta_missing")
        done = dones[0]
        require(isinstance(done.get("message_id"), int) and done["message_id"] > 0, "sse_message_id_missing")
        require(isinstance(done.get("nokb"), bool) and isinstance(done.get("kb_refs"), list),
                "sse_done_contract_invalid")
        require(all(isinstance(ref, str) for ref in done["kb_refs"]), "sse_refs_invalid")
        summary["real_model"] = real_model(done.get("model")) and done.get("model") in self.models
        # A policy rejection is valid for the no-knowledge control, never evidence of generation.
        if label == "grounded":
            require(summary["real_model"], "grounded_model_not_real_or_unconfigured")
            require(done.get("model") == self.primary_model, "primary_model_not_observed")
        if real_model(done.get("model")):
            summary["model"] = done["model"]
        else:
            require(summary["real_model"] or done.get("model") == "policy", "control_model_invalid")
        return "".join(deltas), done

    async def run(self, credentials: dict) -> None:
        self.phase = "admin_login"
        self.admin = await self.login(credentials, "admin")
        self.phase = "employee_login"
        await self.login(credentials, "employee")
        await self.configuration()
        if self.expect_mode == "fake":
            self.phase = "completed_fake_configuration_only"
            return
        nonce, answer = secrets.token_hex(16), "Z" + secrets.token_hex(12)
        self.phase = "synthetic_document_create"
        title = "合成验收星图 " + nonce
        content = f"仅为合成验收数据，不代表公司业务。星图标识 {nonce} 的观测校验值是 {answer}。"
        self.create_attempted = True
        created = await self.request("POST", API + "/admin/kb/files", {
            "title": title, "content": content, "public": True, "approved": True,
        }, self.admin, (200, 201))
        file_id = created.get("file_id")
        require(isinstance(file_id, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,160}", file_id)),
                "created_file_id_invalid_cleanup_unresolved")
        self.file_id = file_id  # Register immediately, before all publication assertions.
        self.report["created_file_ids"].append(file_id)
        require(created.get("public") is True and created.get("approved") is True,
                "synthetic_document_not_published")
        require(created.get("title") == title and created.get("content") == content,
                "created_document_mismatch")
        self.phase = "grounded_session"
        session_id, token = await self.session()
        self.phase = "grounded_stream"
        text, done = await self.stream(session_id, token, nonce, "grounded")
        checks = self.report["checks"]
        checks["synthetic_ref_present"] = file_id in done["kb_refs"]
        checks["synthetic_answer_present"] = answer in text
        require(checks["synthetic_ref_present"] and checks["synthetic_answer_present"]
                and done["nokb"] is False, "grounded_evidence_invalid")
        # Independent visitor AND session: no prior synthetic answer in control history.
        self.phase = "no_knowledge_session"
        session_id, token = await self.session()
        unknown = secrets.token_hex(24)
        self.phase = "no_knowledge_stream"
        text, done = await self.stream(session_id, token, unknown, "no_knowledge")
        checks["no_knowledge_empty_refs"] = done["kb_refs"] == []
        checks["no_knowledge_flag"] = done["nokb"] is True
        checks["no_knowledge_honest_text"] = any(marker in text for marker in (
            "没有", "不足", "未找到", "无法确认", "不清楚", "不知道", "需要确认", "不能确认",
            "not enough", "do not know", "don't know", "no information", "cannot confirm",
        )) and answer not in text
        require(all(checks[key] for key in (
            "no_knowledge_empty_refs", "no_knowledge_flag", "no_knowledge_honest_text",
        )), "no_knowledge_honesty_unproven_or_unrelated_retrieval")
        self.phase = "completed"

    async def cleanup(self) -> None:
        if self.file_id is None:
            if self.create_attempted:
                self.report["cleanup"]["success"] = False
                self.report["errors"].append({"phase": "cleanup", "code": "creation_outcome_unknown_no_owned_id"})
                self.report["status"] = "fail"
            return
        self.report["cleanup"]["attempted"] = True
        path = API + "/admin/kb/files/" + quote(self.file_id, safe="")
        try:
            async with asyncio.timeout(20):
                deleted = await self.request("DELETE", path, token=self.admin)
                require(deleted.get("ok") is True, "cleanup_delete_not_confirmed")
                async with self.client.stream("GET", path,
                    headers={"Authorization": f"Bearer {self.admin}"}) as response:
                    require(response.status_code == 404, "cleanup_absence_not_confirmed")
            self.report["cleanup"]["success"] = True
        except Exception:
            self.report["cleanup"]["success"] = False
            self.report["errors"].append({"phase": "cleanup", "code": "cleanup_failed"})
            self.report["status"] = "fail"


def atomic_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".responses-", delete=False) as output:
            temporary = output.name
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


async def execute(args: argparse.Namespace, report: dict) -> None:
    # 150s workload + <=20s cleanup; outer bound leaves reporting margin within 180s.
    async with asyncio.timeout(175):
        async with httpx.AsyncClient(base_url=args.base_url, trust_env=False,
                                    follow_redirects=False, timeout=httpx.Timeout(12),
                                    transport=httpx.AsyncHTTPTransport(retries=0)) as client:
            test = Acceptance(client, report, args.expect_mode)
            try:
                async with asyncio.timeout(150):
                    test.phase = "credentials_load"
                    require(args.credentials.stat().st_size <= 65536, "credentials_file_too_large")
                    credentials = json.loads(args.credentials.read_text(encoding="utf-8-sig"))
                    require(isinstance(credentials, dict), "credentials_format_invalid")
                    await test.run(credentials)
                    report["status"] = "pass"
            except Blocked as exc:
                report["status"] = "blocked"
                report["errors"].append({"phase": test.phase, "code": str(exc)})
            except Failure as exc:
                report["errors"].append({"phase": test.phase, "code": str(exc)})
            except TimeoutError:
                report["errors"].append({"phase": test.phase, "code": "deadline_exceeded"})
            except Exception:
                report["errors"].append({"phase": test.phase, "code": "request_or_input_failed"})
            finally:
                await test.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", type=loopback_url)
    parser.add_argument("--credentials", type=Path, default=ROOT / "server/local-credentials.json")
    parser.add_argument("--report", type=Path, default=ROOT / "tasks/reports/responses-acceptance.json")
    parser.add_argument("--expect-mode", choices=("real", "fake"), default="real",
                        help="real: require primary Responses generation; fake: configuration-only, no model claims")
    args = parser.parse_args()
    # Do not allow a typo to overwrite credentials, sources or this delivery report.
    if args.report.suffix.lower() != ".json" or args.report.resolve() == args.credentials.resolve():
        parser.error("report must be a separate .json file")
    if args.report.exists():
        parser.error("report already exists; choose a new output path")
    started = time.monotonic()
    report = {
        "status": "fail", "scope": "manual_real_provider_black_box" if args.expect_mode == "real" else "fake_configuration_only",
        "expected_mode": args.expect_mode,
        "checks": {}, "streams": {}, "errors": [],
        "created_file_ids": [], "created_session_ids": [],
        "cleanup": {"attempted": False, "success": None},
        "limitations": [
            "demo card receives synthetic sessions; no session-delete API, sessions retained",
            "protocol is runtime API declaration plus real generation, not provider wire capture",
            "enabled primary/fallback/tertiary llm_api_mode must be responses; no protocol downgrade required",
            "random control can retrieve fixed/company documents; this fails strict nokb/empty-refs checks",
            "honesty text heuristic is not semantic proof; no existing business documents are fetched",
            "lost create response can leave an unidentifiable synthetic document; never search/delete others",
        ],
    }
    try:
        asyncio.run(execute(args, report))
    except BaseException:
        report["status"] = "fail"
        report["errors"].append({"phase": "runner", "code": "interrupted_or_outer_deadline"})
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    try:
        atomic_report(args.report, report)
    except Exception:
        LOG.error("report_write_failed")
        return 1
    LOG.warning("acceptance_status=%s", report["status"])
    return 0 if report["status"] == "pass" and not report["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
