from oceanofpdf_downloader.utils import rename_file


def test_rename_file_strips_prefix():
    assert rename_file("_OceanofPDF.com_Sweet_Temptation.pdf") == "Sweet_Temptation.pdf"


def test_rename_file_no_prefix():
    assert rename_file("Sweet_Temptation.pdf") == "Sweet_Temptation.pdf"


def test_rename_file_empty():
    assert rename_file("") == ""


def test_rename_file_epub():
    assert rename_file("_OceanofPDF.com_My_Book.epub") == "My_Book.epub"
