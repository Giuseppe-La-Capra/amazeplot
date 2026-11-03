"""Qt (PySide6) user interface of amazeplot.

The GUI only *presents* the core layer: it builds widgets from action
metadata and forwards user actions to the session. All data and plot
logic lives in :mod:`amazeplot.core` and :mod:`amazeplot.operations`.
"""

import os

# matplotlib picks its Qt binding when its Qt backend is first imported.
# Pin it to PySide6 so an installed PyQt can never be mixed in.
os.environ.setdefault("QT_API", "pyside6")
