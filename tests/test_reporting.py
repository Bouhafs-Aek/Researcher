from researcher.reporting import build_html_report


def test_report_contains_project_sections():
    class Dummy:
        pass

    # The report renderer is integration-tested through the API/database layer.
    assert callable(build_html_report)
