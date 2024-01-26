import base64
import email
import itertools
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


def list_mimetypes(message, indent=0):
    """
    メッセージのMIMEタイプを再帰的にリストアップし、文字列として返す関数
    """
    mimetype = message.get("mimeType")
    mime_str = " " * indent + mimetype + "\n"
    parts = message.get("parts", [])
    for part in parts:
        mime_str += list_mimetypes(part, indent + 2)
    return mime_str


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
            # メールを収集して、mimetypeの構造の統計を作る。
            # mimetypeの構造の種類をグルーピングしてカウントアップする。

            # メールは100件ほど取得する
            msg_mimetypes = []
            for message_info in inbox_messges[0:100]:
                # print(f"gmail message id:{message_info['id']}")
                # メール本文を取得
                message = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message_info["id"], format="full")
                    .execute()
                )

                # messageのpaylodからmimetypeを元に、本文を取得
                msg_payload = message["payload"]
                # mimetypeを探索的に表示してみる

                mimetype_tree_str = list_mimetypes(msg_payload)
                msg_mimetypes.append(mimetype_tree_str)

            # メールのmimetypeの構造の統計を作る
            # まずはソートをする
            msg_mimetypes.sort()
            # itertools.groupbyを使う
            groupby_mimetypes = itertools.groupby(msg_mimetypes)
            # グルーピングした後に、数をカウントする
            count_mimetypes = [
                (key, len(list(group))) for key, group in groupby_mimetypes
            ]
            # カウントしたものをソートする
            count_mimetypes.sort(key=lambda x: x[1], reverse=True)
            # カウントしたものを表示する
            for key, count in count_mimetypes:
                print(f"{key} : {count}")

    # エラーハンドリング
    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
