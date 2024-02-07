#!/usr/bin/env python3

import sys

import logging
from subprocess import Popen, PIPE, STDOUT

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, Vertical
from textual.reactive import var
from textual.widgets import DirectoryTree, Footer, Header, Static, RichLog


from AnsibleWidget import AnsibleWidget
from AppLogHandler import AppLogHandler
from InventoryTree import InventoryTree
from PlaybookTree import PlaybookTree

log = logging.getLogger(__name__)

# def PlaybookWidget, composed of PlaybookTree and playbook (in place of #code)
    
# def InventoryWidget, composed of InventoryTree and inventory list.
# add events for items selected in inventory list, to limit operation to those selected.
# inventory updates for InventoryTree.Selected and Inventory.Selected (multiselect?)

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
        # TODO: update to hide/show the browser windows.


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
        
        # TODO: move to AppLogHandler init, add -debug flag.
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
            try:
                ansible_widget = self.query_one("#ansible", AnsibleWidget)
                ansible_widget.execute_playbook_cmd(self.inventory, self.playbook)
            except Exception as ex:
                log.error(f"error executing playbook: {ex}", stack_info=True)
                

if __name__ == "__main__":
    Tansible().run()
