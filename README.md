# tansible
A textual-based TUI for the Ansible debugger.

Test: 
* https://github.com/philion/tansible/wiki
* [[wiki]]

This is an exploration of using automation and [infrastructure-as-code](https://en.wikipedia.org/wiki/Infrastructure_as_code) to help teach operational management and support.

Ansible is selected for "simplicity", widespread use, community support and it's FOSS licensing. This is not to say that ansible is a "simple tool". To the contrary, event the simplest tasks and network configuration quickly becomes obscure due to the inherent complexity and scale of the operations ansible is performing. This makes [IaC](https://en.wikipedia.org/wiki/Infrastructure_as_code) difficult for new users, with a daunting learning curve and dire consequenses should any mistakes be made.

At the same time, IaC is a powerful tool that both describes an entire system and provides a means create and maintain it. Framed as a functional description of a system and its operation, IaC becomes an opportunity to use the captured knowledge to demonstrate "how systems are built".

Theoritically. This project is an attempt to see if it works in action.

`tansible` uses [textual](https://github.com/Textualize/textual) for the terminal user interface [TUI](https://en.wikipedia.org/wiki/Text-based_user_interface) to wrap the [Ansible debugger](https://docs.ansible.com/ansible/2.9/user_guide/playbooks_debugger.html), while displaying code location and varible values.

## Design

Made up of several ansible-specific widgets to select an inventory, select a playbook, display specific locations in code (file, line number), display current task vars, and an active ansible console to step, edit and execute the next operation.

playbook debugger commands:
* print var
* set var
* update task
* redo
* continue
* quit

Based on a textual TCSS file, the user will be able to modify the display and layout of the TUI. The TUI is designed to be reactive and to downgrade gracefully for older terminals. `tansible` is intended to operate over ssh, take advantage of modern terminal capabilities and still work well when all you have an actual console connection.

## Alternatives

* by-hand operating instructions (type in, cut-and-paste, etc.)
* Ansible Semaphore webapp: https://github.com/ansible-semaphore/semaphore

## Progress

**Note**: This is a *Work In Progress*.

Simple inventory and playbook widgets are working. App logs are written to the log widget.

Next step is an ansible widget to hold the debugger, playbook and inventory in dry-run mode.
