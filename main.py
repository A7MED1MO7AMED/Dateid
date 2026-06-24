import requests
import time
import threading
from datetime import datetime

URL = "https://natiga.qalubiaedu.org/student/72962/"

BOT_TOKEN = "6892342001:AAHJQhBTjipchtrAZU7b0C6TsFsayY-KQPM"

monitoring = False
sent = False
last_update_id = 0


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def send_message(chat_id, text):
    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        params={
            "chat_id": chat_id,
            "text": text
        }
    )


def monitor(chat_id):
    global sent, monitoring

    while monitoring:
        try:
            log("بدء فحص الصفحة...")

            response = requests.get(
                URL,
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            log(f"تم جلب الصفحة بنجاح - Status Code: {response.status_code}")

            html = response.text

            log(f"حجم الصفحة: {len(html)} حرف")

            found_second_term = "الفصل الدراسي الثاني" in html
            found_280 = "280" in html

            log(
                f"نتيجة الفحص: الفصل الدراسي الثاني = {found_second_term} | 280 = {found_280}"
            )

            if found_second_term or found_280:

                log("تم العثور على الشرط المطلوب!")

                if not sent:

                    log("جاري إرسال ملف HTML...")

                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                        data={"chat_id": chat_id},
                        files={
                            "document": (
                                "result.html",
                                html.encode("utf-8"),
                                "text/html"
                            )
                        }
                    )

                    log("تم إرسال الملف")

                    send_message(
                        chat_id,
                        "🚨 تم العثور على الفصل الدراسي الثاني أو الرقم 280"
                    )

                    sent = True

            else:
                log("لم يتم العثور على أي شرط")

            log("انتظار 60 ثانية...\n")
            time.sleep(60)

        except Exception as e:
            log(f"خطأ أثناء الفحص: {e}")
            log("انتظار 90 ثانية...\n")
            time.sleep(90)


log("تم تشغيل البرنامج")

while True:
    try:

        updates = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
            params={
                "offset": last_update_id + 1,
                "timeout": 10
            }
        ).json()

        for update in updates["result"]:

            last_update_id = update["update_id"]

            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")

            log(f"رسالة واردة: {text}")

            if text == "/start":

                if not monitoring:

                    monitoring = True
                    sent = False

                    threading.Thread(
                        target=monitor,
                        args=(chat_id,),
                        daemon=True
                    ).start()

                    send_message(
                        chat_id,
                        "✅ البوت شغال وبدأ فحص الصفحة كل دقيقة."
                    )

                    log("تم بدء الفحص")

                else:

                    send_message(
                        chat_id,
                        "✅ البوت شغال بالفعل."
                    )

                    log("تم استلام /start والبوت يعمل بالفعل")

            elif text == "/stop":

                monitoring = False

                send_message(
                    chat_id,
                    "⏹️ تم إيقاف الفحص."
                )

                log("تم إيقاف الفحص")

        time.sleep(2)

    except Exception as e:

        log(f"خطأ في البوت: {e}")
        time.sleep(5)