import json
from collections import defaultdict
from statistics import median
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
    try:
        uid = int(item["id"])
        month = item["month"]
        MONTH_CLUSTERS[month].append(uid)
    except:
        pass

# =========================
# REMOVE OUTLIERS
# =========================
def remove_outliers(ids):

    if len(ids) < 4:
        return ids

    ids = sorted(ids)

    q1 = ids[len(ids)//4]
    q3 = ids[(len(ids)*3)//4]

    iqr = q3 - q1

    low = q1 - (1.5 * iqr)
    high = q3 + (1.5 * iqr)

    filtered = [
        x for x in ids
        if low <= x <= high
    ]

    return filtered if filtered else ids

# =========================
# CALCULATE MONTH STATS
# =========================
MONTH_STATS = {}

for month, ids in MONTH_CLUSTERS.items():

    ids = remove_outliers(ids)

    ids.sort()

    MONTH_STATS[month] = {
        "min": min(ids),
        "max": max(ids),
        "median": median(ids),
        "count": len(ids)
    }

# =========================
# SORT MONTHS
# =========================
SORTED_MONTHS = sorted(MONTH_STATS.keys())

# =========================
# SMART PREDICTION
# =========================
def predict_month(user_id):

    user_id = int(user_id)

    best_month = None
    best_score = float("inf")

    for month in SORTED_MONTHS:

        stats = MONTH_STATS[month]

        min_id = stats["min"]
        max_id = stats["max"]
        med = stats["median"]
        count = stats["count"]

        # inside month range
        if min_id <= user_id <= max_id:

            center_distance = abs(user_id - med)

            score = center_distance * 0.4

        else:

            if user_id < min_id:
                edge_distance = min_id - user_id
            else:
                edge_distance = user_id - max_id

            center_distance = abs(user_id - med)

            score = (
                edge_distance * 1.2 +
                center_distance * 0.3
            )

        # dense month bonus
        score /= (1 + count * 0.08)

        if score < best_score:
            best_score = score
            best_month = month

    return best_month

# =========================
# START
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

        except Exception as e:

            results.append(f"{uid} -> Error")

    await update.message.reply_text(
        "\n".join(results)
    )

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
