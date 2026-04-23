"""
snapshot_widget.py - Base class for widgets that render from StatusSnapshot.

Provides snapshot caching and automatic re-render on terminal resize.
"""

from textual.widgets import Static

from data import StatusSnapshot


class SnapshotMixin:
    """Mixin providing snapshot caching and resize re-rendering.

    Usable by any widget class (Static, Widget, etc.).
    """

    _last_snapshot: StatusSnapshot | None = None

    def _init_snapshot_mixin(self) -> None:
        """Call from __init__ to initialize instance-level storage."""
        self._last_snapshot = None

    def update_from_snapshot(self, snap: StatusSnapshot) -> None:
        """Subclasses must override to render snapshot data."""
        raise NotImplementedError

    def on_resize(self, event) -> None:
        """Re-render on resize to adjust dynamic layouts."""
        if self._last_snapshot is not None:
            self.update_from_snapshot(self._last_snapshot)


class SnapshotWidget(SnapshotMixin, Static):
    """Base Static widget with snapshot caching and resize re-rendering."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._init_snapshot_mixin()
