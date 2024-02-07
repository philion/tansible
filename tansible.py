#!/usr/bin/env python3

import sys

import logging
from pathlib import Path
from typing import Iterable
from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, Vertical
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Static, RichLog
from textual.message import Message

from ansible import context
from ansible.cli import CLI
from ansible.module_utils.common.collections import ImmutableDict
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager

log = logging.getLogger(__name__)

# app-based log handling, see https://github.com/Textualize/textual/discussions/2072
class AppLogHandler(logging.Handler):
    """Class for logging to a textual widget"""

    def __init__(self, log_widget:RichLog):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.widget = log_widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.write(msg)


class PlaybookTree(DirectoryTree):
    class Selected(Message):
        """Playbook selected message."""
        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()
            
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths 
                if not path.name.startswith('.') 
                and (path.is_dir() or path.name.lower().endswith(('.yml', '.yaml')))]
    
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Called when the user click a YAML file in the directory tree."""
        # Convert the FileSelected message into a PlaybookTree.Selected message
        self.post_message(self.Selected(event.path))
        
# def PlaybookWidget, composed of PlaybookTree and playbook (in place of #code)
    

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

# def InventoryWidget, composed of InventoryTree and inventory list.
# add events for items selected in inventory list, to limit operation to those selected.
# inventory updates for InventoryTree.Selected and Inventory.Selected (multiselect?)

class AnsibleWidget(RichLog):
    #def __init__(self, path: Path) -> None:
    #        self.path = path
    #        super().__init__()
    
    def execute_playbook(self, inv_file: Path, playbook: Path) -> None:
        # redirect stdout to widget
        
        context.CLIARGS = ImmutableDict(
            tags={}, listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', 
            module_path=None, forks=100, remote_user='ansible', private_key_file=None, ssh_common_args=None, 
            ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method='sudo', 
            become_user='root', verbosity=True, check=False, start_at_task=None)

        loader = DataLoader()
        
        inventory = InventoryManager(loader=loader, sources=inv_file.absolute().as_posix())
        
        variable_manager = VariableManager(
            loader=loader, 
            inventory=inventory, 
            version_info=CLI.version_info(gitinfo=False)
        )

        pbex = PlaybookExecutor(
            playbooks=[playbook.absolute().as_posix()], 
            inventory=inventory, 
            variable_manager=variable_manager, 
            loader=loader, 
            passwords={} # passwords = dict(vault_pass='secret'), load from .env?
        )

        results = pbex.run() # list of plays


class Tansible(App):
    """Ansible browser app."""

    CSS_PATH = "tansible.tcss"
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        ("q", "quit", "Quit"),
        ("x", "execute", "Execute Playbook"),
    ]

    show_tree = var(True)


    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")


    def compose(self) -> ComposeResult:
        """Compose our UI."""
        path = "./" if len(sys.argv) < 2 else sys.argv[1]
        yield Header()
        yield Horizontal(
            Vertical(
                InventoryTree(path, id="inv-tree"),
                VerticalScroll(
                    Static(id="inventory", expand=True),
                    id="inv-view",
                ),
                classes="column",
                id="inv-pane",
            ),
            PlaybookTree(path, id="tree-view"),
            VerticalScroll(
                Static(id="code", expand=True),
                id="code-view",
            )
        )
        yield AnsibleWidget(id="ansible", highlight=True, markup=True)
        yield RichLog(id="logs", highlight=True, markup=True)
        yield Footer()
    
    
    def on_ready(self) -> None:
        """Called when the DOM is ready."""
        
        # capture stdout and stderr and send to the logs widget
        self.begin_capture_print(self.query_one("#logs"))
        
        # initialize log console
        log_console = self.query_one("#logs", RichLog)
        handler = AppLogHandler(log_console)
        logging.basicConfig(level=logging.DEBUG, format="{asctime} {levelname:<8s} {name:<16} {message}", style='{')
        logging.getLogger().addHandler(handler) # root
        log.debug("installed logger")
        
        self.query_one("#tree-view", DirectoryTree).show_root = False
                
        log.info("app is ready")


    def on_mount(self) -> None:
        self.query_one("#inv-tree", DirectoryTree).focus()
    
    
    def on_playbook_tree_selected(self, event: PlaybookTree.Selected) -> None:
        view = self.query_one("#code", Static)
        log.info(f"selected playbook: {event.path}")
        self.playbook = event.path
        
        try:
            syntax = Syntax.from_path(
                str(event.path),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception:
            view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.title = f"Playbook - {event.path}"
            self.sub_title = str(event.path)


    def on_inventory_tree_selected(self, event: InventoryTree.Selected) -> None:
        view = self.query_one("#inventory", Static)
        log.info(f"selected inventory: {event.path}")
        self.inventory = event.path
        
        try:
            syntax = Syntax.from_path(
                str(event.path),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception:
            view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            view.update(syntax)
            self.query_one("#inv-view").scroll_home(animate=False)
            self.title = f"Inventory - {event.path}"
            self.sub_title = str(event.path)


    def action_toggle_files(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree
        log.debug(f"display file tree: {self.show_tree}")


    def action_execute(self) -> None:
        """Called in response to execute key binding, to run a playbook"""
        if self.playbook.is_file() and self.inventory.is_file():
            ansible_widget = self.query_one("#ansible", AnsibleWidget)
            log.info(f"executing {self.playbook} with inventory {self.inventory}")
            ansible_widget.execute_playbook(self.inventory, self.playbook)


if __name__ == "__main__":
    Tansible().run()
