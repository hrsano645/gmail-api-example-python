from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# トークンとクレデンシャルの保存先
token_save_path = Path("google_api_access_token.json")
cred_json = Path("credentials.json")


# クレデンシャルの取得用の関数
def get_cledential(scopes: list[str]) -> Credentials:
    """
    Google APIの認証情報をOAuth2の認証フロー（クライアントシークレット）で取得します。
    既に認証情報があればそれを返します。
    リフレッシュトークンに対応しています。
    なければ認証情報を取得し、google_api_access_token.jsonに保存します。
    args:
        scopes: 認証情報を取得する際に必要なスコープ
    return:
        認証情報
    """
    creds = None
    if token_save_path.exists():
        creds = Credentials.from_authorized_user_file(token_save_path, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(cred_json, scopes)
            creds = flow.run_local_server(port=18081)
        with token_save_path.open("w") as token:
            token.write(creds.to_json())
    return creds


def main():
    creds = get_cledential(SCOPES)
    try:
        service = build("gmail", "v1", credentials=creds)

        # 受信トレイのメールメッセージを収集
        result = (
            service.users().messages().list(userId="me", labelIds="INBOX").execute()
        )
        inbox_messges = result.get("messages", [])
        if not inbox_messges:
            print("No messages in inbox.")
        else:
            print("Inbox Messages:")
            # メールが多い場合を想定して最大10件を表示
            for message in inbox_messges[0:10]:
                print(message["id"])
                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"])
                    .execute()
                )
                print(msg["snippet"])

    # エラーハンドリング
    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
