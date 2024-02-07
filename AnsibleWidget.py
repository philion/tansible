import logging

from ansible import context
from ansible.cli import CLI
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from textual.widgets import RichLog

from pathlib import Path
from subprocess import check_output


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="{asctime} {levelname:<8s} {name:<16} {message}", style='{')

class AnsibleWidget(RichLog):
    #def __init__(self, path: Path) -> None:
    #        self.path = path
    #        super().__init__()

    def execute_playbook_cmd(self, inv_file: Path, playbook: Path) -> None:
        # ansible-playbook -i example-playbook/hosts example-playbook/site.yml --list-hosts
        cmd = ["ansible-playbook", "-i", inv_file, playbook, "--list-hosts"]

        #p = Popen(cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE, text=True)
        #p.wait()
        #stdout_data = p.communicate(input='data_to_write')[0]

        out = check_output(cmd).decode("utf-8")
        self.write(out)
        #log.debug(f"wrote {out.__class__}")


    def execute_playbook(self, inventory: Path, playbook: Path) -> None:
        inventory_filename = inventory.absolute().as_posix()
        playbook_filename = playbook.absolute().as_posix()

        log.info(f"executing {playbook_filename} with inventory {inventory_filename}")

        context.CLIARGS = ImmutableDict(
            tags={}, listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh',
            module_path=None, forks=100, remote_user='ansible', private_key_file=None, ssh_common_args=None,
            ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method='sudo',
            become_user='root', verbosity=True, check=False, start_at_task=None)

        loader = DataLoader()

        inventory = InventoryManager(loader=loader, sources=inventory_filename)

        variable_manager = VariableManager(
            loader=loader,
            inventory=inventory,
            version_info=CLI.version_info(gitinfo=False)
        )

        pbex = PlaybookExecutor(
            playbooks=[playbook_filename],
            inventory=inventory,
            variable_manager=variable_manager,
            loader=loader,
            passwords={} # passwords = dict(vault_pass='secret'), load from .env?
        )

        results = pbex.run() # list of plays
        #self.write(results)
        log.info(results)
    
    
if __name__ == "__main__":
    inventory = Path("./example-playbook/hosts")
    playbook = Path("./example-playbook/site.yml")
    AnsibleWidget().execute_playbook(inventory, playbook)