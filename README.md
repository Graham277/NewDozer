### This is a forked version of the original at https://github.com/Graham277/NewDozer.

## About
A python rewrite of the original dozer-discord-bot.
Much of this project is powered by the blue alliance at https://www.thebluealliance.com/

## Setting up
### Dependencies
The project requires multiple dependencies, including:
* `discord`
* `dotenv`
* `keyring`
* various Google APIs

The package also may require a virtualenv environment to function.
First `cd` to the project directory, then set up like so:
```shell
virtualenv .venv
source .venv/activate # on Linux
```
<!-- TODO: add instructions for Windows machines -->

Certain IDEs (i.e. PyCharm) have these functions condensed into a menu.

To install dependencies, run:
```shell
pip install -r requirements.txt
```

… which will install all pip packages in requirements.txt.

If `pip` has the same problem with system packages, try:
```shell
./.venv/bin/python3 ./.venv/bin/pip install -r requirements.txt
```
### Discord tokens

The bot requires Discord tokens for a bot, which need to be placed into a file
named `.env`.

Add your token to the file in this form: 
```dotenv
token=YourTokenHere
```
Add the id of the guild the bot will be run on to the dotenv.
This provides instant syncing to the guild and is required for this bot.
```dotenv
guild_id=YourGuildIdHere
```

If doing development, you can add a "dev_guild_id" as well, and the commands
will sync to both guilds. This allows you to develop and test the status on
your own server without clogging up the production server.

### Setting up the attendance scripts
1. Install a keyring manager. On a desktop system, this should already exist;
   it may need to be added for a server.
2. Configure and OAuth2 client (in Google Cloud) that has access to the `files`
   scope for Google Sheets (can read and write files used with this
   application).
3. Set up the credentials. TODO: specify which credentials are needed.
4. Install the client on a device on the same network. They should discover
   each other.

## Running
The bot takes the following command-line parameter(s):
* `--disable-attendance`: disable all attendance features. The server will 
  not be started and the OAuth tokens will not be used/verified.

Launch `main.py` with `python3` to run the app.

## Troubleshooting
If the bot throws an error about a locked keyring, exit it and unlock the
keyring before trying again.

If the bot produces "unauthorized" or "forbidden" errors, check the tokens.
Specifically, that they aren't expired and that the correct scopes are
selected.