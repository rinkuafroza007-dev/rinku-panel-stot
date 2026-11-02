import logging
import asyncio
import random
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from config import (
    BOT_TOKEN,
    STORE_NAME,
    CURRENCY,
    SUPPORT_USERNAME,
    BOT_USERNAME,
    ADMIN_IDS,
    USDT_TRC20_WALLET,
    USDT_BEP20_WALLET,
    USDT_TON_WALLET
)
import database as db
import keyboards as kb

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_store_name() -> str:
    return db.get_setting("store_name", STORE_NAME)

def get_support_username() -> str:
    return db.get_setting("support_username", SUPPORT_USERNAME)

def get_deposit_admin_username() -> str:
    return db.get_setting("deposit_admin_username", SUPPORT_USERNAME)

def get_welcome_text(user_name: str) -> str:
    store = get_store_name()
    return (
        f"🏪 — {store} — 🏪\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 Welcome, {user_name}!\n\n"
        f"⭐ — SHOP FEATURES — ⭐\n\n"
        f"├── 🔑 Premium Digital Products\n"
        f"├── ⚡ Instant Delivery 24/7\n"
        f"├── 🔒 100% Secure Payment\n"
        f"├── 💸 Best Prices Guaranteed\n"
        f"├── 🎁 Referral Rewards\n"
        f"└── 🏆 Professional Support\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🚀 Click Shop Now to Start!"
    )

def format_variants_text(product_name: str, variants: list) -> str:
    lines = [
        f"🛒 {product_name.upper()}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 STOCK & PRICING:\n"
    ]
    total = len(variants)
    for idx, v in enumerate(variants):
        is_last = (idx == total - 1)
        prefix = "└──" if is_last else "├──"
        indent = "    " if is_last else "│   "

        stock_line = "✅ In Stock" if v["in_stock"] > 0 else "❌ Out of Stock"

        lines.append(f"{prefix} ⏱️ {v['duration_name']}")
        lines.append(f"{indent}├── {stock_line}")
        lines.append(f"{indent}└── 💰 ${v['price']:.2f}\n")

    lines.append("━━━━━━━━━━━━━━━━━━━━\n")
    lines.append("🎯 SELECT YOUR PLAN:")
    return "\n".join(lines)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    referrer_id = None

    if args and len(args) > 0 and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0].replace("ref_", ""))
        except ValueError:
            referrer_id = None

    db.get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        referrer_id=referrer_id
    )

    text = get_welcome_text(user.first_name)
    user_is_admin = is_admin(user.id)
    reply_markup = kb.main_menu_keyboard(is_admin=user_is_admin)

    if update.callback_query:
        try:
            await update.callback_query.answer()
        except Exception:
            pass
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Access denied. Administrator only.")
        return

    store = get_store_name()
    text = (
        f"🛠️ — <b>{store} ADMIN DASHBOARD</b> — 🛠️\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome, Administrator <b>{user.first_name}</b>!\n"
        f"Choose an option below to manage your store:"
    )
    await update.message.reply_text(text=text, parse_mode="HTML", reply_markup=kb.admin_menu_keyboard())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    data = query.data
    user = update.effective_user

    db_user = db.get_or_create_user(user.id, user.username, user.first_name)
    user_is_admin = is_admin(user.id)
    store = get_store_name()

    # ------------------- CUSTOMER VIEWS -------------------

    if data == "nav_main":
        text = get_welcome_text(user.first_name)
        await query.edit_message_text(text=text, reply_markup=kb.main_menu_keyboard(is_admin=user_is_admin))

    elif data == "nav_shop":
        categories = db.get_categories()
        text = (
            f"🛒 — {store} CATALOG — 🛒\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Please choose a category below to browse available products:"
        )
        await query.edit_message_text(text=text, reply_markup=kb.categories_keyboard(categories))

    elif data.startswith("cat_"):
        cat_id = int(data.split("_")[1])
        category = db.get_category(cat_id)
        if not category:
            await query.edit_message_text("Category not found.", reply_markup=kb.back_to_main_keyboard())
            return

        products = db.get_products_by_category(cat_id)
        text = (
            f"{category['icon']} — {category['name'].upper()} — {category['icon']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Select a product below to view available duration plans & pricing:"
        )
        await query.edit_message_text(text=text, reply_markup=kb.products_keyboard(products, cat_id))

    elif data.startswith("prod_"):
        prod_id = int(data.split("_")[1])
        product = db.get_product(prod_id)
        if not product:
            await query.edit_message_text("Product not found.", reply_markup=kb.back_to_main_keyboard())
            return

        variants = db.get_product_variants_with_stock(prod_id)
        text = format_variants_text(product["name"], variants)
        await query.edit_message_text(
            text=text,
            reply_markup=kb.product_variants_keyboard(prod_id, product["category_id"], variants)
        )

    elif data.startswith("var_out_"):
        await query.answer("❌ Sorry, this duration plan is currently Out of Stock!", show_alert=True)

    elif data.startswith("varbuy_"):
        variant_id = int(data.split("_")[1])
        variant = db.get_variant(variant_id)
        if not variant:
            await query.edit_message_text("Variant not found.", reply_markup=kb.back_to_main_keyboard())
            return

        user_info = db.get_user(user.id)
        price = variant["price"]

        if user_info["balance"] < price:
            needed = price - user_info["balance"]
            text = (
                f"⚠️ — INSUFFICIENT BALANCE — ⚠️\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Item: {variant['product_name']} ({variant['duration_name']})\n"
                f"Price: ${price:.2f} {CURRENCY}\n"
                f"Your Balance: ${user_info['balance']:.2f} {CURRENCY}\n"
                f"Needed: ${needed:.2f} {CURRENCY}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Please top up your balance to complete this purchase."
            )
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Add Balance Now", callback_data="nav_balance")],
                [InlineKeyboardButton("« Back to Product", callback_data=f"prod_{variant['product_id']}")]
            ])
            await query.edit_message_text(text=text, reply_markup=markup)
            return

        text = (
            f"🛒 — CONFIRM ORDER — 🛒\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Item: {variant['product_name']} ({variant['duration_name']})\n"
            f"Price: ${price:.2f} {CURRENCY}\n"
            f"Your Balance After: ${user_info['balance'] - price:.2f} {CURRENCY}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Would you like to complete this purchase now?"
        )
        await query.edit_message_text(
            text=text,
            reply_markup=kb.confirm_buy_variant_keyboard(variant_id, variant["product_id"])
        )

    elif data.startswith("conf_varbuy_"):
        variant_id = int(data.split("_")[2])
        res = db.purchase_variant(user.id, variant_id)

        if not res["success"]:
            if res.get("error") == "INSUFFICIENT_BALANCE":
                await query.edit_message_text(
                    "❌ Insufficient balance! Please top up.",
                    reply_markup=kb.back_to_main_keyboard()
                )
            elif res.get("error") == "OUT_OF_STOCK":
                await query.edit_message_text(
                    "❌ Sorry, this item duration just went out of stock!",
                    reply_markup=kb.back_to_main_keyboard()
                )
            else:
                await query.edit_message_text(
                    f"❌ An error occurred: {res.get('error')}",
                    reply_markup=kb.back_to_main_keyboard()
                )
            return

        text = (
            f"🎉 — PURCHASE SUCCESSFUL — 🎉\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 Order ID: #{res['order_id']}\n"
            f"📦 Product: {res['product_name']} ({res['duration_name']})\n"
            f"💰 Paid: ${res['price']:.2f} {CURRENCY}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 Your Item / License Data:\n"
            f"<code>{res['item_content']}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Thank you for shopping with {store}!\n"
            f"This order has been saved to your 'My Orders'."
        )
        await query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=kb.back_to_main_keyboard()
        )

    elif data == "nav_profile":
        user_info = db.get_user(user.id)
        ref_stats = db.get_referral_stats(user.id)
        text = (
            f"👤 — USER PROFILE — 👤\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 User ID: <code>{user.id}</code>\n"
            f"📛 Name: {user.first_name}\n"
            f"💰 Balance: <b>${user_info['balance']:.2f} {CURRENCY}</b>\n"
            f"🛍️ Total Orders: {user_info['orders_count']}\n"
            f"💸 Total Spent: ${user_info['total_spent']:.2f} {CURRENCY}\n"
            f"🎁 Referral Earnings: ${ref_stats['earnings']:.2f} {CURRENCY}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.profile_keyboard())

    elif data == "nav_orders":
        orders = db.get_user_orders(user.id, limit=5)
        if not orders:
            text = (
                f"📦 — YOUR ORDERS — 📦\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"You haven't placed any orders yet!\n\n"
                f"Check out our shop catalog to get started."
            )
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🛍️ Shop Now", callback_data="nav_shop")],
                [InlineKeyboardButton("« Back to Main Menu", callback_data="nav_main")]
            ])
            await query.edit_message_text(text=text, reply_markup=markup)
            return

        text = f"📦 — RECENT ORDERS ({len(orders)}) — 📦\n━━━━━━━━━━━━━━━━━━━━\n"
        for o in orders:
            text += (
                f"🆔 <b>Order #{o['id']}</b> ({o['created_at'][:16]})\n"
                f"• Item: {o['product_name']} ({o['duration_name']})\n"
                f"• Cost: ${o['price']:.2f} {CURRENCY}\n"
                f"• Delivered Data: <code>{o['item_content']}</code>\n"
                f"────────────────────\n"
            )

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛍️ Shop More", callback_data="nav_shop")],
            [InlineKeyboardButton("« Back to Main Menu", callback_data="nav_main")]
        ])
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=markup)

    elif data == "nav_balance":
        user_info = db.get_user(user.id)
        deposit_admin = get_deposit_admin_username()
        text = (
            f"💳 — <b>ADD BALANCE</b> — 💳\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Your Current Balance: <b>${user_info['balance']:.2f} {CURRENCY}</b>\n"
            f"🆔 Your Telegram ID: <code>{user.id}</code>\n\n"
            f"To top up your account balance, please contact our administrator directly:\n\n"
            f"👤 <b>Administrator:</b> @{deposit_admin}\n\n"
            f"💡 <i>Send your User ID (<code>{user.id}</code>) along with your payment screenshot to get credited immediately!</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.add_balance_keyboard(deposit_admin))

    elif data == "nav_referral":
        user_info = db.get_user(user.id)
        ref_stats = db.get_referral_stats(user.id)
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.id}"

        text = (
            f"🎁 — REFERRAL PROGRAM — 🎁\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Invite friends to {store} and earn commissions on every order they make!\n\n"
            f"🔗 <b>Your Exclusive Referral Link:</b>\n"
            f"<code>{ref_link}</code>\n\n"
            f"👥 Total Invited: <b>{ref_stats['count']} users</b>\n"
            f"💵 Total Earned: <b>${ref_stats['earnings']:.2f} {CURRENCY}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Click the button below to share with your friends:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.referral_keyboard(user.id, store))

    elif data == "nav_spin":
        can_spin, wait_secs = db.can_user_spin(user.id)
        if can_spin:
            status_text = "🟢 <b>Available!</b> You have 1 free spin ready."
        else:
            hours = wait_secs // 3600
            minutes = (wait_secs % 3600) // 60
            status_text = f"⏳ Cooldown active. Next spin in: <b>{hours}h {minutes}m</b>"

        text = (
            f"🎰 — DAILY LUCKY WHEEL — 🎰\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Try your luck daily and win free {CURRENCY} balance!\n\n"
            f"🎁 Possible Rewards: $0.10 to $1.00\n"
            f"⏱️ Free Spin: Once every 24 Hours\n\n"
            f"Status: {status_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.lucky_spin_keyboard(can_spin))

    elif data == "spin_wheel":
        can_spin, wait_secs = db.can_user_spin(user.id)
        if not can_spin:
            await query.answer("⏳ Please wait for your next daily spin!", show_alert=True)
            return

        rewards = [0.10, 0.20, 0.30, 0.50, 1.00]
        weights = [45, 30, 15, 8, 2]
        won_reward = random.choices(rewards, weights=weights)[0]

        db.record_spin_reward(user.id, won_reward)
        user_info = db.get_user(user.id)

        text = (
            f"🎉 — LUCKY SPIN RESULT — 🎉\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎰 Wheel Result: [ 💎 ${won_reward:.2f} {CURRENCY} 💎 ]\n\n"
            f"Congratulations! You won <b>+${won_reward:.2f} {CURRENCY}</b>!\n"
            f"New Balance: <b>${user_info['balance']:.2f} {CURRENCY}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Come back in 24 hours for another free spin!"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.back_to_main_keyboard())

    elif data == "nav_support":
        supp_admin = get_support_username()
        text = (
            f"🎫 — <b>SUPPORT CENTER</b> — 🎫\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Need assistance with an order, replacement, or account top-up?\n"
            f"Our administrator is available 24/7 to assist you!\n\n"
            f"💬 <b>Official Admin:</b> @{supp_admin}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Click the button below to message directly:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.support_keyboard(supp_admin))

    elif data == "nav_about":
        text = (
            f"ℹ️ — ABOUT {store} — ℹ️\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Welcome to <b>{store}</b>, your #1 automated platform for digital products, keys, and subscriptions.\n\n"
            f"⚡ <b>Instant Delivery:</b> Items delivered automatically 24/7.\n"
            f"🔒 <b>Secure:</b> Protected transactions with {CURRENCY} cryptocurrency.\n"
            f"💎 <b>100% Quality:</b> Genuine keys & verified accounts.\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Thank you for choosing us!"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.back_to_main_keyboard())

    # ------------------- ADMIN CONTROLS -------------------

    elif data == "nav_admin":
        if not user_is_admin:
            await query.answer("⛔ Access denied.", show_alert=True)
            return

        text = (
            f"🛠️ — <b>{store} ADMIN DASHBOARD</b> — 🛠️\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Welcome, Administrator <b>{user.first_name}</b>!\n"
            f"Select a management tool below:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_menu_keyboard())

    elif data == "adm_stats":
        if not user_is_admin:
            return
        stats = db.get_admin_stats()
        text = (
            f"📊 — <b>STORE ANALYTICS & STATS</b> — 📊\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Total Users:</b> {stats['total_users']}\n"
            f"📦 <b>Active Products:</b> {stats['total_products']}\n"
            f"🔑 <b>Available Stock Items:</b> {stats['total_stock']}\n"
            f"🛍️ <b>Orders Completed:</b> {stats['total_orders']}\n"
            f"💰 <b>Total Revenue:</b> ${stats['total_revenue']:.2f} {CURRENCY}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    # --- STORE SETTINGS (NAME, SUPPORT, DEPOSIT) ---
    elif data == "adm_settings":
        if not user_is_admin:
            return
        st_name = get_store_name()
        sp_user = get_support_username()
        dp_user = get_deposit_admin_username()
        text = (
            f"⚙️ — <b>STORE SETTINGS & CUSTOMIZATION</b> — ⚙️\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ <b>Store Name:</b> {st_name}\n"
            f"💬 <b>Support Admin:</b> @{sp_user}\n"
            f"💳 <b>Add Balance Admin:</b> @{dp_user}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Select what you would like to customize:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_settings_keyboard())

    elif data == "adm_set_store_name":
        if not user_is_admin:
            return
        context.user_data["admin_state"] = {"action": "change_store_name"}
        text = (
            f"🏷️ — <b>CHANGE STORE NAME</b> — 🏷️\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Current Name: <b>{get_store_name()}</b>\n\n"
            f"Please send the new store name in your next message:\n"
            f"(Example: <code>ACI STORE</code> or <code>RINKU PANEL STORE</code>)"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    elif data == "adm_set_support_user":
        if not user_is_admin:
            return
        context.user_data["admin_state"] = {"action": "change_support_username"}
        text = (
            f"💬 — <b>CHANGE SUPPORT ADMIN USERNAME</b> — 💬\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Current Support: <b>@{get_support_username()}</b>\n\n"
            f"Please send the new Telegram username for Support Center:\n"
            f"(Example: <code>all_iosx</code>)"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    elif data == "adm_set_deposit_user":
        if not user_is_admin:
            return
        context.user_data["admin_state"] = {"action": "change_deposit_username"}
        text = (
            f"💳 — <b>CHANGE ADD BALANCE ADMIN USERNAME</b> — 💳\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Current Deposit Admin: <b>@{get_deposit_admin_username()}</b>\n\n"
            f"Please send the new Telegram username for Add Balance inquiries:\n"
            f"(Example: <code>all_iosx</code>)"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    # --- CATEGORY & PRODUCT MANAGEMENT FLOW ---
    elif data == "adm_cats":
        if not user_is_admin:
            return
        cats = db.get_categories()
        text = (
            f"📁 — <b>CATEGORIES & PRODUCTS</b> — 📁\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Click on a category below to view, add, or manage products:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_categories_keyboard(cats))

    elif data.startswith("adm_cat_view_"):
        if not user_is_admin:
            return
        cat_id = int(data.split("_")[3])
        cat = db.get_category(cat_id)
        if not cat:
            await query.edit_message_text("Category not found.", reply_markup=kb.admin_back_keyboard())
            return

        products = db.get_products_by_category(cat_id)
        text = (
            f"{cat['icon']} — <b>CATEGORY: {cat['name'].upper()}</b> — {cat['icon']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Total Products in this Category: <b>{len(products)}</b>\n\n"
            f"Click <b>➕ Add Product</b> to create a new product here:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_category_detail_keyboard(cat_id, products))

    elif data.startswith("adm_del_cat_"):
        if not user_is_admin:
            return
        cat_id = int(data.split("_")[3])
        db.delete_category(cat_id)
        await query.answer("🗑️ Category deleted successfully!", show_alert=True)
        cats = db.get_categories()
        await query.edit_message_text("📁 Updated Categories:", reply_markup=kb.admin_categories_keyboard(cats))

    elif data == "adm_new_cat":
        if not user_is_admin:
            return
        context.user_data["admin_state"] = {"action": "new_cat"}
        text = (
            f"📁 — <b>CREATE NEW CATEGORY</b> — 📁\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Please send the icon and category name.\n\n"
            f"Example:\n"
            f"<code>🍎 iPhone (iOS)</code>"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    # --- STEP 1: ADD PRODUCT (ENTER NAME) ---
    elif data.startswith("adm_start_add_prod_"):
        if not user_is_admin:
            return
        cat_id = int(data.split("_")[4])
        cat = db.get_category(cat_id)
        context.user_data["admin_state"] = {"action": "create_prod_name", "cat_id": cat_id}
        text = (
            f"➕ — <b>ADD PRODUCT: STEP 1 (ENTER NAME)</b> — ➕\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 Category: <b>{cat['icon']} {cat['name']}</b>\n\n"
            f"📝 Please enter the <b>Product Name</b>:\n"
            f"(Example: <code>EXTERNAL PROXY</code>)"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    # --- STEP 2: TOGGLE VARIANTS (1 DAY, 7 DAYS, 1 MONTH) ---
    elif data in ["toggle_var_1d", "toggle_var_7d", "toggle_var_1m"]:
        if not user_is_admin:
            return
        state = context.user_data.get("admin_state", {})
        if state.get("action") != "select_variants":
            return

        selected = state.get("selected_variants", set())
        var_map = {
            "toggle_var_1d": "1 Day",
            "toggle_var_7d": "7 Days",
            "toggle_var_1m": "1 Month"
        }
        var_name = var_map[data]
        if var_name in selected:
            selected.remove(var_name)
        else:
            selected.add(var_name)

        state["selected_variants"] = selected
        context.user_data["admin_state"] = state

        text = (
            f"➕ — <b>ADD PRODUCT: STEP 2 (SELECT VARIANTS)</b> — ➕\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 Product Name: <b>{state['prod_name']}</b>\n\n"
            f"Please select the duration variants for this product.\n"
            f"(You can toggle 1, 2, or all 3):\n\n"
            f"When finished, click <b>'➡️ Next (Enter Prices)'</b>."
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_variant_toggle_keyboard(selected))

    # --- STEP 3: FINISH VARIANT SELECTION -> PROMPT FOR PRICES ---
    elif data == "finish_var_selection":
        if not user_is_admin:
            return
        state = context.user_data.get("admin_state", {})
        selected = state.get("selected_variants", set())
        if not selected:
            await query.answer("⚠️ Please select at least one duration variant!", show_alert=True)
            return

        order = ["1 Day", "7 Days", "1 Month"]
        sorted_variants = [v for v in order if v in selected]

        first_var = sorted_variants[0]
        context.user_data["admin_state"] = {
            "action": "entering_prices",
            "cat_id": state["cat_id"],
            "prod_name": state["prod_name"],
            "variants_queue": sorted_variants,
            "current_idx": 0,
            "collected_prices": []
        }

        text = (
            f"💰 — <b>ADD PRODUCT: STEP 3 (ENTER PRICES)</b> — 💰\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 Product: <b>{state['prod_name']}</b>\n\n"
            f"⏱️ What is the price for <b>{first_var}</b>? (USD)\n"
            f"Please send a number (Example: <code>0.30</code>):"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    # --- VIEW PRODUCT DETAILS IN ADMIN ---
    elif data.startswith("adm_prod_view_"):
        if not user_is_admin:
            return
        prod_id = int(data.split("_")[3])
        product = db.get_product(prod_id)
        if not product:
            await query.edit_message_text("Product not found.", reply_markup=kb.admin_back_keyboard())
            return

        variants = db.get_product_variants_with_stock(prod_id)
        var_lines = "\n".join([f"• ⏱️ {v['duration_name']}: ${v['price']:.2f} (Stock: {v['in_stock']})" for v in variants])

        text = (
            f"📦 — <b>{product['name']}</b> — 📦\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 Category: {product['category_name']}\n\n"
            f"📊 <b>Active Duration Plans:</b>\n{var_lines}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_product_detail_keyboard(prod_id, product["category_id"]))

    elif data.startswith("adm_del_prod_"):
        if not user_is_admin:
            return
        prod_id = int(data.split("_")[3])
        product = db.get_product(prod_id)
        cat_id = product["category_id"] if product else None
        db.delete_product(prod_id)
        await query.answer("🗑️ Product deleted successfully!", show_alert=True)
        if cat_id:
            products = db.get_products_by_category(cat_id)
            await query.edit_message_text("📦 Updated Product List:", reply_markup=kb.admin_category_detail_keyboard(cat_id, products))
        else:
            cats = db.get_categories()
            await query.edit_message_text("📁 Categories:", reply_markup=kb.admin_categories_keyboard(cats))

    # --- STOCK MANAGEMENT (ADD / REMOVE / VIEW) ---
    elif data == "adm_stock_cats":
        if not user_is_admin:
            return
        cats = db.get_categories()
        text = (
            f"📦 — <b>MANAGE STOCK: STEP 1 (SELECT CATEGORY)</b> — 📦\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Please select the category of the product to manage stock:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_stock_categories_keyboard(cats))

    elif data.startswith("adm_stock_cat_"):
        if not user_is_admin:
            return
        cat_id = int(data.split("_")[3])
        cat = db.get_category(cat_id)
        products = db.get_products_by_category(cat_id)
        text = (
            f"📦 — <b>MANAGE STOCK: STEP 2 (SELECT PRODUCT)</b> — 📦\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 Category: <b>{cat['icon']} {cat['name']}</b>\n\n"
            f"Select a product:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_stock_products_keyboard(products, cat_id))

    elif data.startswith("adm_stock_prod_"):
        if not user_is_admin:
            return
        prod_id = int(data.split("_")[3])
        product = db.get_product(prod_id)
        variants = db.get_product_variants_with_stock(prod_id)
        text = (
            f"📦 — <b>MANAGE STOCK: STEP 3 (SELECT PLAN)</b> — 📦\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛒 Product: <b>{product['name']}</b>\n\n"
            f"Select a duration plan to Add or Remove stock:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_stock_variants_keyboard(variants, prod_id))

    elif data.startswith("adm_var_stock_menu_"):
        if not user_is_admin:
            return
        var_id = int(data.split("_")[4])
        variant = db.get_variant(var_id)
        if not variant:
            await query.edit_message_text("Variant not found.", reply_markup=kb.admin_back_keyboard())
            return

        text = (
            f"📦 — <b>STOCK CONTROLS: {variant['product_name']} ({variant['duration_name']})</b> — 📦\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛒 Product: <b>{variant['product_name']}</b>\n"
            f"⏱️ Plan Duration: <b>{variant['duration_name']}</b>\n"
            f"💵 Price: <b>${variant['price']:.2f} {CURRENCY}</b>\n"
            f"📊 Current In-Stock: <b>{variant['in_stock']} items</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Choose an action below:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_variant_stock_actions_keyboard(var_id, variant["product_id"]))

    elif data.startswith("adm_add_keys_"):
        if not user_is_admin:
            return
        var_id = int(data.split("_")[3])
        variant = db.get_variant(var_id)
        if not variant:
            await query.edit_message_text("Variant not found.", reply_markup=kb.admin_back_keyboard())
            return

        context.user_data["admin_state"] = {"action": "add_stock", "prod_id": variant["product_id"], "var_id": var_id}
        text = (
            f"📥 — <b>PASTE STOCK KEYS</b> — 📥\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛒 Product: <b>{variant['product_name']}</b>\n"
            f"⏱️ Plan: <b>{variant['duration_name']}</b>\n"
            f"📊 Current Stock: <b>{variant['in_stock']} items</b>\n\n"
            f"Please send your digital keys/accounts in your next message.\n"
            f"💡 <b>Multiple items:</b> Put 1 key per line.\n\n"
            f"Example:\n"
            f"<code>KEY-AAA-111\nKEY-BBB-222\nKEY-CCC-333</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    elif data.startswith("adm_clear_stock_"):
        if not user_is_admin:
            return
        var_id = int(data.split("_")[3])
        variant = db.get_variant(var_id)
        if not variant:
            return

        deleted_count = db.clear_variant_stock(var_id)
        await query.answer(f"🗑️ Cleared {deleted_count} unsold keys from stock!", show_alert=True)

        updated_variant = db.get_variant(var_id)
        text = (
            f"📦 — <b>STOCK CONTROLS: {updated_variant['product_name']} ({updated_variant['duration_name']})</b> — 📦\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛒 Product: <b>{updated_variant['product_name']}</b>\n"
            f"⏱️ Plan Duration: <b>{updated_variant['duration_name']}</b>\n"
            f"💵 Price: <b>${updated_variant['price']:.2f} {CURRENCY}</b>\n"
            f"📊 Current In-Stock: <b>{updated_variant['in_stock']} items</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Cleared <b>{deleted_count}</b> unsold keys.\n"
            f"Choose an action below:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_variant_stock_actions_keyboard(var_id, updated_variant["product_id"]))

    elif data.startswith("adm_view_keys_"):
        if not user_is_admin:
            return
        var_id = int(data.split("_")[3])
        variant = db.get_variant(var_id)
        unsold_keys = db.get_variant_unsold_stock(var_id)

        if not unsold_keys:
            key_list_str = "No unsold keys available in stock."
        else:
            key_list_str = "\n".join([f"• <code>{k['item_content']}</code>" for k in unsold_keys])

        text = (
            f"📋 — <b>AVAILABLE KEYS ({len(unsold_keys)})</b> — 📋\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Product: <b>{variant['product_name']} ({variant['duration_name']})</b>\n\n"
            f"{key_list_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("« Back to Stock Controls", callback_data=f"adm_var_stock_menu_{var_id}")]
        ])
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=markup)

    # --- USER BALANCE MANAGEMENT FLOW ---
    elif data == "adm_balance_flow":
        if not user_is_admin:
            return
        context.user_data["admin_state"] = {"action": "awaiting_user_id_for_balance"}
        text = (
            f"💰 — <b>USER BALANCE MANAGEMENT</b> — 💰\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Please enter the customer's <b>Telegram User ID</b>:\n\n"
            f"<i>(Customers can find their User ID in their Profile)</i>"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    elif data.startswith("adm_bal_add_"):
        if not user_is_admin:
            return
        target_uid = int(data.split("_")[3])
        context.user_data["admin_state"] = {"action": "enter_add_balance_amount", "target_uid": target_uid}
        text = (
            f"➕ — <b>ADD BALANCE</b> — ➕\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Target User ID: <code>{target_uid}</code>\n\n"
            f"How much {CURRENCY} balance would you like to <b>ADD</b>?\n"
            f"Please enter the amount (Example: <code>10.00</code>):"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    elif data.startswith("adm_bal_dec_"):
        if not user_is_admin:
            return
        target_uid = int(data.split("_")[3])
        context.user_data["admin_state"] = {"action": "enter_dec_balance_amount", "target_uid": target_uid}
        text = (
            f"➖ — <b>DECLINE / DEDUCT BALANCE</b> — ➖\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Target User ID: <code>{target_uid}</code>\n\n"
            f"How much {CURRENCY} balance would you like to <b>DEDUCT</b>?\n"
            f"Please enter the amount (Example: <code>5.00</code>):"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

    elif data == "adm_broadcast_prompt":
        if not user_is_admin:
            return
        context.user_data["admin_state"] = {"action": "broadcast"}
        text = (
            f"📢 — <b>BROADCAST ANNOUNCEMENT</b> — 📢\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"You can send <b>ANY</b> type of content to broadcast:\n\n"
            f"• 💬 Text Message\n"
            f"• 📸 Photo (with caption)\n"
            f"• 🎥 Video (with caption)\n"
            f"• 📁 Document or File\n"
            f"• 🔄 <b>Forward directly from your Channel!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Send or forward your broadcast post now:"
        )
        await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

# --- ADMIN TEXT & MEDIA INPUT HANDLER ---
async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return

    state = context.user_data.get("admin_state")
    if not state:
        return

    action = state.get("action")

    # Broadcast handles ALL message types (text, photo, video, document, forwarded channel posts, audio, etc.)
    if action == "broadcast":
        context.user_data["admin_state"] = None
        all_users = db.get_all_users()
        sent = 0
        failed = 0
        status_msg = await update.message.reply_text(f"⏳ Broadcasting message to {len(all_users)} registered users...")

        from_chat_id = update.effective_chat.id
        msg_id = update.message.message_id

        for u in all_users:
            uid = u["user_id"]
            delivered = False
            # Try copy_message first
            try:
                await context.bot.copy_message(
                    chat_id=uid,
                    from_chat_id=from_chat_id,
                    message_id=msg_id
                )
                sent += 1
                delivered = True
                logger.info(f"[Broadcast] Successfully copied to {uid}")
            except Exception as e:
                logger.warning(f"[Broadcast] copy_message failed for {uid} ({e}), trying forward_message fallback...")
                try:
                    await context.bot.forward_message(
                        chat_id=uid,
                        from_chat_id=from_chat_id,
                        message_id=msg_id
                    )
                    sent += 1
                    delivered = True
                    logger.info(f"[Broadcast] Successfully forwarded to {uid}")
                except Exception as e2:
                    failed += 1
                    logger.error(f"[Broadcast] Failed to send to {uid}: {e2}")

            await asyncio.sleep(0.05)

        await status_msg.edit_text(
            f"✅ <b>Broadcast Complete!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Total Target Users: <b>{len(all_users)}</b>\n"
            f"📤 Successfully Delivered: <b>{sent} users</b>\n"
            f"⚠️ Failed/Blocked: <b>{failed} users</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML",
            reply_markup=kb.admin_back_keyboard()
        )
        return

    text = (update.message.text or update.message.caption or "").strip()
    if not text:
        return

    # Dynamic Settings Changes
    if action == "change_store_name":
        context.user_data["admin_state"] = None
        db.set_setting("store_name", text)
        await update.message.reply_text(
            f"✅ <b>Store Name Successfully Updated!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"New Store Name: <b>{text}</b>\n"
            f"This is now visible across the entire bot in real-time.",
            parse_mode="HTML",
            reply_markup=kb.admin_back_keyboard()
        )

    elif action == "change_support_username":
        context.user_data["admin_state"] = None
        clean_user = text.replace("@", "").strip()
        db.set_setting("support_username", clean_user)
        await update.message.reply_text(
            f"✅ <b>Support Admin Successfully Updated!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"New Support Username: <b>@{clean_user}</b>\n"
            f"The Support Center button now connects directly to @{clean_user}.",
            parse_mode="HTML",
            reply_markup=kb.admin_back_keyboard()
        )

    elif action == "change_deposit_username":
        context.user_data["admin_state"] = None
        clean_user = text.replace("@", "").strip()
        db.set_setting("deposit_admin_username", clean_user)
        await update.message.reply_text(
            f"✅ <b>Add Balance Admin Successfully Updated!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"New Deposit Admin: <b>@{clean_user}</b>\n"
            f"The Add Balance screen now directs customers to @{clean_user}.",
            parse_mode="HTML",
            reply_markup=kb.admin_back_keyboard()
        )

    # Product Name Entered
    elif action == "create_prod_name":
        prod_name = text
        cat_id = state.get("cat_id")
        context.user_data["admin_state"] = {
            "action": "select_variants",
            "cat_id": cat_id,
            "prod_name": prod_name,
            "selected_variants": set()
        }

        reply_text = (
            f"➕ — <b>ADD PRODUCT: STEP 2 (SELECT VARIANTS)</b> — ➕\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 Product Name: <b>{prod_name}</b>\n\n"
            f"Please select the duration variants for this product.\n"
            f"(You can toggle 1, 2, or all 3):\n\n"
            f"When finished, click <b>'➡️ Next (Enter Prices)'</b>."
        )
        await update.message.reply_text(
            text=reply_text,
            parse_mode="HTML",
            reply_markup=kb.admin_variant_toggle_keyboard(set())
        )

    # Entering Prices Step-by-Step
    elif action == "entering_prices":
        try:
            price = float(text)
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number for price (e.g., 0.30):")
            return

        queue = state["variants_queue"]
        idx = state["current_idx"]
        current_var = queue[idx]
        state["collected_prices"].append((current_var, price))
        state["current_idx"] += 1

        if state["current_idx"] < len(queue):
            next_var = queue[state["current_idx"]]
            context.user_data["admin_state"] = state
            await update.message.reply_text(
                f"✅ Saved price for {current_var}: ${price:.2f}\n\n"
                f"💰 Now, what is the price for ⏱️ <b>{next_var}</b> in USD?\n"
                f"Enter a number (Example: <code>0.70</code>):",
                parse_mode="HTML"
            )
        else:
            cat_id = state["cat_id"]
            prod_name = state["prod_name"]
            variants_list = state["collected_prices"]

            prod_id = db.add_product_with_custom_variants(
                category_id=cat_id,
                name=prod_name,
                description="Instant automated delivery digital product.",
                variants_list=variants_list
            )

            context.user_data["admin_state"] = None
            summary = "\n".join([f"• ⏱️ {v}: ${p:.2f}" for v, p in variants_list])

            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Manage Stock Now", callback_data=f"adm_stock_prod_{prod_id}")],
                [InlineKeyboardButton("« Back to Categories", callback_data="adm_cats")]
            ])

            await update.message.reply_text(
                f"🎉 <b>Product Successfully Created!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🛒 Product: <b>{prod_name}</b>\n"
                f"📊 Duration Plans & Prices:\n{summary}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"You can now add stock to this product:",
                parse_mode="HTML",
                reply_markup=markup
            )

    # Add Stock Keys
    elif action == "add_stock":
        prod_id = state.get("prod_id")
        var_id = state.get("var_id")
        variant = db.get_variant(var_id)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        added = db.add_stock_bulk(prod_id, var_id, lines)
        context.user_data["admin_state"] = None

        new_variant = db.get_variant(var_id)
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Stock Controls", callback_data=f"adm_var_stock_menu_{var_id}")],
            [InlineKeyboardButton("« Admin Dashboard", callback_data="nav_admin")]
        ])
        await update.message.reply_text(
            f"✅ <b>Successfully added {added} keys to stock!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛒 Product: <b>{variant['product_name']}</b>\n"
            f"⏱️ Plan: <b>{variant['duration_name']}</b>\n"
            f"📊 Total Current In-Stock: <b>{new_variant['in_stock']} items</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML",
            reply_markup=markup
        )

    # User Balance: Enter User ID
    elif action == "awaiting_user_id_for_balance":
        try:
            target_uid = int(text)
        except ValueError:
            await update.message.reply_text("❌ Invalid ID format. Please enter numbers only (e.g., 8198898522):")
            return

        target_user = db.get_user(target_uid)
        if not target_user:
            await update.message.reply_text(
                f"❌ User ID <code>{target_uid}</code> was not found in the database!\n"
                f"Please tell the user to send /start to the bot first.",
                parse_mode="HTML",
                reply_markup=kb.admin_back_keyboard()
            )
            return

        context.user_data["admin_state"] = None
        user_name = target_user["first_name"] or "Unknown"
        username_str = f"@{target_user['username']}" if target_user["username"] else "No username"

        text_msg = (
            f"👤 — <b>CLIENT FOUND</b> — 👤\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 Name: <b>{user_name}</b> ({username_str})\n"
            f"🆔 User ID: <code>{target_uid}</code>\n"
            f"💰 Current Balance: <b>${target_user['balance']:.2f} {CURRENCY}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Would you like to Add Balance or Decline / Deduct Balance?"
        )
        await update.message.reply_text(
            text=text_msg,
            parse_mode="HTML",
            reply_markup=kb.admin_user_balance_action_keyboard(target_uid)
        )

    # User Balance: Add Amount
    elif action == "enter_add_balance_amount":
        target_uid = state["target_uid"]
        try:
            amount = float(text)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid positive number (e.g., 10.00):")
            return

        db.update_user_balance(target_uid, amount)
        user_info = db.get_user(target_uid)
        bal = user_info['balance'] if user_info else 0.0
        context.user_data["admin_state"] = None

        await update.message.reply_text(
            f"✅ <b>Balance Added Successfully!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 User ID: <code>{target_uid}</code>\n"
            f"➕ Added: <b>+${amount:.2f} {CURRENCY}</b>\n"
            f"💰 New Balance: <b>${bal:.2f} {CURRENCY}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML",
            reply_markup=kb.admin_back_keyboard()
        )

        # Notify customer
        try:
            store = get_store_name()
            await context.bot.send_message(
                chat_id=target_uid,
                text=(
                    f"💳 — <b>BALANCE CREDITED</b> — 💳\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Your account has been credited with: <b>+${amount:.2f} {CURRENCY}</b>!\n"
                    f"Current Balance: <b>${bal:.2f} {CURRENCY}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"Thank you for choosing {store}!"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

    # User Balance: Decline / Deduct Amount
    elif action == "enter_dec_balance_amount":
        target_uid = state["target_uid"]
        try:
            amount = float(text)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid positive number (e.g., 5.00):")
            return

        db.deduct_user_balance(target_uid, amount)
        user_info = db.get_user(target_uid)
        bal = user_info['balance'] if user_info else 0.0
        context.user_data["admin_state"] = None

        await update.message.reply_text(
            f"✅ <b>Balance Deducted Successfully!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 User ID: <code>{target_uid}</code>\n"
            f"➖ Deducted: <b>-${amount:.2f} {CURRENCY}</b>\n"
            f"💰 New Balance: <b>${bal:.2f} {CURRENCY}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            parse_mode="HTML",
            reply_markup=kb.admin_back_keyboard()
        )

        # Notify customer
        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=(
                    f"⚠️ — <b>BALANCE ADJUSTMENT</b> — ⚠️\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"An amount of <b>${amount:.2f} {CURRENCY}</b> has been deducted from your account.\n"
                    f"Current Balance: <b>${bal:.2f} {CURRENCY}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"If you have any questions, please contact support."
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

    # Add Category
    elif action == "new_cat":
        parts = text.split(" ", 1)
        icon = parts[0] if len(parts) > 1 else "📁"
        name = parts[1] if len(parts) > 1 else parts[0]
        cat_id = db.add_category(name, icon)
        context.user_data["admin_state"] = None
        await update.message.reply_text(
            f"✅ <b>Category Created:</b> {icon} {name} (ID: #{cat_id})",
            parse_mode="HTML",
            reply_markup=kb.admin_back_keyboard()
        )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Access denied.")
        return

    context.user_data["admin_state"] = {"action": "broadcast"}
    text = (
        f"📢 — <b>BROADCAST ANNOUNCEMENT</b> — 📢\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"You can send <b>ANY</b> type of content to broadcast:\n\n"
        f"• 💬 Text Message\n"
        f"• 📸 Photo (with caption)\n"
        f"• 🎥 Video (with caption)\n"
        f"• 📁 Document or File\n"
        f"• 🔄 <b>Forward directly from your Channel!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Send or forward your broadcast post now:"
    )
    await update.message.reply_text(text=text, parse_mode="HTML", reply_markup=kb.admin_back_keyboard())

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Rinku Panel Bot is active and running 24/7!")

    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.getenv("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        server.serve_forever()
    except Exception:
        pass

def main():
    db.init_db()

    # Start health check server for Render/Cloud 24/7 hosting
    threading.Thread(target=start_health_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_admin_text))

    print(f"[*] Bot @{BOT_USERNAME} is running in polling mode...")
    app.run_polling()

if __name__ == "__main__":
    main()
