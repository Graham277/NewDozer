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
import pathlib
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

    # symlink bin and etc directories

    if install_parent_target_abs != bin_path_target_abs:
        print("Linking installation...")

        # make links
        # each link points from the base directory to the appropriate folder
        # (just as an alias)
        #
        # secrets.json is specifically excluded because it shouldn't exist most
        # of the time
        # .env can also point somewhere else if required
        if needs_root:
            # make sure symlinking directories exist
            subprocess.run(["sudo", "mkdir", "-p", bin_path_target_abs])
            subprocess.run(["sudo", "mkdir", "-p", etc_path_target_abs])
            # bin
            subprocess.run(["sudo", "-E", "ln", "-s",
                            install_dir + sep + "main.py",
                            bin_path_target_abs + sep + "dozermain"])
            subprocess.run(["sudo", "-E", "ln", "-s",
                            install_dir + sep + "start.sh",
                            bin_path_target_abs + sep + "dozerstart"])
            # etc
            subprocess.run(["sudo", "-E", "ln", "-s",
                            install_dir + sep + ".env",
                            etc_path_target_abs + sep + "dozer.env"])
        else:
            # same
            pathlib.Path(bin_path_target_abs).mkdir(parents=True)
            pathlib.Path(etc_path_target_abs).mkdir(parents=True)
            # bin
            os.symlink(install_dir + sep + "main.py",
                       bin_path_target_abs + sep + "dozermain")
            os.symlink(install_dir + sep + "start.sh",
                       bin_path_target_abs + sep + "dozerstart")
            # etc
            os.symlink(install_dir + sep + ".env",
                       etc_path_target_abs + sep + "dozer.env")
        print()
        print(*textwrap.wrap(
            f"Success! Executables and configuration may be also found at "
            f"{bin_path_target_abs + sep + "dozermain"} (for main.py), "
            f"{bin_path_target_abs + sep + "dozerstart"} (for start.sh), and "
            f"{(etc_path_target_abs + sep + "dozer.env")} (for .env).",
            wrap_width), sep='\n')

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
        print()
        print("Success!")
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

    print()
    print("Step 5 - creating system service...")
    print()

    log_options_annotated = ["Sink (/dev/null)", "To ~/.cache/dozer.log",
                             "To /var/log/dozer.log", "To syslog"]
    if not needs_root:
        log_options_annotated.remove("To /var/log/dozer.log")
    log_options = ["null", "cache", "varlog", "syslog"]
    if not needs_root:
        log_options.remove("varlog")
    log_option = log_options[choose_option("Where should log messages be sent?",
                                           *log_options_annotated, default=3)]

    # create a systemd file
    if needs_root:
        print("Creating as a system-wide systemd unit")
        print("...")
        # create a new unit file
        start_sh_path = install_dir + sep + "start.sh"
        service_tmp_path = "/tmp/dozer.service"
        service_file_path = "/lib/systemd/system/dozer.service"

        log_data = ""
        match log_option:
            case "null":
                log_data = """
                StandardOutput=/dev/null
                StandardError=/dev/null
                """
                print("WARNING: The `null` log output was selected. This can"
                      "make troubleshooting much more difficult.")
                print()
            case "cache":
                log_data = f"""
                StandardOutput={os.path.expanduser("~/.cache/dozer.log")}
                StandardError={os.path.expanduser("~/.cache/dozer.log")}
                """
                print("Note: It is recommended to set up a log rotation service"
                      " (like logrotate) to avoid having the log grow"
                      " uncontrollably.")
                print()
            case "varlog":
                log_data = f"""
                StandardOutput=/var/log/dozer.log
                StandardError=/var/log/dozer.log
                """
                print("Note: It is recommended to set up a log rotation service"
                      " (like logrotate) to avoid having the log grow"
                      " uncontrollably.")
                print()
            case "syslog":
                pass # default, no action needed

        # taken from nodejs version
        service_file_contents = f"""
        [Unit]
        Description=Dozer discord bot
        After=network.target
        
        [Service]
        WorkingDirectory={install_dir}
        ExecStart={start_sh_path}
        Restart=always
        RestartSec=3
        {log_data}
        
        [Install]
        WantedBy=multi-user.target
        """

        # cat into a temp file then move with sudo
        with open(service_tmp_path, "w") as f:
            f.write(service_file_contents)
        subprocess.run(["sudo", "mv", service_tmp_path, service_file_path])
        print("Enabling...")
        subprocess.run(["sudo", "systemctl", "enable", "dozer.service"])

        print("Success! Try systemctl start dozer.service")
    else:
        print("Creating as a user systemd unit")
        print("...")
        start_sh_path = install_dir + sep + "start.sh"
        service_tmp_path = "/tmp/dozer.service"
        service_file_path = os.path.expanduser("~/.config/systemd/user/dozer.service")

        log_data = ""
        match log_option:
            case "null":
                log_data = """
                StandardOutput=/dev/null
                StandardError=/dev/null
                """
                print("WARNING: The `null` log output was selected. This can"
                      "make troubleshooting much more difficult.")
                print()
            case "cache":
                log_data = f"""
                StandardOutput={os.path.expanduser("~/.cache/dozer.log")}
                StandardError={os.path.expanduser("~/.cache/dozer.log")}
                """
                print("Note: It is recommended to set up a log rotation service"
                      " (like logrotate) to avoid having the log grow"
                      " uncontrollably.")
                print()
            case "syslog":
                pass # default, no action needed

        service_file_contents = f"""
        [Unit]
        Description=Dozer discord bot
        After=network.target
        
        [Service]
        WorkingDirectory={install_dir}
        ExecStart={start_sh_path}
        Restart=always
        RestartSec=3
        {log_data}
        
        [Install]
        WantedBy=default.target
        """

        with open(service_tmp_path, "w") as f:
            f.write(service_file_contents)
        subprocess.run(["mv", service_tmp_path, service_file_path])
        print("Enabling...")
        subprocess.run(["systemctl", "enable", "--user", "dozer.service"])

        print("Success! Try systemctl --user start dozer.service")

    print()
    print("Successfully installed Dozer bot.")
    print()
    print(*textwrap.wrap("Note: A keyring (a DBus Secret Service provider) is"
                         " required to run the bot with attendance features."
                         " Ensure one is installed before running the bot for"
                         " the first time.", wrap_width), sep='\n')
    print()
    print("You will probably also need to manually import credentials.")
    print("For that, run setup.py with the subcommand 'import'.")

def setup_import():
    print()
    print(" === Dozer Setup ===")
    print("Version 1.0.0")
    print("Task: Import secrets")
    print()

    # import systemd secrets

    print("Where is secrets.json located?")
    print()
    while True:
        secrets_path = input("Enter a path: ")

        if not os.path.exists(secrets_path):
            print(f"Couldn't find secrets file at {secrets_path}, try again.")
            print()
            continue
        if not os.path.isfile(secrets_path):
            print(f"{secrets_path} path is not a file, try again.")
            print()
            continue

        break

    cred_locations = ["Into keyring", "Into the unit file (encrypted)", "Cancel"]
    cred_location = cred_locations[choose_option("How should the"
                                                 " credentials be imported?",
                                                 *cred_locations, default=1)]

    if cred_location == "Cancel":
        print("Abort. --- ")
        sys.exit(0)

    is_systemd = False if cred_location == "Into keyring" else True
    is_system = False # early assignment for the print

    if is_systemd:
        install_paths = ["/usr/local/share/dozerbot", "/opt/dozerbot", "~/.local/share/dozerbot"]
        install_path = install_paths[choose_option("Where is the bot installed? ")]

        is_system = not install_path.startswith("~")
        unit_file_conf_path = os.path.expanduser("~/.config/systemd/user/dozer.service.d/")\
            if not is_system else "/etc/systemd/system/dozer.service.d/"

        print(f"Using {"system" if is_system else "user"} service's unit file")
        print()
        print("Where is the secrets file located?")
        secrets_path = input("Enter a path: ")

        # encrypt
        print("The script will now ask for superuser (required for encryption).")
        out = subprocess.check_call(["sudo", "systemd-creds", "encrypt", "-p",
                        "--name=service_auth", secrets_path, "-"])

        # write to conf
        if not is_system:
            # can use native functions
            pathlib.Path(unit_file_conf_path).mkdir(parents=True, exist_ok=True)
            with open(unit_file_conf_path + "10-creds.conf", "w") as f2:
                f2.write(
                    f"""
                    [Service]
                    {out}
                    """)
        else:
            subprocess.run(["sudo", "mkdir", "-p", unit_file_conf_path])
            with open("/tmp/10-creds.conf", "w") as f2:
                f2.write(
                    f"""
                    [Service]
                    {out}
                    """)
            subprocess.run(["sudo", "mv", "/tmp/10-creds.conf",
                            unit_file_conf_path + "10-creds.conf"])

    print()
    if is_systemd:
        print(f"Successfully imported secrets! Try systemctl"
              f" {"--user" if not is_system else ""} restart dozer.service")
    else:
        print("Successfully imported secrets!")

if __name__ == "__main__":
    main()