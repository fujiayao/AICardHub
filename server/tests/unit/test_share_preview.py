"""Regression for the actual HTML targets that caused the WeChat broken link."""

from html.parser import HTMLParser
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from app.core.db import get_db
from app.modules.workspace import router as routes
from app.modules.workspace import schemas as s
from app.modules.workspace import share_link_service as links


class PreviewParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "meta":
            self.meta[values.get("property") or values.get("name") or values.get("http-equiv")] = (
                values.get("content")
            )
        if tag == "a":
            self.hrefs.append(values.get("href"))


@pytest.mark.parametrize("prefix", ["", "/aicardhub"])
def test_微信实际HTML中的跳转和分享地址只含一次部署前缀(monkeypatch, prefix):
    monkeypatch.setattr(
        links,
        "get_settings",
        lambda: SimpleNamespace(public_base_url=f"https://cards.example{prefix}/"),
    )
    card = s.PublicCard(
        code="test",
        status="active",
        name='名字"<',
        title="职位",
        dept="部门",
        business_scope='业务"<',
        photo_url="/files/photo.jpg",
        company=s.CompanyData(name="企业", short_name="企业简称"),
    )
    location = f"{prefix}/card/test?s=link&e=7"
    page = links.share_preview_html(card, location)
    parser = PreviewParser()
    parser.feed(page)
    destination = f"https://cards.example{location}"
    assert parser.meta["og:url"] == destination
    assert parser.meta["refresh"] == f"0;url={destination}"
    assert parser.hrefs == [destination]
    assert parser.meta["og:image"] == f"https://cards.example{prefix}/c/test?image=1&s=poster&e=7"
    assert parser.meta["og:description"] == '业务"<'
    assert "<script" not in page
    assert "/aicardhub/aicardhub/" not in page


def test_已经包含部署前缀的图片地址不重复拼接(monkeypatch):
    monkeypatch.setattr(
        links,
        "get_settings",
        lambda: SimpleNamespace(public_base_url="https://cards.example/aicardhub/"),
    )
    assert (
        links._absolute_asset("/aicardhub/files/photo.jpg")
        == "https://cards.example/aicardhub/files/photo.jpg"
    )


@pytest.mark.parametrize("prefix", ["", "/aicardhub"])
@pytest.mark.parametrize("user_agent", ["MicroMessenger/8.0", "UnknownLinkCrawler/1.0"])
@pytest.mark.parametrize("status", ["active", "disabled"])
async def test_显式分享链接无需猜测爬虫UA且停用不暴露个人信息(
    monkeypatch, prefix, user_agent, status
):
    app = FastAPI()
    app.include_router(routes.public_redirect)

    async def database():
        yield object()

    async def by_code(db, code):
        assert code == "synthetic"

    async def public_card(db, code, campaign_id):
        return s.PublicCard(
            code=code,
            status=status,
            name="PERSONAL_SENTINEL",
            company=s.CompanyData(name="Company"),
        )

    app.dependency_overrides[get_db] = database
    monkeypatch.setattr(links.shared, "by_code", by_code)
    monkeypatch.setattr(links.shared, "public_card", public_card)
    monkeypatch.setattr(
        links,
        "get_settings",
        lambda: SimpleNamespace(public_base_url=f"https://cards.example{prefix}"),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, root_path=prefix), base_url="http://test"
    ) as client:
        response = await client.get(
            "/c/synthetic?s=link&preview=1", headers={"User-Agent": user_agent}
        )
    assert response.headers["vary"] == "Accept, User-Agent"
    if status == "disabled":
        assert response.status_code == 302
        assert response.headers["location"] == f"{prefix}/card/synthetic?s=link"
        assert "PERSONAL_SENTINEL" not in response.text
    else:
        assert response.status_code == 200
        assert "PERSONAL_SENTINEL" in response.text
        assert "style-src 'unsafe-inline'" in response.headers["content-security-policy"]
        parsed = PreviewParser()
        parsed.feed(response.text)
        assert (
            parsed.meta["refresh"] == f"0;url=https://cards.example{prefix}/card/synthetic?s=link"
        )
