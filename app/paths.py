import os
import sys

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(sys.executable)
            if sys.platform == 'darwin' and base.endswith('Contents/MacOS'):
                base = os.path.join(os.path.dirname(base), 'Resources')
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
