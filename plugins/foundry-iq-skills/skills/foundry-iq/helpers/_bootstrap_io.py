"""Private storage and shell-free native CLI execution for the bootstrap owner."""
from __future__ import annotations

import ctypes
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

try:
    from ._common import HelperFailure, canonical_bytes
except ImportError:
    from _common import HelperFailure, canonical_bytes

MAX_BYTES = 1024 * 1024


def failure(code, message):
    return HelperFailure(code, message, blocked_at="verification")


def read_json(path):
    try:
        with Path(path).open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise failure("bootstrap-input-invalid", "JSON exceeds the one MiB input limit.")
        value = json.loads(raw.decode("utf-8"))
        pending = [(value, 0)]
        count = 0
        while pending:
            item, depth = pending.pop()
            count += 1
            if depth > 20 or count > 10000:
                raise ValueError("JSON structure exceeds limits")
            if isinstance(item, dict):
                pending.extend((v, depth + 1) for v in item.values())
            elif isinstance(item, list):
                pending.extend((v, depth + 1) for v in item)
        json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
        return value
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise failure("bootstrap-input-invalid", "Select bounded, valid UTF-8 JSON.") from exc


def _windows_private(path):
    # Inspect effective trustees, not chmod: Windows chmod does not establish privacy.
    from ctypes import wintypes as w
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    pointer = ctypes.c_void_p
    adv.GetNamedSecurityInfoW.argtypes = [w.LPWSTR, w.DWORD, w.DWORD] + [ctypes.POINTER(pointer)] * 5
    adv.GetNamedSecurityInfoW.restype = w.DWORD
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [
        pointer, w.DWORD, w.DWORD, ctypes.POINTER(w.LPWSTR), ctypes.POINTER(w.DWORD),
    ]
    adv.ConvertSidToStringSidW.argtypes = [pointer, ctypes.POINTER(w.LPWSTR)]
    adv.OpenProcessToken.argtypes = [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)]
    adv.GetTokenInformation.argtypes = [w.HANDLE, ctypes.c_int, pointer, w.DWORD, ctypes.POINTER(w.DWORD)]
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.LocalFree.argtypes = [pointer]
    descriptor, owner, group, dacl, sacl = (pointer() for _ in range(5))
    text, sid_text, token, size = w.LPWSTR(), w.LPWSTR(), w.HANDLE(), w.DWORD()
    try:
        if adv.GetNamedSecurityInfoW(str(path), 1, 5, ctypes.byref(owner), ctypes.byref(group),
                                    ctypes.byref(dacl), ctypes.byref(sacl), ctypes.byref(descriptor)):
            raise OSError("Cannot inspect private ACL")
        if not adv.ConvertSecurityDescriptorToStringSecurityDescriptorW(
            descriptor, 1, 5, ctypes.byref(text), None,
        ):
            raise OSError("Cannot inspect security descriptor")
        if not adv.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
            raise OSError("Cannot inspect current owner")
        adv.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        buffer = ctypes.create_string_buffer(size.value)
        if not adv.GetTokenInformation(token, 1, buffer, size, ctypes.byref(size)):
            raise OSError("Cannot inspect current owner")
        sid = ctypes.cast(buffer, ctypes.POINTER(pointer))[0]
        if not adv.ConvertSidToStringSidW(sid, ctypes.byref(sid_text)):
            raise OSError("Cannot inspect current owner")
        sddl = text.value
        current = sid_text.value
        owner_text, separator, acl = sddl.partition("D:")
        if not separator or owner_text != "O:" + current or not dacl:
            raise OSError("Owner or DACL is not private")
        entries = re.findall(r"\(([^()]*)\)", acl)
        if not entries or re.sub(r"\([^()]*\)", "", acl) not in ("", "P", "AI", "PAI"):
            raise OSError("Unsupported ACL")
        for entry in entries:
            parts = entry.split(";")
            if len(parts) != 6 or parts[0] != "A" or parts[5] not in (current, "OW", "SY", "BA"):
                raise OSError("ACL grants access to another principal")
    finally:
        if token:
            kernel.CloseHandle(token)
        for allocated in (descriptor, text, sid_text):
            if allocated:
                kernel.LocalFree(ctypes.cast(allocated, pointer))


def _validated_directory(value):
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise failure("bootstrap-receipt-private", "Select an absolute, existing private receipt directory.")
    path = Path(value)
    try:
        for part in (path, *path.parents):
            info = part.lstat()
            if part == path:
                selected = info
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise OSError("Linked paths are unsupported")
        skill = Path(__file__).resolve().parents[1]
        plugin = skill.parent.parent
        protected = [skill]
        if any((plugin / marker / "plugin.json").is_file() for marker in (".plugin", ".claude-plugin", ".cursor-plugin")):
            protected.append(plugin)
        if not stat.S_ISDIR(selected.st_mode) or any(root in (path.resolve(), *path.resolve().parents) for root in protected):
            raise OSError("Receipts must be outside the installed plugin")
        if os.name == "nt":
            _windows_private(path)
        else:
            if selected.st_uid != os.getuid() or stat.S_IMODE(selected.st_mode) & 0o077:
                raise OSError("Directory must be private to its owner")
    except (OSError, ValueError) as exc:
        raise failure("bootstrap-receipt-private", "Receipt location must be user-owned and private; no ACLs were changed.") from exc
    return path, selected


def private_directory(value):
    return _validated_directory(value)[0]


def private_file(directory, name, value):
    if (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,199}", name)
            or name.endswith(".") or re.fullmatch(r"(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])", name.split(".")[0])):
        raise failure("bootstrap-receipt-failed", "Receipt name must be a safe, ordinary leaf name.")
    data = canonical_bytes(value) + b"\n"
    if len(data) > MAX_BYTES:
        raise failure("bootstrap-receipt-failed", "Sanitized receipt exceeds its bound.")
    directory_fd = file_fd = None
    primary = None
    try:
        directory, selected = _validated_directory(str(directory))
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        if os.name == "nt":
            file_fd = os.open(directory / name, flags, 0o600)
        else:
            if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
                raise failure("bootstrap-receipt-private", "POSIX handle-relative private creation is unavailable.")
            directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            opened = os.fstat(directory_fd)
            if ((opened.st_dev, opened.st_ino) != (selected.st_dev, selected.st_ino)
                    or not stat.S_ISDIR(opened.st_mode) or opened.st_uid != os.getuid()
                    or stat.S_IMODE(opened.st_mode) & 0o077):
                raise failure("bootstrap-receipt-private", "Opened receipt directory changed identity, ownership or permissions.")
            file_fd = os.open(name, flags, 0o600, dir_fd=directory_fd)
        handle = os.fdopen(file_fd, "wb")
        file_fd = None
        with handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except HelperFailure as exc:
        primary = exc
        raise
    except (OSError, NotImplementedError) as exc:
        primary = failure("bootstrap-receipt-failed", "Private receipt could not be persisted; retain the returned ownership handoff.")
        raise primary from exc
    finally:
        cleanup_failed = False
        for descriptor in (file_fd, directory_fd):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    cleanup_failed = True
        if cleanup_failed:
            if primary is not None:
                primary.warnings.append("Receipt descriptor cleanup could not be confirmed.")
            else:
                raise failure("bootstrap-receipt-failed", "Receipt descriptor cleanup could not be confirmed.")
    return directory / name


def cli_prefix():
    executable = shutil.which("az")
    if executable is None:
        raise failure("bootstrap-tool-unavailable", "A signed-in Azure CLI installation is required.")
    if os.name == "nt":
        if Path(executable).suffix.lower() not in (".cmd", ".bat"):
            raise failure("bootstrap-tool-unavailable", "Windows requires the supported bundled CLI Python layout.")
        # Use the installed CLI's own interpreter, never cmd.exe or caller commands.
        # Azure/azure-cli: build_scripts/windows/scripts/az_msi.cmd (and az_zip.cmd).
        python = Path(executable).parent.parent / "python.exe"
        if not python.is_file():
            raise failure("bootstrap-tool-unavailable", "This Windows CLI layout has no supported bundled Python launcher.")
        return [str(python), "-IBm", "azure.cli"]
    return [executable]


def run_cli(arguments, timeout):
    """Capture native CLI output; size validation is post-capture, not a memory bound."""
    env = dict(os.environ, AZURE_EXTENSION_USE_DYNAMIC_INSTALL="no",
               AZURE_CORE_COLLECT_TELEMETRY="no", AZURE_CORE_ONLY_SHOW_ERRORS="true",
               AZURE_CORE_NO_COLOR="true", AZURE_LOGGING_ENABLE_LOG_FILE="false",
               AZURE_AUTO_UPGRADE_ENABLE="false")
    try:
        command = cli_prefix() + arguments + ["--output", "json", "--only-show-errors"]
        result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                                shell=False, env=env, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise failure("bootstrap-cli-timeout", "Native CLI timed out; remote completion and process-tree cleanup are not established.") from exc
    except OSError as exc:
        cause = exc
        for _ in range(8):
            if not isinstance(cause, OSError):
                break
            cause = cause.__context__
        if isinstance(cause, subprocess.TimeoutExpired):
            error = failure("bootstrap-cli-timeout", "Native CLI timed out; remote completion is not established.")
            error.warnings.append("Standard subprocess cleanup also failed; process state is unknown.")
        else:
            error = failure("bootstrap-cli-unavailable", "Native CLI execution failed; process and remote state may be unknown.")
        raise error from exc
    if len(result.stdout) > MAX_BYTES or len(result.stderr) > MAX_BYTES:
        raise failure("bootstrap-cli-output-limit", "Captured CLI output exceeds one MiB per stream; this is not a capture-memory bound.")
    return result.returncode, result.stdout, result.stderr
