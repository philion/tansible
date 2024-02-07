from textual.message import Message
from textual.widgets import DirectoryTree


from pathlib import Path
from typing import Iterable


class InventoryTree(DirectoryTree):
    class Selected(Message):
        """Inventory selected message."""
        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths
                if not path.name.startswith('.')
                and (path.is_dir() or path.suffix == '' or 'hosts' in path.name)]

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Called when the user click a hosts file in the inventory directory tree."""
        # Convert the FileSelected message into an InventoryTree.Selected message
        self.post_message(self.Selected(event.path))