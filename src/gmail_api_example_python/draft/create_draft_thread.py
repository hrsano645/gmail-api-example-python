# create_draft_thread.py
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
THREAD_ID = ""  # スレッドIDを指定
MSG_BODY = "返信本文"
ATTACHMENT_PATH = ""  # 添付ファイルのパス


def main():
    creds = get_cledential(SCOPES)
    try:
        service = build("gmail", "v1", credentials=creds)

        # スレッドIDを指定してスレッド情報を取得 -> スレッドの最下部=最新メッセージを取得
        thread = service.users().threads().get(userId="me", id=THREAD_ID).execute()
        # print(thread)
        quote_message = thread["messages"][-1]
        print(
            f'Quoted message id:{quote_message["id"] } snippet:{quote_message["snippet"][:30]}'
        )

        message = EmailMessage()

        # 引用する形で返信する
        # メッセージの種類によっては引用しづらい時がある。引用元のメッセージはtext/planeを使うと良い
        # partsがない場合 = シンプルなテキストベースの場合
        if not quote_message["payload"].get("parts"):
            reply_info = "--- quoted_message ---"
            # 元のメッセージのボディを引用符で囲む
            quoted_body = f'> {base64.urlsafe_b64decode(quote_message["payload"]["body"]["data"]).decode("utf8")}'
            quoted_body = quoted_body.replace("\\", "\\\\").replace("\n", "\n> ")
            reply_body = f"{MSG_BODY}\n{reply_info}\n{quoted_body}"

            message.set_content(reply_body)
        # payloadにpartがある場合は返信元のメッセージを引用しないようにしています
        else:
            message.set_content(MSG_BODY)

        # 送信先を指定: 返信元のメッセージのfromを取得して送信先に設定
        # headersの構造は、以下のようになっている
        # [
        #     {
        #     "name": "To",
        #     "value": "送信先アドレス"
        #     },
        # ...]
        # このようになっているので、nameのtoを探す必要があるので、リスト内包表記で探し、取得したvalueの最初の要素next関数で取得
        message["to"] = next(
            (
                i.get("value", "")
                for i in quote_message["payload"]["headers"]
                if i.get("name").lower() == "from"
            )
        )
        quoted_subject = next(
            (
                i.get("value", "")
                for i in quote_message["payload"]["headers"]
                if i.get("name").lower() == "subject"
            )
        )
        message["subject"] = f"Re: {quoted_subject}"

        # References,In-Reply-Toを設定する
        # 返信先のメッセージのMessage-IDを取得して、それを設定する
        message_id = next(
            (
                i.get("value", "")
                for i in quote_message["payload"]["headers"]
                if i.get("name").lower() == "message-id"
            )
        )
        message["reply-to"] = message_id
        message["references"] = message_id

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
