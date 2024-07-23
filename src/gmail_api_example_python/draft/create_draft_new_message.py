# create_draft_new_message.py
import base64
from email.message import EmailMessage

# こちらを参考: https://hr-sano.net/blog/gmail-api-read-attachment/#get_cledential
from googleauth_util import get_cledential

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# readonlyに、下書きを作成するための権限を追加
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

# 利用する際に入力します
SUBJECT = "タイトル"
BODY = "本文"
TO_ADDRESS = ""  # 送信先
ATTACHMENT_PATH = ""  # 添付ファイルのパス


def main():
    creds = get_cledential(SCOPES)
    try:
        service = build("gmail", "v1", credentials=creds)

        # 下書きを作成
        message = EmailMessage()
        message.set_content(BODY)
        message["subject"] = SUBJECT
        message["to"] = TO_ADDRESS

        # 添付ファイルがある場合は追加
        # TODO: ここでは一つのファイルしか扱っていない。複数の場合はループ処理で登録する
        if ATTACHMENT_PATH:
            with open(ATTACHMENT_PATH, "rb") as f:
                attachment = f.read()
            message.add_attachment(
                attachment,
                maintype="application",
                subtype="octet-stream",
                filename=ATTACHMENT_PATH,
            )

        # apiで下書きを作成する
        draft = (
            service.users()
            .drafts()
            .create(
                userId="me",
                body={
                    "message": {
                        "raw": base64.urlsafe_b64encode(message.as_bytes()).decode()
                    }
                },
            )
            .execute()
        )
        print(f"Create draft. Draft id: {draft['id']}")

    # エラーハンドリング
    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
