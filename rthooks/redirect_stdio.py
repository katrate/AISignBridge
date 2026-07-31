import sys
import os
import logging

# In windowed (--noconsole) mode, sys.stdout/sys.stderr are None.
# Any logging handler created while they are None will capture None and
# crash on emit(). Redirect them to a log file next to the executable
# as early as possible (this runtime hook runs before package rthooks
# such as pyi_rth_tensorflow.py).

_log_file = None
try:
    log_dir = os.path.dirname(sys.executable)
    log_path = os.path.join(log_dir, "ai_sign_bridge.log")
    _log_file = open(log_path, "a", encoding="utf-8", buffering=1)
except Exception:
    _log_file = None

if _log_file is not None:
    sys.stdout = _log_file
    sys.stderr = _log_file
else:
    import io
    _null = io.StringIO()
    sys.stdout = _null
    sys.stderr = _null

# Make sure the root logger always has a working handler so TF/logging
# messages land in the log file instead of raising or going nowhere.
try:
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(_log_file or sys.stderr)
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
        root.addHandler(handler)
    root.setLevel(logging.INFO)
except Exception:
    pass
