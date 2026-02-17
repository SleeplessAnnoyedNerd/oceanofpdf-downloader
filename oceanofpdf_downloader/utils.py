def rename_file(filename: str) -> str:
    """Rename a downloaded file by stripping the _OceanofPDF.com_ prefix."""
    return filename.replace("_OceanofPDF.com_", "")
