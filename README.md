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
2. Set up a service account on a Google Cloud project and create a key for it.
   **Do not lose or compromise this key**. They can be recreated/disabled but
   always keep security in mind.
3. Add two lines to `.env`:
   ```dotenv
   service_account=example@foo.iam.gserviceaccount.com
   allowable_owner=johndoe@example.io
   ```
   The first email should match the service account name.

   The second should be a regular account that will own the spreadsheet.
4. Place the token in the same folder as `main.py`, name it `secrets.json` and
   run `main.py` with the argument `--import-secrets`.
5. Make sure you have an encrypted copy of the token on another device, and
   destroy it. Never leave a plaintext copy on a device.
6. Create a spreadsheet on the account listed in the `allowable_owner` field.
   Its name should end with "\[attendance-bot\]" *exactly*. Avoid editing the 
   top row. Share this sheet with the service account.
7. Install the code client on a device on the same network. They should
   discover each other automagically.

## Running
The bot takes the following command-line parameter(s):
* `--disable-attendance`: disable all attendance features. The server will 
  not be started and the OAuth tokens will not be used/verified.
* `--import-secrets`: Import the secrets from `secrets.json` into the keyring.
  The program will immediately terminate after success/failure. **Always secure
  the tokens**, do not leave an unsecured copy on the server (keep an encrypted
  copy on a different host). Must not be specified with `--disable-attendance`.

Launch `main.py` with `python3` to run the app.

## Troubleshooting
If the bot throws an error about a locked keyring, exit it and unlock the
keyring before trying again.

If the bot produces "unauthorized" or "forbidden" errors, check the tokens.
Specifically, that they aren't expired and that the correct scopes are
selected.

If the bot raises a `ValueError` about how no valid sheet was found, make sure
that there is a sheet that:
* is shared with the designated service account;
* is named with the appropriate suffix (no quotes or extra spaces); and
* is editible/visible.