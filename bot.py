from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import os
TOKEN = os.environ.get("BOT_TOKEN")


# ---- /start ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [["Annuitet"], ["Differensial"]]
    await update.message.reply_text(
        "Kredit hisoblash turini tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---- main handler ----
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ⬅️ ORTGA
    if text == "⬅️ Ortga":
        if "summa" in context.user_data:
            context.user_data.pop("summa", None)
            await choose_credit_type(update)
        elif "manba" in context.user_data:
            context.user_data.pop("manba", None)
            await choose_calc_type(update)
        else:
            await start(update, context)
        return

    # 1️⃣ Annuitet / Differensial
    if text in ["Annuitet", "Differensial"]:
        context.user_data.clear()
        context.user_data["hisob_turi"] = text
        await choose_credit_type(update)

    # 2️⃣ Kredit manbai
    elif text in ["Pensiya", "Ish haqqi", "Avtomashina garovi"]:
        context.user_data["manba"] = text

        if text == "Avtomashina garovi":
            context.user_data["foiz"] = 48
        else:
            context.user_data["foiz"] = 49

        await update.message.reply_text(
            "Kredit summasini kiriting (so‘m):",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Ortga"]], resize_keyboard=True)
        )

    # 3️⃣ Kredit summasi
    elif "summa" not in context.user_data:
        context.user_data["summa"] = float(text)
        await update.message.reply_text(
            "Muddatni kiriting (oylarda):",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Ortga"]], resize_keyboard=True)
        )

    # 4️⃣ Oylar → HISOB
    elif "oy" not in context.user_data:
        context.user_data["oy"] = int(text)

        kredit = context.user_data["summa"]
        foiz = context.user_data["foiz"]
        oylar = context.user_data["oy"]
        turi = context.user_data["hisob_turi"]

        r = foiz / 12 / 100
        qolgan = kredit
        rows = []

        if turi == "Annuitet":
            oylik_tolov = kredit * (r * (1 + r) ** oylar) / ((1 + r) ** oylar - 1)

            for i in range(1, oylar + 1):
                oylik_foiz = qolgan * r
                asosiy = oylik_tolov - oylik_foiz
                qolgan -= asosiy

                rows.append([
                    f"{i}-oy",
                    f"{oylik_foiz:,.0f}",
                    f"{asosiy:,.0f}",
                    f"{oylik_tolov:,.0f}",
                    f"{max(qolgan, 0):,.0f}"
                ])
        else:
            asosiy = kredit / oylar
            for i in range(1, oylar + 1):
                oylik_foiz = qolgan * r
                tolov = asosiy + oylik_foiz
                qolgan -= asosiy

                rows.append([
                    f"{i}-oy",
                    f"{oylik_foiz:,.0f}",
                    f"{asosiy:,.0f}",
                    f"{tolov:,.0f}",
                    f"{max(qolgan, 0):,.0f}"
                ])

        # 🎨 Rangli jadval
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.axis("off")

        table = ax.table(
            cellText=rows,
            colLabels=["Oy", "Foiz", "Asosiy qarz", "Oylik to‘lov", "Qoldiq summa"],
            loc="center",
            cellLoc="center"
        )

        table.scale(1, 1.5)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_facecolor("#cce7ff")
                cell.set_text_props(weight="bold")
            else:
                if col == 3:
                    cell.set_facecolor("#eeeeee")
                else:
                    cell.set_facecolor("#ffffff")
                cell.set_edgecolor("black")

        plt.savefig("jadval.png", bbox_inches="tight")
        plt.close()

        await update.message.reply_photo(
            photo=open("jadval.png", "rb"),
            caption=f"📊 {turi} kredit jadvali"
        )

        await start(update, context)

# ---- yordamchi menyular ----
async def choose_calc_type(update):
    keyboard = [["Annuitet"], ["Differensial"]]
    await update.message.reply_text(
        "Kredit hisoblash turini tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def choose_credit_type(update):
    keyboard = [
        ["Pensiya"],
        ["Ish haqqi"],
        ["Avtomashina garovi"],
        ["⬅️ Ortga"]
    ]
    await update.message.reply_text(
        "Kredit manbasini tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---- app ----
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling()
