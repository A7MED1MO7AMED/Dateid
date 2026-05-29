import json
from collections import defaultdict
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
# LOAD DATASET
# =========================
with open("telegram_cleaned_dataset.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

# =========================
# BUILD MONTH CLUSTERS
# =========================
MONTH_CLUSTERS = defaultdict(list)

for item in DATA:
    MONTH_CLUSTERS[item["month"]].append(int(item["id"]))

# =========================
# CALCULATE MONTH STATS
# =========================
MONTH_STATS = {}

for month, ids in MONTH_CLUSTERS.items():

    ids.sort()

    avg_id = sum(ids) / len(ids)

    min_id = min(ids)
    max_id = max(ids)

    MONTH_STATS[month] = {
        "avg": avg_id,
        "min": min_id,
        "max": max_id,
        "count": len(ids)
    }

# =========================
# SMART MONTH PREDICTION
# =========================
def predict_month(user_id):

    user_id = int(user_id)

    best_month = None
    best_score = float("inf")

    for month, stats in MONTH_STATS.items():

        avg_id = stats["avg"]
        min_id = stats["min"]
        max_id = stats["max"]
        count = stats["count"]

        # Distance from average
        avg_distance = abs(user_id - avg_id)

        # Distance from range
        if user_id < min_id:
            range_distance = min_id - user_id

        elif user_id > max_id:
            range_distance = user_id - max_id

        else:
            range_distance = 0

        # Smart score
        score = (
            avg_distance * 0.7
            + range_distance * 1.3
        )

        # Bonus for dense clusters
        score /= (1 + (count * 0.05))

        if score < best_score:
            best_score = score
            best_month = month

    return best_month

# =========================
# START COMMAND
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "Send Telegram IDs separated by spaces or lines.\n\n"
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

        except Exception:

            results.append(f"{uid} -> Error")

    final_text = "\n".join(results)

    await update.message.reply_text(final_text)

# =========================
# MAIN
# =========================
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

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
