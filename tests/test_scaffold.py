"""Tests for the initial project scaffold."""

import sys

import fs24_mod_manager


def test_supported_python_and_importable_package() -> None:
    assert sys.version_info >= (3, 13)
    assert fs24_mod_manager.__doc__
