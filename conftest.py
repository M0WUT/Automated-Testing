import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--skipPSU",
        action="store_true",
        default=False,
        help="Skip Long PSU specific tests"
    )

    parser.addoption(
        "--skipSiggen",
        action="store_true",
        default=False,
        help="Skip Long Signal Generator specific tests"
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "psu: mark test as PSU specific"
    )

    config.addinivalue_line(
        "markers",
        "siggen: mark test as Signal Generator specific"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skipPSU"):
        skip_list = pytest.mark.skip(
            reason="Skipping Long PSU specific tests"
        )
        for item in items:
            if "psu" in item.keywords:
                item.add_marker(skip_list)

    if config.getoption("--skipSiggen"):
        skip_list = pytest.mark.skip(
            reason="Skipping Long Signal Generator specific tests"
        )
        for item in items:
            if "siggen" in item.keywords:
                item.add_marker(skip_list)
    return
