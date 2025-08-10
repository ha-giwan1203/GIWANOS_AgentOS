import pathlib, shutil
from scripts.generate_pdf_report import generate

def test_pdf_generate(tmp_path: pathlib.Path):
    # generate() 는 project 루트 기준 경로를 반환 → 임시 디렉터리로 우회
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    # monkeypatch DST 경로
    import scripts.generate_pdf_report as g
    g.DST = reports_dir

    pdf_path = generate()
    assert pdf_path.exists()
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.stat().st_size > 0


