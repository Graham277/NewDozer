#!/usr/bin/env /usr/bin/python3
#
# ========= Setup =========
# Standalone script to install files and to set up dependencies.
# This script makes the following changes:
#  1. Clones all project files into the selected directory. If appropriate,
#     creates symlinks to `bin` directories.
#  2. Creates a virtualenv in the installation directory.
#  3. `pip install`s dependencies in the virtualenv.
#  4. Creates a `systemd` service (if available) to run the bot.
#     Created as a user service if installed into the home directory, system
#     otherwise.
#  5. Configures rsyslog if using system-wide service. Configures logrotate if
#     using user service.
# Requires sudo privileges.
import os
import stat
from os.path import sep
import shutil
import subprocess
import sys
import textwrap


## Helper functions

def choose_option(message: str, *options: str, default: int | None = None) -> int:
    """
    Present a list for the user to choose various options from.
    The default option is chosen when the user enters '0' or nothing, and is
    marked with an asterisk.
    :param message: a header message to inform the user of the message's context
    :param options: the set of options the user has
    :param default: the index of the option that is chosen by default, or None if none
    :return: the index of the option that was chosen
    """

    wrap_col = 80

    # regularize to non-None int

    # first print out the options
    # all printed messages are wrapped in textwrap.wrap() and have sep='\n'
    # this is so extra-long messages are put onto multiple lines.
    print(*textwrap.wrap(message, wrap_col), sep='\n')
    print()
    # either:
    # Choose an option [1-N, or 0 for default]: | if default not None
    # Choose an option [1-N]:                   | if default None
    print(*textwrap.wrap(f"Choose an option [1-{len(options)}"
          f"{", or 0 for default" if default is not None else ""}]:", wrap_col),
          sep='\n')

    # offset = how long the last index is
    offset = len(str(len(options)))
    number = 1
    # print each option. each number is space-buffered from the left if it is
    # not max length.
    # default is marked with an asterisk
    for option in options:
        buffer = " " * (offset - len(str(number)))
        if default is not None and default + 1 == number:
            # either (default selected):
            # | * NNN. option placeholder
            # |   NNN. option placeholder
            # or (no default):
            # | NNN. option placeholder
            # | NNN. option placeholder
            print(*textwrap.wrap(f"{" *" if default is not None else ""} {buffer}"
                                f"{number}. {option}", wrap_col), sep='\n')
        else:
            print(*textwrap.wrap(f"{"  " if default is not None else ""} {buffer}"
                                f"{number}. {option}", wrap_col), sep='\n')
        number += 1

    print()

    # get choice
    # keep doing it until a valid input is reached

    # choice_start: lowest valid integer for choice
    choice_start = 0 if default is not None else 1
    while True:
        # wait for input
        # either:
        # Choice [0-N]:
        # or:
        # Choice [1-N]:
        val = input(f"Choice [{choice_start}-{len(options)}]: ")

        # validate input
        # first, if the string is empty, that means the default was chosen
        if not val:
            val = "0"

        # check: value is an integer
        try:
            val_index: int = int(val) - 1
        except ValueError:
            print("Invalid input (not a number), please try again.")
            continue

        # from now on, index starts at 0 and default == -1
        # check: value is not default if default is unset
        if default is None and val_index == -1:
            print("Invalid input (no default option), please try again.")
            continue

        # collapse default value
        # default is not None already implied here
        if val_index == -1 and default is not None:
            val_index = default

        # check: value in range
        if val_index < 0 or val_index >= len(options):
            print(f"Input out of range ({choice_start}-{len(options)}), please try again.")
            continue

        # all good
        return val_index

    assert False, "Unreachable state"

def confirm(message: str, default_state: bool | None) -> bool:
    """
    Presents the user with a confirmation message, which they can respond to in
    various ways.

    The values "y", "yes" and "true" yield `True`, while "n", "no" and "false"
    yield `False`, an empty string results in the default value, and anything
    else makes the user try again.
    :param message:
    :param default_state: the option to return if the user inputs nothing, or
                          None if this is not a valid option
    :return: a `bool` representing the user's choice
    """

    # essentially:
    # default is False  -> y/N
    # default is True   -> Y/n
    # default is None   -> y/n
    possible_inputs = (f"[{'y' if not default_state or default_state is None else 'Y'}/"
                       f"{'n' if default_state or default_state is None else 'N'}]")
    val = input(message + " " + possible_inputs + "? ")
    while True:
        # if nothing was entered, use default
        if not val or len(val.strip()) == 0:
            if default_state is not None:
                return default_state
            # if default is None, reject it and try again
            else:
                val = input(f"Invalid input. {possible_inputs}? ")
                continue
        else:
            # if it is yes, true
            if val.strip().lower() in ("y", "yes", "true"):
                return True
            # if no, false
            elif val.strip().lower() in ("n", "no", "false"):
                return False
            # if invalid, go again
            else:
                val = input(f"Invalid input. {possible_inputs}? ")
                continue

    assert False, "Unreachable state"

def wait():
    """
    Waits for the user to press enter.
    :return: nothing
    """
    input("Press enter to continue...")

def is_subdir(parent: str | os.PathLike, child: str | os.PathLike) -> bool:
    """
    Checks if the child is a subdirectory of or equal to the parent.
    :param parent: the parent directory
    :param child: the child, which might be a child of the parent
    :return: bool: whether the child is a subdirectory of the parent
    """
    parent_real = os.path.realpath(os.path.abspath(os.path.expanduser(parent)))
    child_real = os.path.realpath(os.path.abspath(os.path.expanduser(child)))
    return parent_real == os.path.commonpath([parent_real, child_real])

def main():
    """
    Main routine that handles all functions.
    :return: nothing
    """

    subdir_name = "dozerbot"
    wrap_width = 80

    print(" === Dozer Installer === ")
    print("Version 1.0.0")
    print()
    print("Step 1 - gathering information...")
    print()

    # get information

    # only supports Linux atm
    if not sys.platform.startswith("linux"):
        print("ERROR: This install script is only supported on Linux (and similar) systems.")
        print("Abort. ---")
        sys.exit(1)

    # check deps (virtualenv)
    if shutil.which("virtualenv") is None:
        print(*textwrap.wrap("ERROR: no installed copy of virtualenv was found, which is"
              " required for installation. Please check $PATH and install it if"
              " necessary.", wrap_width), sep='\n')
        print("Abort. ---")
        sys.exit(1)

    # get the install directory
    install_targets = ["/usr/local/share", "/opt", "~/.local/share"]
    bin_path_targets = ["/usr/local/bin", "/opt", "~/.local/bin"]
    etc_path_targets = ["/usr/local/etc", "/opt", "~/.local/etc"]
    annotated_install_targets = [
        "Into /usr/local/share, linked into /usr/local/bin and etc",
        "Into /opt, in its own subdirectory",
        "Into ~/.local/share, linked into ~/.local/bin and etc",]
    option = choose_option(
        "Which directory should the bot be installed into?\n",
        *annotated_install_targets)

    install_parent_target_abs = os.path.realpath(os.path.abspath(
        os.path.expanduser(install_targets[option])
    ))
    bin_path_target_abs = os.path.realpath(os.path.abspath(
        os.path.expanduser(bin_path_targets[option])
    ))
    etc_path_target_abs = os.path.realpath(os.path.abspath(
        os.path.expanduser(etc_path_targets[option])
    ))

    # check $PATH
    path = os.getenv("PATH")
    path_entries = path.split(os.pathsep)
    has_found_current = False

    # this awful mess just gets the real path of a file
    # (i.e. no symlinks, tildes or relative components)
    # this loop checks if the selected directory is in PATH
    for entry in path_entries:
        entry_test_dir = os.path.realpath(os.path.abspath(os.path.expanduser(entry)))
        if entry_test_dir == bin_path_target_abs:
            has_found_current = True
            break

    # warn user if their installation dir is not in PATH
    if not has_found_current:
        print()
        print(*textwrap.wrap("WARNING: Cannot find " + bin_path_target_abs +
              " in $PATH. This will not prevent installation, but may cause"
              " issues if running directly from the command line.",
                             wrap_width), sep='\n')
        print(*textwrap.wrap("It is recommended to add the directory to PATH if"
                             " you plan on using it directly from the command"
                             " line.", wrap_width), sep='\n')

    print()
    wait()

    # install!
    print()
    print("Step 2 - installing files...")
    print()

    install_dir = install_parent_target_abs + sep + subdir_name
    needs_root = not is_subdir("~", install_parent_target_abs)
    print("Starting copy...")

    if needs_root:
        print("The installer will now ask for superuser permissions.")

    # copy files
    try:
        if needs_root:
            # make sure directories exist
            subprocess.run(["sudo", "mkdir", "-p", install_dir])
            subprocess.run(["sudo", "cp", "-r", ".", install_dir])
            # and make sure anyone can execute
            subprocess.run(["sudo", "chmod", "+x", install_dir + sep + "main.py"])
            subprocess.run(["sudo", "chmod", "+x", install_dir + sep + "start.sh"])
        else:
            # but with 100% less sudo
            subprocess.run(["mkdir", "-p", install_dir])
            subprocess.run(["cp", ".", install_dir])
            os.chmod(install_dir + sep + "main.py",
                     os.stat(install_dir + sep + "main.py").st_mode | stat.S_IEXEC)
            os.chmod(install_dir + sep + "start.sh",
                     os.stat(install_dir + sep + "start.sh").st_mode | stat.S_IEXEC)
        print("Success!")
        print()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to copy files! (exit code {e.returncode},"
              f" message: {str(e)})")
        print("Abort. ---")
        exit(1)
    # done

    # make venv
    print()
    print("Step 3 - creating virtual environment...")
    print()

    venv_folder = install_dir + sep + ".venv"
    try:
        print("Creating...")
        print()
        subprocess.run(["sudo", "-E", "virtualenv", venv_folder])
        print("Success!")
        print()
        # cannot source it so it has to be explicitly called every time
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment! (exit code"
              f" {e.returncode}, message: {str(e)})")
        print("Abort. ---")
        exit(1)
    # done

    # get pip deps
    print()
    print("Step 4 - installing dependencies...")
    print()

    try:
        print("Installing dependencies from requirements.txt...")
        print()
        print(" -------- pip output begins -------- ")
        print()
        subprocess.run(["sudo", "-E", venv_folder + sep + "bin" + sep + "pip",
                        "install", "-r", install_dir + sep + "requirements.txt"])
        print()
        print(" --------  pip output ends  -------- ")
        print()
        print("Success!")
        print()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies! (exit code"
              f" {e.returncode}, message: {str(e)})")
        print("Abort. ---")
        exit(1)

    # TODO: symlink [.]local/bin, etc
    # TODO: make systemd files/log config

if __name__ == "__main__":
    main()