import datetime
import json
import os

import keyring
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Partially derived from:
# - https://developers.google.com/workspace/sheets/api/quickstart/python
# - https://developers.google.com/identity/protocols/oauth2/service-account#python
# - https://docs.cloud.google.com/iam/docs/create-short-lived-credentials-direct#python
# See https://www.apache.org/licenses/LICENSE-2.0 for their licenses, even
# though this code is undeniably now a separate work (not under Apache 2.0).

class SheetManager:

    # These scopes are fairly wide-ranging but only applicable to the service account.
    CONST_SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "https://www.googleapis.com/auth/spreadsheets"]

    account_name = None
    allowable_owner = None
    secret_file = ""
    static_token: service_account.Credentials = None
    sheets_service = None

    def __init__(self, secret_name: str = "secrets.json"):
        self.secret_file = secret_name
        self.account_name = os.getenv("service_account")
        self.allowable_owner = os.getenv("allowable_owner")
        pass

    def import_secrets(self):
        """
        Import client secrets from a file to the keyring.
        Do not call anything after this method. If the file does not exist, the
        method exits the interpreter.
        :return: nothing
        """
        try:
            with open(self.secret_file) as f:
                self._lock_token(f.read())
                print("Successfully imported secrets")
        except FileNotFoundError:
            print(f"The file {self.secret_file} does not exist! Cannot import keys.")
            exit(1)

    def unlock_token(self):
        """
        Get the service account credentials from the keyring, then put them in
        `static_token`.
        :return:
        """
        try:
            raw_data = keyring.get_keyring().get_credential("dozer_service_secrets", "service_auth").password
            self.static_token = service_account.Credentials.from_service_account_info(json.loads(raw_data), scopes=self.CONST_SCOPES)
        except keyring.errors.InitError | keyring.errors.NoKeyringError as e:
            # use systemd-creds
            creds_folder = os.getenv("CREDENTIALS_DIRECTORY")
            if creds_folder is None:
                raise e
            raw_data = open(creds_folder + os.path.sep + "service_auth").read()
            self.static_token = service_account.Credentials.from_service_account_info(json.loads(raw_data), scopes=self.CONST_SCOPES)

    def _lock_token(self, data: str):
        """
        Internal: Save the service account credentials to the keyring.
        :return: nothing
        """
        keyring.set_password("dozer_service_secrets", "service_auth", data)

    def find_sheet(self, suffix: str):
        """
        Find a possible sheet to store attendance, matching the given suffix.
        Chooses one arbitrarily if there is more than one sheet.
        :param suffix: suffix to match
        :return: The sheet's ID, or None if nothing is found
        """
        if self.static_token is None:
            self.unlock_token()
        drive_service = build("drive", "v3", credentials=self.static_token)
        results = drive_service.files().list(fields="nextPageToken, files(id, name, mimeType, owners)").execute()
        files = results.get("files", [])



        for file in files:
            owners = []
            for owner in file['owners']:
                owners.append(owner["emailAddress"])
            if file['mimeType'] == "application/vnd.google-apps.spreadsheet" and file['name'].endswith(suffix)\
                    and self.allowable_owner in owners:
                return file['id']

        return None


    def add_line(self, timestamp: datetime.datetime, handle: str, display_name: str, sheet_id: str):
        """
        Add a line to the specified sheet.
        :param timestamp: entry for timestamp column
        :param handle: user's handle - mostly internal
        :param display_name: user's display/friendly name - probably includes their real name
        :param sheet_id: spreadsheet ID
        :return: nothing
        """
        # First: initialize if not done before - double nested
        first_cell = self._get(sheet_id, "A1")
        if not any(first_cell):
            self._set(sheet_id, "A1:E1", [["Timestamp", "Handle", "Display name", 2, "!! NOTE: avoid editing anything in this sheet!"]])

        # set the line
        # first find the first available row
        row_index: int = int(self._get(sheet_id, "D1")[0][0])

        # check to see if that row is populated. If so, scan down the sheet until it isn't
        while any(self._get(sheet_id, f"A{row_index}")):
            row_index += 1

        # insert a new row
        self._set(sheet_id, f"A{row_index}:C{row_index}", [[timestamp.strftime("%Y-%m-%d %H:%M:%S"), handle, display_name]])
        row_index += 1

        # write back index
        self._set(sheet_id, "D1", [[row_index]])
        pass

    def _get(self, sheet_id: str, data_range: str):
        """
        Internal: Get the data of a specific range. Creates the required
        service if none exists.
        :param sheet_id: The sheet to operate on
        :param data_range: The data range, in the standard API format
        :return: A 2d array of data representing the stored values. Always 2d even if the range is not.
        """
        if self.static_token is None:
            self.unlock_token()
        if not self.sheets_service:
            self.sheets_service = build("sheets", "v4", credentials=self.static_token).spreadsheets()
        result = self.sheets_service.values().get(spreadsheetId=sheet_id, range=data_range).execute()
        return result.get("values", [])

    def _set(self, sheet_id: str, data_range: str, data: list[list]):
        """
        Internal: Set a specific range to the given 2d array of data. Creates
        the required service if none exists.
        :param sheet_id: The sheet to operate on
        :param data_range: The data range, in the standard API format
        :param data: A 2d array of data - even if the data is not really 2d, a 2d array should be used
        :return: The amount of cells updated
        """
        if self.static_token is None:
            self.unlock_token()
        if not self.sheets_service:
            self.sheets_service = build("sheets", "v4", credentials=self.static_token).spreadsheets()

        result = (self.sheets_service.values()
            .update(
                spreadsheetId=sheet_id, range=data_range,
                valueInputOption="RAW", body={"values": data}
            ).execute()
        )
        return result.get('updatedCells')