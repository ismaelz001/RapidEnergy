import os
import sys


def pytest_configure():
    # Ensure repository root is on sys.path so imports like `from app...` work
    # regardless of how pytest is invoked.
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

