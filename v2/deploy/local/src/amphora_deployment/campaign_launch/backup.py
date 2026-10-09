"""Cold backup guard; no state creation for installations without a launch journal."""
from pathlib import Path

from .journal import LaunchJournal


def require_launches_drained(root):
    directory = Path(root) / 'campaign-launches'
    if not (directory / 'launches.sqlite3').exists():
        return 0
    return LaunchJournal(directory).verify_quiescent()
