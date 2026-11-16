"""UI entrypoint. Python 3.12 and PySide6 6.12.0 required on Windows."""
import sys
if sys.version_info[:2] != (3,12):
    raise SystemExit('This project requires Python 3.12 (not other Python versions).')
try:
    from importlib.metadata import version
    if version('PySide6') != '6.12.0':raise ImportError('Installed PySide6 version must be exactly 6.12.0')
    from fgmapping.ui.main import main
except ImportError as exc:
    raise SystemExit('PySide6 6.12.0 is required to launch the Windows UI: '+str(exc)) from exc
raise SystemExit(main())
