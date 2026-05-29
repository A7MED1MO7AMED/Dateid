import json
from bisect import bisect_left
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ====== BOT TOKEN ======
TOKEN = "8824897435:AAHYNuoRRTqr0zgavzXIv_oipj8MhL2Lr_s"

# ====== LOAD DATASET ======
with open("telegram_cleaned_dataset.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

# Sort dataset by ID
DATA.sort(key=lambda x: int(x["id"]))

IDS = [int(x["id"]) for x in DATA]


# ====== SMART PREDICTION ======
def predict_date(user_id, neighbors=6):
    user_id = int(user_id)

    pos = bisect_left(IDS, user_id)

    nearby = []

    start = max(0, pos - neighbors)
    end = min(len(DATA), pos + neighbors)

    for i in range(start, end):
        item = DATA[i]

        anchor_id = int(item["id"])
        distance = abs(user_id - anchor_id)

        nearby.append({
            "month": item["month"],
            "distance": distance
        })

    scores = {}

    for item in nearby:
        month = item["month"]

        # +1 عشان منع division by zero
        distance = item["distance"] + 1

        weight = 1 / distance

        scores[month] = scores.get(month, 0) + weight

    best_month = max(scores, key=scores.get)

    return best_month


# ====== START COMMAND ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Send Telegram IDs separated by spaces or lines.\n\n"
        "Example:\n"
        "8374818286\n"
        "7019795401\n"
        "6665067360"
    )

    await update.message.reply_text(text)


# ====== HANDLE IDS ======
async def handle_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):

    raw_text = update.message.text

    # Split by spaces/newlines
    ids = raw_text.split()

    results = []

    for uid in ids:

        # Validate
        if not uid.isdigit():
            results.append(f"{uid} -> Invalid ID")
            continue

        try:
            predicted = predict_date(uid)

            results.append(f"{uid} → {predicted}")

        except Exception:
            results.append(f"{uid} -> Error")

    final_text = "\n".join(results)

    await update.message.reply_text(final_text)


# ====== MAIN ======
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ids)
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()