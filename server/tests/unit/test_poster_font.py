"""No installed fonts, database or remote services required."""

from types import SimpleNamespace

import pytest

from app.core.errors import AppError, ErrorCode
from app.modules.workspace import media_service as media


def test_管理员字体优先且保留字号(monkeypatch, tmp_path):
    font_path = tmp_path / "custom-cjk.otf"
    font_path.write_bytes(b"synthetic-font")
    monkeypatch.setenv("AICARD_POSTER_FONT_PATH", str(font_path))
    calls = []
    sentinel = object()

    def load(path, size):
        calls.append((path, size))
        return sentinel

    monkeypatch.setattr(media.ImageFont, "truetype", load)
    assert media.poster_font(36) is sentinel
    assert calls == [(str(font_path), 36)]


@pytest.mark.parametrize(
    "path", ["C:/Windows/Fonts/msyh.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
)
def test_系统中文字体兼容Windows和Linux(monkeypatch, path):
    monkeypatch.delenv("AICARD_POSTER_FONT_PATH", raising=False)
    monkeypatch.setattr(media.Path, "is_file", lambda p: p.as_posix() == path)
    calls = []
    sentinel = object()
    monkeypatch.setattr(media.ImageFont, "truetype", lambda p, size: calls.append(p) or sentinel)
    assert media.poster_font() is sentinel
    assert [media.Path(p).as_posix() for p in calls] == [path]


@pytest.mark.parametrize(
    "configured", [None, "/missing/font.otf", "https://example.invalid/font.otf"]
)
def test_缺字体或错误配置不生成乱码海报(monkeypatch, configured):
    if configured is None:
        monkeypatch.delenv("AICARD_POSTER_FONT_PATH", raising=False)
    else:
        monkeypatch.setenv("AICARD_POSTER_FONT_PATH", configured)
    monkeypatch.setattr(media.Path, "is_file", lambda p: False)
    monkeypatch.setattr(
        media.ImageFont, "load_default", lambda **kw: pytest.fail("不可降级为默认字体")
    )
    monkeypatch.setattr(media, "root", lambda: pytest.fail("字体失败前不得写图片"))
    with pytest.raises(AppError) as error:
        media.create_share(SimpleNamespace(code="synthetic"))
    assert error.value.code == ErrorCode.INTERNAL_ERROR
    assert error.value.status == 503
    assert "中文字体" in error.value.message


def test_字体损坏返回明确安全错误(monkeypatch, tmp_path):
    path = tmp_path / "broken.ttf"
    path.write_bytes(b"not-a-font")
    monkeypatch.setenv("AICARD_POSTER_FONT_PATH", str(path))

    def broken(*args):
        raise OSError("private filesystem detail")

    monkeypatch.setattr(media.ImageFont, "truetype", broken)
    with pytest.raises(AppError) as error:
        media.poster_font()
    assert "private filesystem" not in error.value.message
