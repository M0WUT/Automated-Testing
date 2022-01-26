import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--skipPSU",
        action="store_true",
        default=False,
        help="Skip Long PSU specific tests",
    )

    parser.addoption(
        "--skipSmb100a",
        action="store_true",
        default=False,
        help="Skip Long SMB100A specific tests",
    )

    parser.addoption(
        "--skipSdg2122x",
        action="store_true",
        default=False,
        help="Skip Long SDG2122X specific tests",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "psu: mark test as PSU specific")

    config.addinivalue_line("markers", "smb100a: mark test as SMB100a specific")

    config.addinivalue_line("markers", "sdg2122x: mark test as SDG2122X specific")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--skipPSU"):
        skip_list = pytest.mark.skip(reason="Skipping Long PSU specific tests")
        for item in items:
            if "psu" in item.keywords:
                item.add_marker(skip_list)

    if config.getoption("--skipSmb100a"):
        skip_list = pytest.mark.skip(reason="Skipping Long SMB100A specific tests")
        for item in items:
            if "smb100a" in item.keywords:
                item.add_marker(skip_list)
    if config.getoption("--skipSdg2122x"):
        skip_list = pytest.mark.skip(reason="Skipping Long SDG2122X specific tests")
        for item in items:
            if "sdg2122x" in item.keywords:
                item.add_marker(skip_list)
    return
