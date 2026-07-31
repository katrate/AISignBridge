import sys
import types

# mediapipe.tasks.python.vision.drawing_utils imports matplotlib.pyplot
# at module level. We provide a minimal stub since the real matplotlib
# has a broken ft2font C extension on this Python version.
matplotlib = types.ModuleType('matplotlib')
matplotlib.pyplot = types.ModuleType('matplotlib.pyplot')
matplotlib.__path__ = []
matplotlib.__file__ = '<mock>'
matplotlib.__package__ = 'matplotlib'
matplotlib.pyplot.__file__ = '<mock>'
matplotlib.pyplot.__package__ = 'matplotlib.pyplot'

# Provide a minimal Figure class so matplotlib.pyplot can be used
class Figure:
    pass

matplotlib.pyplot.figure = lambda *a, **kw: Figure()
matplotlib.pyplot.subplots = lambda *a, **kw: (Figure(), None)
matplotlib.pyplot.ioff = lambda: None
matplotlib.pyplot.close = lambda *a, **kw: None

sys.modules['matplotlib'] = matplotlib
sys.modules['matplotlib.pyplot'] = matplotlib.pyplot
