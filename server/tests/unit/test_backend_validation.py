import pytest
from pydantic import ValidationError

from app.core.validation import safe_url
from app.modules.chat.stream_filter import MarkerFilter
from app.modules.workspace import schemas as s


@pytest.mark.parametrize(
    "url", ["", "/files/abc.jpg", "https://example.com/a", "http://localhost:8000/a"]
)
def test_允许安全图片和网站链接(url: str) -> None:
    assert safe_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,x",
        "file:///etc/passwd",
        "//evil.test/a",
        "/files/../.env",
        "/files/%2e%2e/.env",
        "/files/a\\b",
        "https://user:password@example.com",
        "https://example.com/\nx",
    ],
)
def test_拒绝危险链接(url: str) -> None:
    with pytest.raises(ValueError):
        s.CardInput(photo_url=url)
    with pytest.raises(ValueError):
        s.ProductInput(title="test", image_url=url)
    with pytest.raises(ValueError):
        s.CompanyData(name="test", website=url)


@pytest.mark.parametrize("password", ["密" * 25, "a" * 73])
def test_密码限制按UTF8字节检查(password: str) -> None:
    with pytest.raises(ValidationError):
        s.LoginInput(phone="13800009999", password=password)
    with pytest.raises(ValidationError):
        s.ResetPassword(password=password)


@pytest.mark.parametrize(
    "parts",
    [["hello<<NO", "KB>>world"], ["hello<", "<NOK", "B>>world"], ["hello", "<<NOKB>>", "world"]],
)
def test_内部标记拆包不泄露(parts: list[str]) -> None:
    filter_ = MarkerFilter()
    text = "".join(filter_.feed(part) for part in parts) + filter_.feed("", final=True)
    assert text == "helloworld"
    assert filter_.nokb


def test_员工无法修改锁定字段且留资必须明确同意() -> None:
    with pytest.raises(ValidationError):
        s.CardInput.model_validate({"dept": "越权部门"})
    for consent in [False, None, "true"]:
        with pytest.raises(ValidationError):
            s.LeadInput.model_validate(
                {
                    "name": "合成访客",
                    "phone": "13800009999",
                    "card_code": "demo",
                    "consent": consent,
                }
            )
