"""Shared pytest configuration: skip network tests unless ESW_ALLOW_NETWORK=1."""

import os

import pytest


def pytest_collection_modifyitems(config, items):
    if os.environ.get("ESW_ALLOW_NETWORK") == "1":
        return
    skip = pytest.mark.skip(reason="network tests disabled (set ESW_ALLOW_NETWORK=1)")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)
