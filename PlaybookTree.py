from textual.message import Message
from textual.widgets import DirectoryTree

from pathlib import Path
from typing import Iterable


class PlaybookTree(DirectoryTree):
    class Selected(Message):
        """Playbook selected message."""
        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        # filter for YAML files and directories
        return [path for path in paths if 
                not path.name.startswith('.') # skip dot files
                # allow directories and YAML file extensions
                and (path.is_dir() or path.name.lower().endswith(('.yml', '.yaml')))]

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Called when the user click a YAML file in the directory tree."""
        # Convert the FileSelected message into a PlaybookTree.Selected message
        self.post_message(self.Selected(event.path))