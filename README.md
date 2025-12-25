# About
A python rewrite of the original dozer-discord-bot.
Much of this project is powered by the blue alliance at https://www.thebluealliance.com/

This version of the bot also includes attendance features. This implementation
uses a Google Sheets spreadsheet for storage.

# Setting up
## Dependencies and environment
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
(which is just a more forceful way of using the virtualenv pip.)

## Environment file and keyrings

This bot requires tokens to access several APIs. Obviously they cannot be
hardcoded, thus they are passed through environment variables in a file named
`.env`, which will never be checked into Git.

Entries are formatted like so:
```dotenv
key=value
multi_word_key="extra long entry with spaces!"
```

Make sure to remove trailing whitespace.

If the `.env` file must be located in a different place (i.e. /run/secrets),
set:

```shell
DOZER_DOTENV_PATH=/path/to/.env
```

before running the bot.

Additionally, certain keys are so sensitive that they cannot be stored in
plaintext. Instead they are stored in a keyring (Windows Credential Manager, 
Gnome Secret Service or similar, or macOS's offering), where they are encrypted
at rest.

A keyring must be installed and unlocked for this app to function. If
* you are using **macOS or Windows**: you already have a keyring
* you are running a **mainstream desktop flavour of Linux**: you probably have
  a keyring manager, look for a password manager/keyring app (or similar)
* you are running a server distribution of Linux: check according to your
  specific distribution. Try running:
  ```shell
  gnome-keyring version
  ```
  and see if it exists. The agent must implement the Secret Service, thus
  GNOME keyring or KDE wallet should work for most situations.

## Discord tokens

The bot requires a Discord API token and a guild ID for instant sync. Both are
stored in the `.env` file.

### Creating an app and getting tokens

To create an app:
1. Go to the discord developer's portal.
2. Click on 'new application', and give it a name.
3. Go to the 'Bot' tab and generate/copy the bot's token. Paste it into `.env`
   as below.

To find a server's `guild_id`:
1. Enable developer mode (Settings > Advanced > Developer mode).
2. Right click on a server.
3. Click 'Copy ID'. Paste it into `.env` as below.

To install the app into the server:
1. In the developer's portal, go to 'Installation'.
2. Make sure it has the `applications.commands` scope.
3. Copy the auth link and paste it into the browser.
4. Grant access to the server you want.

A `dev_guild_id` line can be added for development. Commands will sync to both
the production and dev guilds; the dev guild can be used to avoid clogging the
prod server with commands.

Add your credentials to the file in this form: 
```dotenv
# long Base64 token
token=YourTokenHere
# long integer (longer than shown here), accessible from the Discord client
# (guild is API-speak for server)
guild_id=12345678
# like above, but a different server for dev purposes
dev_guild_id=87654321
```

To test it, run:
```shell
python3 main.py --disable-attendance
```
It should authenticate and provide most of the commands.

## Google authentication

The attendance host requires various Google API features to store verification
history. This takes the form of a Google Cloud service account that has a
spreadsheet shared with it.

To set it up:

1. **Set up a Google Cloud project**. Go to the console and create a project,
   and give it a useful name.
2. **Enable the required APIs**, which include:
    * Drive API
    * Sheets API
3. **Go to** IAM/Admin > Service Accounts and create a new service account.
   Give it a convenient name and email address.
4. **Click on the options menu** next to the account, manage its keys, and
   create a new key.
5. **Download this key** to a safe place on a trusted client. **Do not compromise
   this key**. Always keep an encrypted copy on hand - not plaintext, and not
   on the server.
6. **Transfer the key** (in plaintext) to the server. Move it to the bot's
   project root and name it `secrets.json`.
7. (Optional) **Add the following line** to `.env` if the secrets file has a
   different path:
   ```dotenv
   secrets_json_path=/path/to/secrets-file.json
   ```
8. **Run `main.py`** with the argument `--import-secrets`.
9. **Add the following lines** to `.env`:
   ```dotenv
   # service account just created
   service_account=example@foo.iam.gserviceaccount.com
   # the owner of this email will own the main sheet and share it with the
   # service account
   allowable_owner=johndoe@example.test
   ```
10. Using the `allowable_owner`'s associated Google account, **create a
    spreadsheet**. Name it anything, but add the suffix "[attendance-bot]" to
    the end. Avoid editing this sheet as the app stores metadata and state in
    some parts.
11. **Start up the server.**
12. **Expose an attendance client on the same network**, using the associated
    Java package. The two should discover each other automagically.

# Running
The bot takes the following command-line parameter(s):
* `--disable-attendance`: disable all attendance features. The server will 
  not be started and the OAuth tokens will not be used/verified.
* `--import-secrets`: Import the secrets from `secrets.json` into the keyring.
  The program will immediately terminate after success/failure. **Always secure
  the tokens**, do not leave an unsecured copy on the server (keep an encrypted
  copy on a different host). Must not be specified with `--disable-attendance`.

Launch `main.py` with `python3` to run the app.

# Troubleshooting
* **If the bot throws an error about a locked keyring**, exit it and unlock the
keyring before trying again.

* **If the bot produces "unauthorized" or "forbidden" errors**, check the
tokens. Specifically, that they aren't expired and that the correct scopes are
selected.

* **If the bot raises a `ValueError` about how no valid sheet was found**, make
sure that there is a sheet that:
  * is shared with the designated service account;
  * is named with the appropriate suffix (no quotes or extra spaces); and
  * is editable/visible.

Requires the discord.py, statbotics, requests, pillow, and dotenv libraries (as well as attendance libraries mentioned before)

## TODO:
- Implement caching TBA responses with the ETag, If-None-Match and Cache-Control headers
  (see https://www.thebluealliance.com/apidocs)
- Implement the following slash commands:
  - Alliances
  - Rankings
  - EPA Rankings
  - Events
  - Match
  - Schedule
