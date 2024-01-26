import base64
import email
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


def get_plain_text_body(payload):
    """
    text/plain MIMEタイプのメール本文を取得する関数
    mimetypeが入れ子構造になっているため、探索的にtext/planeを探す
    """
    mimetype = payload.get("mimeType")
    if mimetype == "text/plain":
        body = payload.get("body", {})
        data = body.get("data")
        if data:
            text = base64.urlsafe_b64decode(data).decode("utf-8")
            return text

    parts = payload.get("parts", [])
    for part in parts:
        text = get_plain_text_body(part)
        if text:
            return text
    return None


# ヘッダも名前を元に探索的に探す
def get_header_by_name(payload, name):
    """
    メッセージのヘッダを再帰的に探索し、nameに一致するヘッダを返す関数
    """
    headers = payload.get("headers", [])
    for header in headers:
        if header["name"] == name:
            return header["value"]
    return None


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
            # メールが多い場合を想定して最大2件を表示
            for message_info in inbox_messges[0:3]:
                print(f"gmail message id:{message_info['id']}")
                # メール本文を取得
                message = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message_info["id"], format="full")
                    .execute()
                )

                # messageのpaylodからmimetypeを元に、本文を取得
                msg_payload = message["payload"]

                # ヘッダーからタイトルを取得
                subject = get_header_by_name(msg_payload, "Subject")
                print(f"subject:{subject}")

                # 探索的にtext/planeを探して表示する
                plain_text_body = get_plain_text_body(msg_payload)
                if plain_text_body:
                    print(f"{plain_text_body[0:20]}\n")

    # エラーハンドリング
    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
