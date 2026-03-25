"""Tests for memora package __init__.py."""


def test_memora_store_import():
    """Test that MemoraStore can be imported from memora package."""
    from memora import MemoraStore

    assert MemoraStore is not None


def test_memora_store_in_all():
    """Test that MemoraStore is in __all__."""
    from memora import __all__

    assert "MemoraStore" in __all__


def test_memora_store_instantiation():
    """Test that MemoraStore can be instantiated after import."""
    from memora import MemoraStore

    store = MemoraStore()
    assert store is not None
