"""Pytest configuration and shared fixtures for Zero Action tests."""

import os
import shutil
import tempfile
from pathlib import Path
import pytest
from loguru import logger


@pytest.fixture
def temp_zero_dir():
    """Create a temporary directory to isolate configuration and logs.

    Mocks the ZERO_HOME environment variable and cleans up open file handles
    upon teardown to prevent file-locking issues on Windows.
    """
    temp_dir = tempfile.mkdtemp()
    old_zero_home = os.environ.get("ZERO_HOME")
    os.environ["ZERO_HOME"] = temp_dir

    yield Path(temp_dir)

    # Release open log file handles
    logger.remove()

    if old_zero_home is not None:
        os.environ["ZERO_HOME"] = old_zero_home
    else:
        os.environ.pop("ZERO_HOME", None)

    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass
