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

    # build sorted points
    points = []

    for month, stats in MONTH_STATS.items():

        points.append({
            "month": month,
            "min": stats["min"],
            "max": stats["max"],
            "median": stats["median"]
        })

    # sort by median id
    points.sort(key=lambda x: x["median"])

    best = None
    best_distance = float("inf")

    # nearest median search
    for point in points:

        dist = abs(user_id - point["median"])

        if dist < best_distance:

            best_distance = dist
            best = point

    # refinement:
    # if inside another month range -> prioritize it

    inside_candidates = []

    for point in points:

        if point["min"] <= user_id <= point["max"]:

            range_center = (
                point["min"] +
                point["max"]
            ) / 2

            dist = abs(user_id - range_center)

            inside_candidates.append(
                (dist, point)
            )

    if inside_candidates:

        inside_candidates.sort(
            key=lambda x: x[0]
        )

        best = inside_candidates[0][1]

    return best["month"]
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
