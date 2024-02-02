import base64
from pathlib import Path

from googleauth_util import get_cledential

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

SAVE_AS_DIR_PATH = Path("mail_files")

# 画像があるメールメッセージID
MESSAGE_ID = "1889f107f29eeaff"


def decode_base64url(data):
    """Base64URLでエンコードされたデータをデコードする"""
    if data:
        return base64.urlsafe_b64decode(data)
    return None


def download_attachment(service, userId, messageId, attachment_id, filepath):
    """
    添付ファイルをダウンロードして保存する関数
    """
    attachment = (
        service.users()
        .messages()
        .attachments()
        .get(userId=userId, messageId=messageId, id=attachment_id)
        .execute()
    )
    file_data = decode_base64url(attachment["data"])
    with open(filepath, "wb") as f:
        f.write(file_data)
    print(f"Saved attachment to {str(filepath)}")


def find_and_download_attachments(
    service, message_id: str, message_payload: dict, userId: str, directory: Path
):
    """
    メッセージから添付ファイルを探索し、ダウンロードする関数
    """
    directory.mkdir(exist_ok=True)

    for part in message_payload.get("parts", []):
        filename = part.get("filename")
        body = part.get("body", {})
        attachment_id = body.get("attachmentId")

        if filename and attachment_id:
            # 添付ファイルが見つかった場合、ダウンロード
            print(f"filename: {filename}, attachment_id: {attachment_id}")
            filepath = directory / filename
            download_attachment(service, userId, message_id, attachment_id, filepath)

        if "parts" in part:
            # 入れ子になっている場合は再帰的に探索
            find_and_download_attachments(service, message_id, part, userId, directory)


def main():
    creds = get_cledential(SCOPES)
    try:
        service = build("gmail", "v1", credentials=creds)

        # メッセージの取得
        message = service.users().messages().get(userId="me", id=MESSAGE_ID).execute()

        print(f"Message ID: {message['id']}")
        print(f"Message snippet: {message['snippet']}")

        # 添付ファイルの取得
        message_payload = message["payload"]
        find_and_download_attachments(
            service, MESSAGE_ID, message_payload, "me", SAVE_AS_DIR_PATH
        )

    # エラーハンドリング
    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
