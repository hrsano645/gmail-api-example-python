from googleauth_util import get_cledential

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
    creds = get_cledential(SCOPES)
    try:
        service = build("gmail", "v1", credentials=creds)

        # ラベルの一覧を収集
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        print("Labels:")
        # ラベル名とIDを表示
        for label in labels:
            print(f"{label['name']}: {label['id']}")

    # エラーハンドリング
    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
