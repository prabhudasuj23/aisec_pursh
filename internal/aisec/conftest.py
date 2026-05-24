"""
Pytest conftest.py — adds aisec/app to sys.path so tests can import `app.*`
without requiring an editable install.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "app"))
