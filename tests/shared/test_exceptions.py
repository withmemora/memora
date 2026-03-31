"""Tests for shared/exceptions.py custom exceptions."""

import pytest

from memora.shared.exceptions import (
    BranchNotFoundError,
    ConflictExistsError,
    HashMismatchError,
    MemoraError,
    ObjectNotFoundError,
    StagingEmptyError,
    StoreLockError,
    StoreNotInitializedError,
)


class TestMemoraError:
    """Test base MemoraError exception."""

    def test_memora_error_is_exception(self):
        """Test that MemoraError inherits from Exception."""
        assert issubclass(MemoraError, Exception)

    def test_memora_error_can_be_raised(self):
        """Test that MemoraError can be raised and caught."""
        with pytest.raises(MemoraError):
            raise MemoraError("Test error")

    def test_memora_error_with_message(self):
        """Test that MemoraError can carry a message."""
        error = MemoraError("Custom error message")
        assert str(error) == "Custom error message"


class TestStoreNotInitializedError:
    """Test StoreNotInitializedError exception."""

    def test_inherits_from_memora_error(self):
        """Test that StoreNotInitializedError inherits from MemoraError."""
        assert issubclass(StoreNotInitializedError, MemoraError)

    def test_can_be_raised(self):
        """Test that StoreNotInitializedError can be raised."""
        with pytest.raises(StoreNotInitializedError):
            raise StoreNotInitializedError("Store not found")

    def test_can_be_caught_as_memora_error(self):
        """Test that StoreNotInitializedError can be caught as MemoraError."""
        with pytest.raises(MemoraError):
            raise StoreNotInitializedError()


class TestObjectNotFoundError:
    """Test ObjectNotFoundError exception."""

    def test_inherits_from_memora_error(self):
        """Test that ObjectNotFoundError inherits from MemoraError."""
        assert issubclass(ObjectNotFoundError, MemoraError)

    def test_can_be_raised(self):
        """Test that ObjectNotFoundError can be raised."""
        with pytest.raises(ObjectNotFoundError):
            raise ObjectNotFoundError("Object hash123 not found")

    def test_can_be_caught_as_memora_error(self):
        """Test that ObjectNotFoundError can be caught as MemoraError."""
        with pytest.raises(MemoraError):
            raise ObjectNotFoundError()


class TestHashMismatchError:
    """Test HashMismatchError exception."""

    def test_inherits_from_memora_error(self):
        """Test that HashMismatchError inherits from MemoraError."""
        assert issubclass(HashMismatchError, MemoraError)

    def test_can_be_raised(self):
        """Test that HashMismatchError can be raised."""
        with pytest.raises(HashMismatchError):
            raise HashMismatchError("Hash mismatch detected")

    def test_can_be_caught_as_memora_error(self):
        """Test that HashMismatchError can be caught as MemoraError."""
        with pytest.raises(MemoraError):
            raise HashMismatchError()


class TestStagingEmptyError:
    """Test StagingEmptyError exception."""

    def test_inherits_from_memora_error(self):
        """Test that StagingEmptyError inherits from MemoraError."""
        assert issubclass(StagingEmptyError, MemoraError)

    def test_can_be_raised(self):
        """Test that StagingEmptyError can be raised."""
        with pytest.raises(StagingEmptyError):
            raise StagingEmptyError("Nothing to commit")

    def test_can_be_caught_as_memora_error(self):
        """Test that StagingEmptyError can be caught as MemoraError."""
        with pytest.raises(MemoraError):
            raise StagingEmptyError()


class TestConflictExistsError:
    """Test ConflictExistsError exception."""

    def test_inherits_from_memora_error(self):
        """Test that ConflictExistsError inherits from MemoraError."""
        assert issubclass(ConflictExistsError, MemoraError)

    def test_can_be_raised(self):
        """Test that ConflictExistsError can be raised."""
        with pytest.raises(ConflictExistsError):
            raise ConflictExistsError("Unresolved conflicts exist")

    def test_can_be_caught_as_memora_error(self):
        """Test that ConflictExistsError can be caught as MemoraError."""
        with pytest.raises(MemoraError):
            raise ConflictExistsError()


class TestBranchNotFoundError:
    """Test BranchNotFoundError exception."""

    def test_inherits_from_memora_error(self):
        """Test that BranchNotFoundError inherits from MemoraError."""
        assert issubclass(BranchNotFoundError, MemoraError)

    def test_can_be_raised(self):
        """Test that BranchNotFoundError can be raised."""
        with pytest.raises(BranchNotFoundError):
            raise BranchNotFoundError("Branch 'feature' not found")

    def test_can_be_caught_as_memora_error(self):
        """Test that BranchNotFoundError can be caught as MemoraError."""
        with pytest.raises(MemoraError):
            raise BranchNotFoundError()


class TestStoreLockError:
    """Test StoreLockError exception."""

    def test_inherits_from_memora_error(self):
        """Test that StoreLockError inherits from MemoraError."""
        assert issubclass(StoreLockError, MemoraError)

    def test_can_be_raised(self):
        """Test that StoreLockError can be raised."""
        with pytest.raises(StoreLockError):
            raise StoreLockError("Could not acquire lock")

    def test_can_be_caught_as_memora_error(self):
        """Test that StoreLockError can be caught as MemoraError."""
        with pytest.raises(MemoraError):
            raise StoreLockError()


class TestExceptionHierarchy:
    """Test the exception hierarchy."""

    def test_all_exceptions_inherit_from_memora_error(self):
        """Test that all custom exceptions inherit from MemoraError."""
        exceptions = [
            StoreNotInitializedError,
            ObjectNotFoundError,
            HashMismatchError,
            StagingEmptyError,
            ConflictExistsError,
            BranchNotFoundError,
            StoreLockError,
        ]

        for exc in exceptions:
            assert issubclass(exc, MemoraError)

    def test_catch_all_memora_errors(self):
        """Test that a single except clause can catch all Memora errors."""
        exceptions_to_test = [
            StoreNotInitializedError("test"),
            ObjectNotFoundError("test"),
            HashMismatchError("test"),
            StagingEmptyError("test"),
            ConflictExistsError("test"),
            BranchNotFoundError("test"),
            StoreLockError("test"),
        ]

        for exc in exceptions_to_test:
            with pytest.raises(MemoraError):
                raise exc
