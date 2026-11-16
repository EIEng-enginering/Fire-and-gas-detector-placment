# Windows acceptance still pending
Use a new synthetic development folder and Python3.12/PySide6 6.12.0. Review setup.ps1; optional reporting packages require `setup.ps1 -Reports`. Do not alter organisation execution policy to bypass restrictions.

Run `tools/windows_acceptance.ps1 -Python <path-to-development-python.exe>`. It records separate suite output and explicitly requires Qt's Windows platform for screenshots. No package installation, publication or engineering release is performed by this script.

Manual acceptance must then exercise: all four virtual registers; 10,000 detectors; selection/filter/sort and numeric order; copy, previewed paste, rejected cut; named-editor forms; generic and scene history conflicts; geometry append/replace/cancel; evidence/findings; zone/orientation annotations; per-case view and per-PC column layout; save/close/recover; concurrent sessions across runtime folders; crash recovery and backups; asynchronous reports/cancel and actual Office/PDF layout.

The POSIX symlink regression may require Windows developer-mode/symlink privileges or an explicitly reviewed Windows-specific equivalent; do not weaken or silently skip its acceptance meaning. Windows Job Object memory limits, real DPI/multi-monitor behaviour and local/cloud-synced file semantics remain unverified. Passing smoke screenshots alone is not acceptance or engineering qualification.
