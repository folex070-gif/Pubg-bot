import logging
import random
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8854926116:AAHy-j_NVgWaAsZEDp7ZuxiVPsh3kn2p6zE"
ADMIN_ID = 8484899374
CHANNEL_USERNAME = "@TopAliyADMIN"  # Kanal username

# ===================== MA'LUMOTLAR =====================
# users = { user_id: { "uc": 0, "last_spin": None, "extra_spins": 0, "pubg_id": None, "referred_by": set() } }
users = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===================== YORDAMCHI FUNKSIYALAR =====================

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "uc": 0,
            "last_spin": None,
            "extra_spins": 0,
            "pubg_id": None,
            "referred_users": set()
        }
    return users[user_id]


async def check_subscription(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


def can_spin(user_data):
    today = date.today().isoformat()
    if user_data["last_spin"] != today:
        return True
    if user_data["extra_spins"] > 0:
        return True
    return False


# ===================== /start =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_data = get_user(user_id)

    # Referal tekshirish
    if context.args:
        ref_id = context.args[0]
        if ref_id.isdigit():
            ref_id = int(ref_id)
            if ref_id != user_id and ref_id in users:
                ref_data = users[ref_id]
                if user_id not in ref_data["referred_users"]:
                    ref_data["referred_users"].add(user_id)
                    ref_data["extra_spins"] += 1
                    await context.bot.send_message(
                        ref_id,
                        f"🎉 Yangi do'st qo'shildi! Siz 1 ta qo'shimcha aylantirish oldingiz!"
                    )

    # Kanal tekshirish
    is_subscribed = await check_subscription(user_id, context.bot)
    if not is_subscribed:
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check_sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ Botdan foydalanish uchun avval kanalimizga obuna bo'ling!\n\n"
            f"📢 Kanal: {CHANNEL_USERNAME}",
            reply_markup=reply_markup
        )
        return

    await show_main_menu(update, user)


async def show_main_menu(update, user):
    user_data = get_user(user.id)
    keyboard = [
        [InlineKeyboardButton("🎡 Barabanni aylantirish", callback_data="spin")],
        [InlineKeyboardButton("👥 Do'st taklif qilish", callback_data="referral")],
        [InlineKeyboardButton("💰 UC Yechib olish", callback_data="withdraw")],
        [InlineKeyboardButton("📊 Mening hisobim", callback_data="profile")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"🎮 Salom, {user.first_name}!\n\n"
        f"🏆 PUBG UC Bot ga xush kelibsiz!\n\n"
        f"💎 UC Balansingiz: {user_data['uc']} UC\n"
        f"🎡 Bugungi aylantirish: {'✅ Mavjud' if can_spin(user_data) else '❌ Tugagan'}\n\n"
        f"Minimum 60 UC yig'sang, PUBG akkauntingizga o'tkazishingiz mumkin!"
    )

    if hasattr(update, 'message') and update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


# ===================== CALLBACK HANDLER =====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = user.id
    user_data = get_user(user_id)

    # Obuna tekshirish
    if query.data == "check_sub":
        is_subscribed = await check_subscription(user_id, context.bot)
        if is_subscribed:
            await query.edit_message_text("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.")
            await show_main_menu(update, user)
        else:
            await query.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)
        return

    # Kanal obunasini tekshirish
    is_subscribed = await check_subscription(user_id, context.bot)
    if not is_subscribed:
        await query.answer("❌ Avval kanalga obuna bo'ling!", show_alert=True)
        return

    # ===== SPIN =====
    if query.data == "spin":
        if not can_spin(user_data):
            await query.answer(
                "❌ Bugungi aylantirish tugadi!\n"
                "Do'st taklif qiling va qo'shimcha aylantirish oling!",
                show_alert=True
            )
            return

        # Aylantirish
        today = date.today().isoformat()
        uc_won = random.randint(1, 10)

        if user_data["last_spin"] != today:
            user_data["last_spin"] = today
        elif user_data["extra_spins"] > 0:
            user_data["extra_spins"] -= 1

        user_data["uc"] += uc_won

        # Animatsiya matni
        spin_animation = "🎡 Baraban aylanmoqda...\n\n"
        prizes = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        prize_display = " ".join(prizes)

        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🎡 Baraban aylanmoqda...\n\n"
            f"1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟\n\n"
            f"🎉 Tabriklaymiz! Siz **{uc_won} UC** yutib oldingiz!\n\n"
            f"💎 Umumiy balansingiz: **{user_data['uc']} UC**\n"
            f"🎡 Qo'shimcha aylantirish: {user_data['extra_spins']} ta",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    # ===== REFERRAL =====
    elif query.data == "referral":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        ref_count = len(user_data["referred_users"])

        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"👥 Do'st taklif qilish\n\n"
            f"Har bir do'stingiz botga qo'shilsa, siz 1 ta qo'shimcha aylantirish olasiz!\n\n"
            f"🔗 Sizning havolangiz:\n`{ref_link}`\n\n"
            f"👤 Taklif qilgan do'stlar: {ref_count} ta\n"
            f"🎡 Qo'shimcha aylantirish: {user_data['extra_spins']} ta",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    # ===== WITHDRAW =====
    elif query.data == "withdraw":
        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if user_data["uc"] < 60:
            needed = 60 - user_data["uc"]
            await query.edit_message_text(
                f"💰 UC Yechib olish\n\n"
                f"❌ Yechib olish uchun kamida **60 UC** kerak!\n\n"
                f"💎 Sizda: {user_data['uc']} UC\n"
                f"📊 Yana {needed} UC yig'ing!",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"💰 UC Yechib olish\n\n"
                f"💎 Sizda: {user_data['uc']} UC\n\n"
                f"📱 PUBG akkaunt ID ingizni yuboring:\n"
                f"(Faqat raqamlarni yuboring)",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            context.user_data["waiting_pubg_id"] = True

    # ===== PROFILE =====
    elif query.data == "profile":
        ref_count = len(user_data["referred_users"])
        today = date.today().isoformat()
        spins_left = 0
        if user_data["last_spin"] != today:
            spins_left = 1
        spins_left += user_data["extra_spins"]

        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📊 Mening profilim\n\n"
            f"👤 Ism: {user.first_name}\n"
            f"🆔 ID: {user_id}\n"
            f"💎 UC Balans: {user_data['uc']} UC\n"
            f"🎡 Qolgan aylantirish: {spins_left} ta\n"
            f"👥 Taklif qilingan do'stlar: {ref_count} ta\n"
            f"🎮 PUBG ID: {user_data['pubg_id'] or 'Kiritilmagan'}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    # ===== MENU =====
    elif query.data == "menu":
        await show_main_menu(update, user)


# ===================== PUBG ID QABUL QILISH =====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_data = get_user(user_id)
    text = update.message.text

    if context.user_data.get("waiting_pubg_id"):
        if text.isdigit():
            pubg_id = text
            user_data["pubg_id"] = pubg_id
            uc_amount = user_data["uc"]
            context.user_data["waiting_pubg_id"] = False

            # Foydalanuvchiga xabar
            await update.message.reply_text(
                f"✅ So'rovingiz qabul qilindi!\n\n"
                f"🎮 PUBG ID: {pubg_id}\n"
                f"💎 So'ralgan UC: {uc_amount} UC\n\n"
                f"⏳ Admin ko'rib chiqadi va tez orada UC yuboradi!"
            )

            # Adminga xabar
            await context.bot.send_message(
                ADMIN_ID,
                f"🔔 YANGI UC SO'ROVI!\n\n"
                f"👤 Foydalanuvchi: {user.first_name} (@{user.username or 'yoq'})\n"
                f"🆔 Telegram ID: {user_id}\n"
                f"🎮 PUBG ID: {pubg_id}\n"
                f"💎 UC miqdori: {uc_amount} UC\n\n"
                f"UC ni o'tkazgandan so'ng foydalanuvchi balansini nolga tushiring:\n"
                f"/reset {user_id}"
            )

            # Balansni nolga tushirish (admin tasdiqlashidan keyin)
            # Hozircha kutish holatida qoldiramiz
        else:
            await update.message.reply_text("❌ Faqat raqamlarni kiriting! PUBG ID raqamlardan iborat bo'ladi.")
        return


# ===================== ADMIN KOMANDALAR =====================

async def reset_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ Format: /reset [user_id]")
        return

    target_id = int(context.args[0])
    if target_id in users:
        users[target_id]["uc"] = 0
        await update.message.reply_text(f"✅ {target_id} foydalanuvchining balansi nolga tushirildi!")
        await context.bot.send_message(
            target_id,
            "✅ UC so'rovingiz bajarildi! PUBG akkauntingizni tekshiring.\n"
            "🎡 Yana UC yig'ishingiz mumkin!"
        )
    else:
        await update.message.reply_text("❌ Bunday foydalanuvchi topilmadi!")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    total_users = len(users)
    total_uc = sum(u["uc"] for u in users.values())

    await update.message.reply_text(
        f"📊 Bot statistikasi\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"💎 Jami yig'ilgan UC: {total_uc} UC"
    )


# ===================== MAIN =====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset_balance))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot ishga tushdi!")
    app.run_polling()


if __name__ == "__main__":
    main()
