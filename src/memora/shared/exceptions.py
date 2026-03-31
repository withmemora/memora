"""Custom exceptions for Memora.

All exceptions inherit from MemoraError. Each exception includes
a descriptive docstring with user-friendly hints for resolution.
"""


class MemoraError(Exception):
    """Base exception for all Memora errors.

    All custom exceptions in Memora inherit from this base class.
    This allows catching all Memora-specific errors with a single except clause.
    """

    pass


class StoreNotInitializedError(MemoraError):
    """Raised when .memora/ directory not found or invalid.

    This typically occurs when trying to use Memora commands in a directory
    that hasn't been initialized yet.

    Hint: Run 'memora init' first.
    """

    pass


class ObjectNotFoundError(MemoraError):
    """Raised when a hash does not exist in the object store.

    This occurs when attempting to retrieve an object by its SHA-256 hash,
    but no file exists at the expected path in .memora/objects/.
    """

    pass


class HashMismatchError(MemoraError):
    """Raised when file content does not match its hash.

    This indicates store corruption - the content of an object file
    produces a different hash than the filename/path indicates.

    This indicates store corruption. Run 'memora doctor'.
    """

    pass


class StagingEmptyError(MemoraError):
    """Raised when commit is called with nothing staged.

    Cannot create a commit when the staging area is empty.
    Facts must be added to staging before committing.

    Hint: Use 'memora remember' first.
    """

    pass


class ConflictExistsError(MemoraError):
    """Raised in strict mode when unresolved conflicts block commit.

    In strict mode, commits are blocked if there are unresolved conflicts.
    Resolve or review conflicts before committing, or use lenient mode.
    """

    pass


class BranchNotFoundError(MemoraError):
    """Raised when a branch name does not exist in refs/heads/.

    This occurs when attempting to switch to or access a branch
    that hasn't been created yet.
    """

    pass


class StoreLockError(MemoraError):
    """Raised when write lock cannot be acquired within timeout.

    The write lock prevents concurrent modifications to the store.
    If this error occurs, another process may be writing to the store,
    or a previous operation may have crashed without releasing the lock.

    Another process may be writing to the store.
    """

    pass
