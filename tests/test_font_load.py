import pathlib, pytest

# 프로젝트 루트 = 현재 파일에서 두 단계 위
ROOT = pathlib.Path(__file__).resolve().parents[1]
FONTS_DIR = ROOT / "fonts"

@pytest.mark.skipif(not FONTS_DIR.exists(), reason="fonts/ directory absent")
def test_fonts_dir_exists():
    assert FONTS_DIR.is_dir()

@pytest.mark.skipif(not FONTS_DIR.exists(), reason="fonts/ directory absent")
def test_at_least_one_font():
    fonts = list(FONTS_DIR.glob("*.ttf"))
    assert fonts, "No .ttf fonts found in fonts/"


