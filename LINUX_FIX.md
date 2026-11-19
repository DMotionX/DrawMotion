# Linux Startup Fix

## Problem

On Linux, DrawMotion crashed immediately at startup with:

```
AttributeError: module 'ctypes' has no attribute 'windll'
```

`main.py` used the Windows-only `ctypes.windll` API unconditionally for its
single-instance "mutex" guard:

```python
mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
```

Because `ctypes.windll` only exists on Windows, the application terminated
before the Qt UI could be created. The same code also called
`ctypes.windll.user32.MessageBoxW` and
`ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID`.

## Fix

All Windows-only calls are now guarded behind `sys.platform == "win32"`.
The single-instance guard uses a POSIX advisory lock (`fcntl.flock`) on a lock
file in the application data directory on Linux/macOS.

Files changed:

- `main.py`
  - `_install_native_crash_handler()`: `MessageBoxW` only on Windows.
  - Single-instance enforcer: Win32 mutex on Windows, `fcntl.flock` elsewhere.
  - Taskbar / AppUserModelID: only on Windows.

## Verified

Tested on Kali Linux with Python 3.12.16 and the pinned
`requirements.txt` (PySide6 6.11.1, OpenCV 5.0.0.93, NumPy 2.5.1):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The application initializes Qt and FFmpeg and stays running.

## Run from source (Linux)

```bash
git clone https://github.com/zaddi-zk/DrawMotion.git
cd DrawMotion
uv venv --python 3.12 .venv      # or: python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Building installers

The existing GitHub Actions workflow
(`.github/workflows/build-linux.yml`) builds a standalone Nuitka binary, a
`.deb`, a tarball, and an AppImage. Push a `v*.*.*` tag or run the workflow
manually from the Actions tab.

## License

DrawMotion is licensed under the GNU GPL v3.0. This patch is distributed under
the same license.
