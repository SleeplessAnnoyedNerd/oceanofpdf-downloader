from oceanofpdf_downloader.utils import rename_file


def test_rename_file_returns_same():
    assert rename_file("Sweet_Temptation_-_Cora_Kent.pdf") == "Sweet_Temptation_-_Cora_Kent.pdf"


def test_rename_file_empty():
    assert rename_file("") == ""
