"""Pure URL construction and the existing renderer share one public-link format."""

from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest
from PIL import ImageFont

from app.modules.workspace import media_service as media
from app.modules.workspace import share_link_service as links


@pytest.mark.parametrize(
    ("accept", "expected"),
    [
        ("", False),
        ("*/*", False),
        ("application/json", False),
        ("text/*", False),
        ("text/html;q=0", False),
        ("text/html;q=invalid", False),
        ("text/html", True),
        ("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", True),
        ("application/json,text/html;q=0.5", True),
    ],
)
def test_仅明确接受HTML时显示活动恢复页(accept, expected):
    assert links.accepts_html(accept) is expected


def test_活动恢复模板转义属性且编号不能注入脚本():
    location = "/aicardhub" + links.card_path('code"><script>alert(1)</script>', "nfc", short=False)
    page = links.campaign_recovery_html(location)
    assert "<script>" not in page
    assert 'href="/aicardhub/card/code%22%3E%3Cscript%3Ealert%281%29%3C%2Fscript%3E?s=nfc"' in page
    assert "&quot;" in links.campaign_recovery_html('/card/code?value="&other=<')


@pytest.mark.parametrize("base", ["https://cards.example", "https://cards.example/aicardhub/"])
@pytest.mark.parametrize("source", ["nfc", "qr", "poster", "link", "sig"])
@pytest.mark.parametrize("campaign_id", [None, 7])
def test_公开短链保留受控域名部署前缀来源和活动(monkeypatch, base, source, campaign_id):
    monkeypatch.setattr(links, "get_settings", lambda: SimpleNamespace(public_base_url=base))
    result = links.short_url("synthetic", source, campaign_id)
    parsed = urlsplit(result)
    assert parsed.scheme == "https" and parsed.netloc == "cards.example"
    assert parsed.path == urlsplit(base).path.rstrip("/") + "/c/synthetic"
    assert parse_qs(parsed.query) == {
        "s": [source],
        **({"e": [str(campaign_id)]} if campaign_id is not None else {}),
    }


def test_编码名片编号不能注入路径参数或外部跳转(monkeypatch):
    monkeypatch.setattr(
        links, "get_settings", lambda: SimpleNamespace(public_base_url="https://cards.example")
    )
    result = links.short_url("//evil.test/?s=qr&redirect=https://evil.test#fragment", "nfc")
    parsed = urlsplit(result)
    assert parsed.netloc == "cards.example"
    assert parsed.path.startswith("/c/%2F%2Fevil.test%2F%3F")
    assert parsed.query == "s=nfc" and not parsed.fragment


@pytest.mark.parametrize("base", ["https://cards.example/", "https://cards.example/aicardhub/"])
def test_原图片分享与轻量链接共用来源和活动格式(monkeypatch, tmp_path, base):
    monkeypatch.setattr(links, "get_settings", lambda: SimpleNamespace(public_base_url=base))
    monkeypatch.setattr(media, "root", lambda: tmp_path)
    monkeypatch.setattr(media, "poster_font", lambda: ImageFont.load_default())
    original = media.qrcode.make
    qr_payloads = []

    def capture(value, **kwargs):
        qr_payloads.append(value)
        return original(value, **kwargs)

    monkeypatch.setattr(media.qrcode, "make", capture)
    result = media.create_share(
        SimpleNamespace(code="synthetic", name="Synthetic", display_title="Staff", photo_url=""),
        "nfc",
        7,
    )
    assert result.short_url == links.short_url("synthetic", "nfc", 7)
    assert qr_payloads == [
        links.short_url("synthetic", "qr", 7),
        links.short_url("synthetic", "poster", 7),
    ]
    assert (tmp_path / result.qr_url.rsplit("/", 1)[1]).is_file()
    assert (tmp_path / result.poster_url.rsplit("/", 1)[1]).is_file()
