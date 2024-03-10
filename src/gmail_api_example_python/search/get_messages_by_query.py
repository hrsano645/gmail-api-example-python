from googleauth_util import get_cledential

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

SEARCHQUERY = "subject:Google"


# MessagePartからヘッダー>sujbectを取得
def get_subject(message_detail):
    return next(
        (
            header["value"]
            for header in message_detail["payload"]["headers"]
            if header["name"] == "Subject"
        ),
        None,
    )


def main():
    creds = get_cledential(SCOPES)
    try:
        service = build("gmail", "v1", credentials=creds)

        # ラベルからメッセージ一覧を取得
        results = service.users().messages().list(userId="me", q=SEARCHQUERY).execute()
        messages = results.get("messages", [])

        # メッセージIDを表示
        for message in messages[:10]:
            # メッセージのサブジェクトを表示
            message_detail = (
                service.users().messages().get(userId="me", id=message["id"]).execute()
            )
            print(f"ID:{message['id']}  - {get_subject(message_detail)}")

    # エラーハンドリング
    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
