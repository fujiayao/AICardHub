"""Synthetic evaluation evidence tests; no real provider requests in automation."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from app.integrations.llm.client import FakeLLMClient
from app.kb.evaluate import (
    SAMPLE_VERSION,
    TARGETS,
    _checks,
    digest,
    evaluate,
    grade_report,
    main,
    samples,
    seal,
)


@pytest.mark.asyncio
async def test_Fake报告只声称边界检查而不生成语义正确率() -> None:
    fake = FakeLLMClient(reply="这段答复故意不含题目所问事实")
    report = await evaluate(client=fake)
    assert report["mode"] == report["provider_kind"] == "fake"
    assert report["sample_version"] == SAMPLE_VERSION
    assert report["sample_hash"] == digest(samples())
    assert report["denominator"] == 14
    assert report["category_denominators"] == {
        "quote_refusal": 3,
        "knowledge_correctness": 3,
        "general_assistance": 3,
        "boundary": 5,
    }
    assert report["automatic_summary"]["passed"] == 14
    assert report["automatic_summary"]["measurement"] == "protocol_boundary_only"
    assert report["semantic_metrics"] == {}
    assert report["semantic_status"] == "not_applicable_fake"
    assert report["real_execution"] == "unverified_not_run"
    assert "accuracy" not in json.dumps(report)
    # A clearly non-answer still passes protocol checks; it is never semantic success.
    assert len(fake.calls) == 14


@pytest.mark.asyncio
@pytest.mark.parametrize("nokb", [False, True])
async def test_资料缺失允许模型诚实标记且不泄露未选资料(nokb: bool) -> None:
    fake = FakeLLMClient(reply="资料不足，需要本人确认" + ("<<NOKB>>" if nokb else ""))
    report = await evaluate(
        "real", client=fake, case_ids=["boundary-01", "boundary-02", "boundary-03"]
    )
    assert len(fake.calls) == 3
    assert report["automatic_summary"]["passed"] == 3
    assert report["semantic_metrics"] == {}
    assert report["semantic_status"] == "not_applicable_fake"
    assert "虚构灯塔沙盒只支持" not in json.dumps(fake.calls, ensure_ascii=False)
    for record in report["records"]:
        assert record["events"][-1]["data"]["nokb"] is nokb
        assert record["events"][-1]["data"]["kb_refs"] == []
        assert "<<NOKB>>" not in record["response"]


@pytest.mark.parametrize(
    ("nokb", "refs", "valid"),
    [
        (False, ["synthetic-lantern"], True),
        (True, [], True),
        (True, ["synthetic-lantern"], False),
        (False, ["unselected-file"], False),
        (False, [], False),
        ("false", ["synthetic-lantern"], False),
        (None, ["synthetic-lantern"], False),
    ],
)
def test_引用限于选中资料且NOKB必须为布尔值(nokb, refs, valid) -> None:
    case = next(case for case in samples() if case["id"] == "knowledge-01")
    case["used_refs"] = ["synthetic-lantern"]
    events = [
        {"event": "delta", "data": {"text": "合成答复"}},
        {"event": "done", "data": {"nokb": nokb, "kb_refs": refs, "model": "fake"}},
    ]
    assert all(_checks(case, events, "合成答复").values()) is valid


@pytest.mark.asyncio
async def test_选择题目保留完整样本哈希但单独记录选择和分母() -> None:
    report = await evaluate(case_ids=["knowledge-01", "quote-01"])
    assert report["denominator"] == 2 and report["total_sample_count"] == 14
    assert report["selected_ids"] == ["quote-01", "knowledge-01"]
    assert report["sample_hash"] == digest(samples())
    assert report["selection_hash"] != report["sample_hash"]
    changed = samples()
    changed[0]["expected_behavior"] += "变更"
    assert digest(changed) != report["sample_hash"]


@pytest.mark.asyncio
async def test_失败题仍计入分母并保留安全错误() -> None:
    fake = FakeLLMClient(fail_after=0, error=RuntimeError("fake-secret-header"))
    report = await evaluate(client=fake, case_ids=["quote-01", "knowledge-01"])
    assert report["denominator"] == 2
    assert report["automatic_summary"]["passed"] == 0
    assert report["automatic_summary"]["failed"] == 2
    assert report["records"][1]["status"] == "failed"
    assert "fake-secret-header" not in json.dumps(report)
    assert "accuracy" not in json.dumps(report)


@pytest.mark.asyncio
async def test_总预算到期仍为未执行题保留分母并关闭流() -> None:
    # Warm tokenizer initialization so this test reaches provider iteration before
    # its deliberately short deadline, independently of execution order/coverage.
    await evaluate(case_ids=["knowledge-01"])
    fake = FakeLLMClient(delay=1)
    report = await evaluate(
        client=fake, case_ids=["knowledge-01", "knowledge-02"], budget_seconds=0.2
    )
    assert report["denominator"] == len(report["records"]) == 2
    assert all(record["failure"] == "run_deadline_exceeded" for record in report["records"])
    assert fake.closed_streams == 1


@pytest.mark.asyncio
async def test_取消向上传播并关闭流() -> None:
    fake = FakeLLMClient(delay=10)
    task = asyncio.create_task(evaluate(client=fake, case_ids=["knowledge-01"]))
    try:
        await asyncio.wait_for(fake.stream_started.wait(), timeout=5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    assert fake.closed_streams == 1


@pytest.mark.asyncio
async def test_real缺少独立路由配置明确未验证且不回退Fake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for suffix in ("BASE_URL", "API_KEY", "MODEL"):
        monkeypatch.delenv("EVAL_TEST_" + suffix, raising=False)
    monkeypatch.setenv("LLM_API_KEY", "must-not-read-shared-setting")
    report = await evaluate("real", route="test")
    assert report["real_execution"] == "unverified_not_run"
    assert report["provider_kind"] == "not_configured"
    assert report["configuration_error"] == "missing_route_environment"
    assert report["records"] == [] and report["denominator"] == 14
    assert "must-not-read" not in json.dumps(report)


@pytest.mark.asyncio
async def test_real参数配Fake也不能声称真实执行或人工正确率() -> None:
    report = await evaluate("real", client=FakeLLMClient(), case_ids=["knowledge-01"])
    assert report["provider_kind"] == "fake"
    assert report["real_execution"] == "unverified_not_run"
    with pytest.raises(ValueError, match="real-mode"):
        grade_report(report, {})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "unknown"},
        {"budget_seconds": 46},
        {"budget_seconds": 0},
        {"budget_seconds": float("nan")},
        {"budget_seconds": float("inf")},
        {"route": "../secret"},
        {"case_ids": []},
        {"case_ids": ["unknown"]},
        {"case_ids": ["quote-01", "quote-01"]},
    ],
)
async def test_拒绝无效评测参数(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        await evaluate(**kwargs)


@pytest.fixture
async def real_evidence() -> dict[str, Any]:
    # Explicit report fixture for scoring, not a real provider execution claim.
    report = await evaluate()
    report.update(
        mode="real",
        provider_kind="real",
        real_execution="completed",
        semantic_status="unverified_pending_human",
    )
    return seal(report)


def decisions_for(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_hash": report["report_hash"],
        "sample_hash": report["sample_hash"],
        "reviewer": "synthetic-test-reviewer",
        "decisions": [
            {
                "id": record["id"],
                "answer_hash": record["answer_hash"],
                "passed": True,
                "rationale": "仅用于评分逻辑的合成判分记录",
            }
            for record in report["records"]
            if record["category"] in TARGETS
        ],
    }


@pytest.mark.asyncio
async def test_仅明确人工完整判分生成各类别accuracy(
    real_evidence: dict[str, Any],
) -> None:
    grades = decisions_for(real_evidence)
    original = deepcopy(real_evidence)
    graded = grade_report(real_evidence, grades)
    assert real_evidence == original
    assert graded["source_report_hash"] == original["report_hash"]
    assert graded["semantic_status"] == "human_reviewed"
    for metric in graded["semantic_metrics"].values():
        assert metric["denominator"] == metric["reviewed"] == metric["passed"] == 3
        assert metric["accuracy"] == 1.0 and metric["status"] == "met"
    assert graded["targets"] == {
        "quote_refusal": 1.0,
        "knowledge_correctness": 0.9,
        "general_assistance": 0.95,
    }


@pytest.mark.asyncio
async def test_部分评分和缺失类别不给accuracy(real_evidence: dict[str, Any]) -> None:
    grades = decisions_for(real_evidence)
    grades["decisions"] = grades["decisions"][:1]
    graded = grade_report(real_evidence, grades)
    assert graded["semantic_status"] == "unverified_partial_human_review"
    assert all("accuracy" not in metric for metric in graded["semantic_metrics"].values())
    assert graded["semantic_metrics"]["quote_refusal"]["denominator"] == 3
    assert graded["semantic_metrics"]["quote_refusal"]["reviewed"] == 1


@pytest.mark.asyncio
async def test_人工失败计入完整分母且低于门槛(real_evidence: dict[str, Any]) -> None:
    grades = decisions_for(real_evidence)
    grades["decisions"][0]["passed"] = False
    graded = grade_report(real_evidence, grades)
    metric = graded["semantic_metrics"]["quote_refusal"]
    assert metric["accuracy"] == 2 / 3 and metric["denominator"] == 3
    assert metric["status"] == "below_target"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutation",
    [
        "report_hash",
        "sample_hash",
        "reviewer",
        "answer_hash",
        "rationale",
        "passed",
        "duplicate",
        "unknown",
        "boundary",
    ],
)
async def test_拒绝错配空理由伪造类型和重复人工评分(
    real_evidence: dict[str, Any], mutation: str
) -> None:
    grades = decisions_for(real_evidence)
    if mutation in {"report_hash", "sample_hash"}:
        grades[mutation] = "mismatch"
    elif mutation == "reviewer":
        grades["reviewer"] = " "
    elif mutation == "duplicate":
        grades["decisions"].append(deepcopy(grades["decisions"][0]))
    elif mutation == "unknown":
        grades["decisions"][0]["id"] = "unknown"
    elif mutation == "boundary":
        grades["decisions"][0]["id"] = "boundary-01"
    else:
        grades["decisions"][0][mutation] = (
            "mismatch" if mutation == "answer_hash" else " " if mutation == "rationale" else "true"
        )
    with pytest.raises(ValueError):
        grade_report(real_evidence, grades)


@pytest.mark.asyncio
async def test_修改报告或换版本后不能套用原评分(real_evidence: dict[str, Any]) -> None:
    grades = decisions_for(real_evidence)
    real_evidence["records"][0]["response"] = "已改变"
    with pytest.raises(ValueError, match="Report hash"):
        grade_report(real_evidence, grades)
    real_evidence["sample_version"] = "old-version"
    seal(real_evidence)
    with pytest.raises(ValueError, match="Sample version"):
        grade_report(real_evidence, grades)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutation", ["denominator", "selection_hash", "category", "response", "duplicate"]
)
async def test_重算报告哈希也不能绕过题目答复与分母校验(
    real_evidence: dict[str, Any], mutation: str
) -> None:
    if mutation == "denominator":
        real_evidence["denominator"] = 1
    elif mutation == "selection_hash":
        real_evidence["selection_hash"] = "changed"
    elif mutation == "duplicate":
        real_evidence["records"].append(deepcopy(real_evidence["records"][0]))
    else:
        real_evidence["records"][0][mutation] = "changed"
    seal(real_evidence)
    with pytest.raises(ValueError):
        grade_report(real_evidence, decisions_for(real_evidence))


def test_CLI输出合法JSON且不读取工作目录dotenv(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "EVAL_BASE_URL=PRIVATE_SENTINEL\nEVAL_API_KEY=PRIVATE_SENTINEL\n",
        encoding="utf-8",
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    environment["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-m", "app.kb.evaluate", "run", "--mode", "fake"],
        cwd=tmp_path,
        check=False,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=45,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["automatic_summary"]["passed"] == 14
    assert "PRIVATE_SENTINEL" not in result.stdout + result.stderr


def test_CLI真实未配置与无效参数有非零退出码(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for suffix in ("BASE_URL", "API_KEY", "MODEL"):
        monkeypatch.delenv("EVAL_EMPTY_" + suffix, raising=False)
    assert main(["run", "--mode", "real", "--route", "empty"]) == 2
    assert json.loads(capsys.readouterr().out)["real_execution"] == "unverified_not_run"
    assert main(["run", "--case", "unknown"]) == 2
    assert "invalid configuration" in capsys.readouterr().err


@pytest.mark.asyncio
async def test_评分CLI读取明确文件并按门槛返回状态(
    real_evidence: dict[str, Any], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report_path, grades_path = tmp_path / "report.json", tmp_path / "grades.json"
    report_path.write_text(json.dumps(real_evidence), encoding="utf-8")
    grades = decisions_for(real_evidence)
    grades["decisions"][0]["passed"] = False
    grades_path.write_text(json.dumps(grades), encoding="utf-8")
    assert main(["score", "--report", str(report_path), "--grades", str(grades_path)]) == 1
    assert (
        json.loads(capsys.readouterr().out)["semantic_metrics"]["quote_refusal"]["status"]
        == "below_target"
    )
