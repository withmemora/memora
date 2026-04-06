"""Cross-platform compatibility utilities for Memora v3.1.

Handles Windows/Unix path separators, file locking, and atomic operations.
"""

import os
import sys
from pathlib import Path, PurePath
from typing import Union, Optional
import tempfile
import shutil
from contextlib import contextmanager

# Platform-specific imports
if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


class PlatformUtils:
    """Cross-platform utilities for file operations."""

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows."""
        return sys.platform == "win32" or os.name == "nt"

    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        """Normalize path separators for current platform."""
        if isinstance(path, str):
            # Convert forward slashes to backslashes on Windows
            if PlatformUtils.is_windows():
                path = path.replace("/", "\\")
            # Convert to Path object
            return Path(path)
        return path

    @staticmethod
    def safe_file_write(file_path: Path, content: str, encoding: str = "utf-8") -> None:
        """Atomic file write that works on both Windows and Unix."""
        file_path = PlatformUtils.normalize_path(file_path)

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Use temporary file for atomic write
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding=encoding, dir=file_path.parent, delete=False, suffix=".tmp"
            ) as tf:
                tf.write(content)
                temp_file = Path(tf.name)

            # Atomic move (works on both platforms)
            if PlatformUtils.is_windows():
                # Windows requires removing target first
                if file_path.exists():
                    file_path.unlink()

            temp_file.replace(file_path)

        except Exception:
            # Cleanup temp file if something went wrong
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise

    @staticmethod
    def safe_file_read(file_path: Path, encoding: str = "utf-8") -> str:
        """Safe file read with proper path handling."""
        file_path = PlatformUtils.normalize_path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        return file_path.read_text(encoding=encoding)

    @staticmethod
    @contextmanager
    def file_lock(file_path: Path, shared: bool = False):
        """Cross-platform file locking context manager."""
        file_path = PlatformUtils.normalize_path(file_path)
        lock_file = None

        try:
            # Create lock file
            lock_file = open(file_path, "a+")

            if PlatformUtils.is_windows():
                # Windows file locking using msvcrt
                try:
                    if shared:
                        # Shared lock (multiple readers)
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
                    else:
                        # Exclusive lock (single writer)
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                except IOError as e:
                    raise OSError(f"Could not acquire lock on {file_path}: {e}")
            else:
                # Unix file locking using fcntl
                try:
                    lock_type = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
                    fcntl.flock(lock_file.fileno(), lock_type | fcntl.LOCK_NB)
                except IOError as e:
                    raise OSError(f"Could not acquire lock on {file_path}: {e}")

            yield lock_file

        finally:
            if lock_file:
                try:
                    if PlatformUtils.is_windows():
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                except (IOError, OSError):
                    pass  # Ignore unlock errors

                try:
                    lock_file.close()
                except (IOError, OSError):
                    pass  # Ignore close errors

    @staticmethod
    def create_directories_safe(path: Path) -> None:
        """Create directories with proper permissions."""
        path = PlatformUtils.normalize_path(path)

        try:
            path.mkdir(parents=True, exist_ok=True)

            # Set secure permissions on Unix-like systems
            if not PlatformUtils.is_windows():
                os.chmod(path, 0o700)

        except OSError as e:
            raise OSError(f"Could not create directory {path}: {e}")

    @staticmethod
    def get_temp_dir() -> Path:
        """Get platform-appropriate temporary directory."""
        temp_dir = Path(tempfile.gettempdir()) / "memora"
        PlatformUtils.create_directories_safe(temp_dir)
        return temp_dir

    @staticmethod
    def is_case_sensitive_fs() -> bool:
        """Check if filesystem is case sensitive."""
        if PlatformUtils.is_windows():
            return False  # Windows is case-insensitive by default

        # Test on Unix-like systems
        try:
            temp_dir = PlatformUtils.get_temp_dir()
            test_file1 = temp_dir / "CasE_TeSt"
            test_file2 = temp_dir / "case_test"

            test_file1.touch()
            exists = test_file2.exists()

            # Cleanup
            if test_file1.exists():
                test_file1.unlink()
            if test_file2.exists():
                test_file2.unlink()

            return not exists  # If file2 doesn't exist, FS is case-sensitive

        except Exception:
            return True  # Assume case-sensitive if test fails

    @staticmethod
    def resolve_executable_path(executable: str) -> Optional[Path]:
        """Find executable in PATH, handling Windows .exe extension."""
        # On Windows, try with .exe extension
        if PlatformUtils.is_windows() and not executable.endswith(".exe"):
            exe_name = f"{executable}.exe"
        else:
            exe_name = executable

        # Search in PATH
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            if not path_dir:
                continue

            exe_path = Path(path_dir) / exe_name
            if exe_path.is_file() and os.access(exe_path, os.X_OK):
                return exe_path

        return None

    @staticmethod
    def get_config_dir() -> Path:
        """Get platform-appropriate config directory."""
        if PlatformUtils.is_windows():
            # Windows: Use APPDATA
            appdata = os.environ.get("APPDATA")
            if appdata:
                return Path(appdata) / "Memora"

        # Unix-like: Use XDG_CONFIG_HOME or ~/.config
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            return Path(config_home) / "memora"

        return Path.home() / ".config" / "memora"


# Convenience functions
def safe_write_file(path: Union[str, Path], content: str) -> None:
    """Write file safely with cross-platform path handling."""
    PlatformUtils.safe_file_write(Path(path), content)


def safe_read_file(path: Union[str, Path]) -> str:
    """Read file safely with cross-platform path handling."""
    return PlatformUtils.safe_file_read(Path(path))


def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize path for current platform."""
    return PlatformUtils.normalize_path(path)


@contextmanager
def file_lock(path: Union[str, Path], shared: bool = False):
    """Lock file for exclusive or shared access."""
    with PlatformUtils.file_lock(Path(path), shared) as lock:
        yield lock
