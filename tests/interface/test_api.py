"""Tests for interface/api.py."""

import pytest

from memora.interface.api import MemoraStore


class TestMemoraStore:
    """Test MemoraStore API class."""

    def test_memora_store_exists(self):
        """Test that MemoraStore class exists."""
        assert MemoraStore is not None

    def test_memora_store_instantiation(self):
        """Test that MemoraStore can be instantiated."""
        store = MemoraStore()
        assert isinstance(store, MemoraStore)
