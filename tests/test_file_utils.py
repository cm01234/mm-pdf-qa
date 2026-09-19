from file_utils import sanitize_filename


def test_sanitize_filename_removes_path_components_and_unsafe_characters():
    assert sanitize_filename("../quarterly report (final).pdf") == "quarterly_report_final.pdf"


def test_sanitize_filename_handles_windows_paths_and_missing_names():
    assert sanitize_filename(r"C:\reports\Q1.pdf") == "Q1.pdf"
    assert sanitize_filename("...pdf") == "uploaded.pdf"
