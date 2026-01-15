#!/usr/bin/env sh

# start.sh
# quickly source .venv and start up
# this script should be entirely sh-compliant

# if no arguments, use .venv
# if there is one argument, use it as a target
# if the one argument is --help/-h/-?, show help
# if there are two or more, throw error

VENV_TARGET=".venv"

# print help

help() {
  echo "Usage:";
  echo " setup.sh [--help|-h|-?|<venv-location>]";
  echo " <venv-location>: The location of a virtualenv folder (optional, must not be specified with anything else). Defaults to '.venv'.";
  echo " --help/-h/-?: Print this help (optional, must not be specified with anything else)";
  echo "venv-location must not be named '--help', '-h' or '-?'";
  exit "$1";
}

# parse argument (just one)

if [ $# -gt 1 ]; then
  echo "Too many arguments";
  help 1;
fi

if [ $# -eq 1 ]; then
  # check for target/help
  if [ "$1" = "--help" ] || [ "$1" = "-h" ] || [ "$1" = "-?" ]; then
    help 0;
  else
    VENV_TARGET="$1";
  fi
fi

# check for venv and main.py
if ! [ -e "$VENV_TARGET" ] || ! [ -d "$VENV_TARGET" ]; then
  echo "Cannot find directory $VENV_TARGET";
  help 1;
fi
if ! [ -e "main.py" ] || ! [ -f "main.py" ]; then
  echo "Cannot find main.py";
  help 1;
fi

# source but sh
. "$VENV_TARGET"/bin/activate;

# run
"$VENV_TARGET"/bin/python3 main.py;
