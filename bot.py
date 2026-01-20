import matplotlib
matplotlib.use('Agg')  # Serverda grafika uchun
import matplotlib.pyplot as plt
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os

TOKEN = os.getenv("BOT_TOKEN")


# ---- /start ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [["Annuitet"], ["Differensial"]]
    await update.message.reply_text(
        "Kredit hisoblash turini tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

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

# ---- main handler ----
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ⬅️ Ortga tugmasi
    if text == "⬅️ Ortga":
        for key in ["oy", "summa", "yil", "manba"]:
            context.user_data.pop(key, None)
        if "hisob_turi" in context.user_data:
            await choose_credit_type(update)
        else:
            await start(update, context)
        return

    # 1️⃣ Annuitet / Differensial
    if text in ["Annuitet", "Differensial"]:
        context.user_data.clear()
        context.user_data["hisob_turi"] = text
        await choose_credit_type(update)
        return

    # 2️⃣ Kredit manbai
    if text in ["Pensiya", "Ish haqqi", "Avtomashina garovi"]:
        context.user_data["manba"] = text

        if text == "Avtomashina garovi":
            await update.message.reply_text(
                "Avtomashina yilini kiriting (masalan, 2021):",
                reply_markup=ReplyKeyboardMarkup([["⬅️ Ortga"]], resize_keyboard=True)
            )
        else:
            context.user_data["foiz"] = 49
            await update.message.reply_text(
                "Kredit summasini kiriting (so‘m):",
                reply_markup=ReplyKeyboardMarkup([["⬅️ Ortga"]], resize_keyboard=True)
            )
        return

    # 2a️⃣ Avtomashina yili
    if "manba" in context.user_data and context.user_data["manba"] == "Avtomashina garovi" and "yil" not in context.user_data:
        try:
            yil = int(text)
            context.user_data["yil"] = yil
            context.user_data["foiz"] = 48 if yil >= 2021 else 54
            await update.message.reply_text(
                "Kredit summasini kiriting (so‘m):",
                reply_markup=ReplyKeyboardMarkup([["⬅️ Ortga"]], resize_keyboard=True)
            )
        except ValueError:
            await update.message.reply_text("Iltimos, yilni faqat raqam bilan kiriting:")
        return

    # 3️⃣ Kredit summasi
    if "summa" not in context.user_data:
        try:
            summa = float(text.replace(",", ""))
            context.user_data["summa"] = summa
            await update.message.reply_text(
                "Muddatni kiriting (oylarda):",
                reply_markup=ReplyKeyboardMarkup([["⬅️ Ortga"]], resize_keyboard=True)
            )
        except ValueError:
            await update.message.reply_text("Iltimos, summani faqat raqam bilan kiriting:")
        return

    # 4️⃣ Muddat (oylar)
    if "oy" not in context.user_data:
        try:
            oylar = int(text)
            context.user_data["oy"] = oylar
        except ValueError:
            await update.message.reply_text("Iltimos, muddatni butun raqam bilan kiriting:")
            return

        # ---- HISOB ----
        kredit = context.user_data["summa"]
        foiz = context.user_data["foiz"]
        turi = context.user_data["hisob_turi"]
        r = foiz / 12 / 100
        qolgan = kredit
        rows = []

        jami_foiz = 0
        jami_asosiy = 0
        jami_tolov = 0

        if turi == "Annuitet":
            oylik_tolov = kredit * (r * (1 + r) ** oylar) / ((1 + r) ** oylar - 1)
            for i in range(1, oylar + 1):
                oylik_foiz = qolgan * r
                asosiy = oylik_tolov - oylik_foiz
                qolgan -= asosiy

                rows.append([f"{i}-oy", f"{oylik_foiz:,.0f}", f"{asosiy:,.0f}", f"{oylik_tolov:,.0f}", f"{max(qolgan,0):,.0f}"])

                jami_foiz += oylik_foiz
                jami_asosiy += asosiy
                jami_tolov += oylik_tolov
        else:
            asosiy = kredit / oylar
            for i in range(1, oylar + 1):
                oylik_foiz = qolgan * r
                tolov = asosiy + oylik_foiz
                qolgan -= asosiy

                rows.append([f"{i}-oy", f"{oylik_foiz:,.0f}", f"{asosiy:,.0f}", f"{tolov:,.0f}", f"{max(qolgan,0):,.0f}"])

                jami_foiz += oylik_foiz
                jami_asosiy += asosiy
                jami_tolov += tolov

        # ---- JAMINI QO'SHISH (Oxirgi qator, rangsiz) ----
        rows.append(["JAMI", f"{jami_foiz:,.0f}", f"{jami_asosiy:,.0f}", f"{jami_tolov:,.0f}", ""])

        # ---- JADVAL ----
        fig, ax = plt.subplots(figsize=(10,6))
        ax.axis("off")
        table = ax.table(cellText=rows,
                         colLabels=["Oy","Foiz","Asosiy qarz","Oylik to‘lov","Qoldiq summa"],
                         loc="center", cellLoc="center")
        table.scale(1, 1.5)

        for (row, col), cell in table.get_celld().items():
            if row == 0:
                # Sarlavha qatori rangli
                cell.set_facecolor("#cce7ff")
                cell.set_text_props(weight="bold")
            else:
                # Boshqa barcha qatorlar rangsiz (default)
                cell.set_facecolor("#ffffff")
                cell.set_edgecolor("black")

        file_name = f"jadval_{update.effective_user.id}.png"
        plt.savefig(file_name, bbox_inches="tight")
        plt.close()

        caption = f"📊 {turi} kredit jadvali"
        with open(file_name, "rb") as f:
            await update.message.reply_photo(photo=f, caption=caption)

        # --- boshlashga qaytish ---
        await start(update, context)

# ---- app ----
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.run_polling()




