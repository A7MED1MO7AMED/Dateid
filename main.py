import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# BOT TOKEN
# =========================
TOKEN = "8824897435:AAHYNuoRRTqr0zgavzXIv_oipj8MhL2Lr_s"

# =========================
# LOAD RANGE DATASET
# =========================
with open("telegram_ranges_dataset.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

# =========================
# SMART MONTH PREDICTION
# =========================
def predict_month(user_id):

    user_id = int(user_id)

    best_month = None
    best_score = float("inf")

    for item in DATA:

        month = item["month"]

        min_id = item["min"]
        max_id = item["max"]
        center = item["center"]
        count = item["count"]

        # =========================
        # INSIDE RANGE
        # =========================
        if min_id <= user_id <= max_id:

            # distance from center
            center_distance = abs(user_id - center)

            # strong bonus for being inside
            score = center_distance * 0.35

        else:

            # distance from nearest edge
            edge_distance = min(
                abs(user_id - min_id),
                abs(user_id - max_id)
            )

            center_distance = abs(user_id - center)

            score = (
                edge_distance * 1.0 +
                center_distance * 0.15
            )

        # =========================
        # DENSITY BONUS
        # =========================
        score /= (1 + count * 0.03)

        # =========================
        # BEST MATCH
        # =========================
        if score < best_score:

            best_score = score
            best_month = month

    return best_month

# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "1Send Telegram IDs separated by spaces or lines.\n\n"
        "Example:\n"
        "8374818286\n"
        "7019795401\n"
        "6665067360"
    )

    await update.message.reply_text(text)

# =========================
# HANDLE IDS
# =========================
async def handle_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):

    raw_text = update.message.text

    ids = raw_text.split()

    results = []

    for uid in ids:

        if not uid.isdigit():

            results.append(f"{uid} -> Invalid ID")
            continue

        try:

            result = predict_month(uid)

            results.append(f"{uid} → {result}")

        except Exception as e:

            results.append(f"{uid} -> Error")

    final_text = "\n".join(results)

    await update.message.reply_text(final_text)

# =========================
# MAIN
# =========================
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_ids
        )
    )

    print("Bot running...")

    app.run_polling()

if __name__ == "__main__":
    main()
