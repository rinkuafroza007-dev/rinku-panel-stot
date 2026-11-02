from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import urllib.parse
from config import SUPPORT_USERNAME, CHANNEL_LINK, BOT_USERNAME

def main_menu_keyboard(is_admin: bool = False):
    keyboard = [
        [
            InlineKeyboardButton("🛍️ Shop Now", callback_data="nav_shop")
        ],
        [
            InlineKeyboardButton("📦 My Orders", callback_data="nav_orders"),
            InlineKeyboardButton("👤 Profile", callback_data="nav_profile")
        ],
        [
            InlineKeyboardButton("💰 Add Balance", callback_data="nav_balance"),
            InlineKeyboardButton("🎁 Referral", callback_data="nav_referral")
        ],
        [
            InlineKeyboardButton("🎰 Lucky Spin", callback_data="nav_spin")
        ],
        [
            InlineKeyboardButton("🎫 Support Center", callback_data="nav_support")
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="nav_about")
        ]
    ]
    if is_admin:
        keyboard.append([
            InlineKeyboardButton("🛠️ Admin Dashboard", callback_data="nav_admin")
        ])
    return InlineKeyboardMarkup(keyboard)

def categories_keyboard(categories):
    keyboard = []
    for cat in categories:
        keyboard.append([
            InlineKeyboardButton(f"{cat['icon']} {cat['name']}", callback_data=f"cat_{cat['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton("« Back to Main Menu", callback_data="nav_main")
    ])
    return InlineKeyboardMarkup(keyboard)

def products_keyboard(products, category_id):
    keyboard = []
    for prod in products:
        stock_text = f"({prod['total_stock']})" if prod['total_stock'] > 0 else "(Sold Out)"
        keyboard.append([
            InlineKeyboardButton(f"🛒 {prod['name']} {stock_text}", callback_data=f"prod_{prod['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton("« Back to Categories", callback_data="nav_shop"),
        InlineKeyboardButton("« Main Menu", callback_data="nav_main")
    ])
    return InlineKeyboardMarkup(keyboard)

def product_variants_keyboard(product_id, category_id, variants):
    keyboard = []
    for v in variants:
        if v["in_stock"] > 0:
            btn_text = f"🛒 Buy {v['duration_name']} - ${v['price']:.2f}"
            callback = f"varbuy_{v['id']}"
        else:
            btn_text = f"❌ {v['duration_name']} - ${v['price']:.2f} (Out of Stock)"
            callback = f"var_out_{v['id']}"

        keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])

    keyboard.append([
        InlineKeyboardButton("🔙 Back to Products", callback_data=f"cat_{category_id}")
    ])
    return InlineKeyboardMarkup(keyboard)

def confirm_buy_variant_keyboard(variant_id, product_id):
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm & Pay", callback_data=f"conf_varbuy_{variant_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"prod_{product_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def profile_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("💰 Add Balance", callback_data="nav_balance"),
            InlineKeyboardButton("📦 My Orders", callback_data="nav_orders")
        ],
        [
            InlineKeyboardButton("« Back to Main Menu", callback_data="nav_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def add_balance_keyboard(admin_username: str = "all_iosx"):
    keyboard = [
        [
            InlineKeyboardButton(f"💬 Contact Admin (@{admin_username})", url=f"https://t.me/{admin_username}")
        ],
        [
            InlineKeyboardButton("« Back to Main Menu", callback_data="nav_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def referral_keyboard(user_id, store_name: str = "RINKU PANEL STORE"):
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(ref_link)}&text={urllib.parse.quote(f'Instant digital goods 24/7 at {store_name}!')}"
    
    keyboard = [
        [
            InlineKeyboardButton("🚀 Share Referral Link", url=share_url)
        ],
        [
            InlineKeyboardButton("« Back to Main Menu", callback_data="nav_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def lucky_spin_keyboard(can_spin):
    keyboard = []
    if can_spin:
        keyboard.append([
            InlineKeyboardButton("🎰 Spin The Wheel Now!", callback_data="spin_wheel")
        ])
    keyboard.append([
        InlineKeyboardButton("« Back to Main Menu", callback_data="nav_main")
    ])
    return InlineKeyboardMarkup(keyboard)

def support_keyboard(support_username: str = "all_iosx"):
    keyboard = [
        [
            InlineKeyboardButton(f"💬 Contact Support (@{support_username})", url=f"https://t.me/{support_username}")
        ],
        [
            InlineKeyboardButton("« Back to Main Menu", callback_data="nav_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("« Back to Main Menu", callback_data="nav_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ----------------- ADMIN KEYBOARDS -----------------

def admin_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("📊 Store Analytics", callback_data="adm_stats"),
            InlineKeyboardButton("📦 Manage Stock", callback_data="adm_stock_cats")
        ],
        [
            InlineKeyboardButton("📁 Categories & Products", callback_data="adm_cats"),
            InlineKeyboardButton("💰 Add User Balance", callback_data="adm_balance_flow")
        ],
        [
            InlineKeyboardButton("⚙️ Store Settings", callback_data="adm_settings"),
            InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast_prompt")
        ],
        [
            InlineKeyboardButton("« Back to Customer View", callback_data="nav_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🏷️ Change Store Name", callback_data="adm_set_store_name")
        ],
        [
            InlineKeyboardButton("💬 Change Support Admin", callback_data="adm_set_support_user")
        ],
        [
            InlineKeyboardButton("💳 Change Deposit Admin", callback_data="adm_set_deposit_user")
        ],
        [
            InlineKeyboardButton("« Back to Admin Dashboard", callback_data="nav_admin")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Categories list for managing/adding products
def admin_categories_keyboard(categories):
    keyboard = []
    for cat in categories:
        keyboard.append([
            InlineKeyboardButton(f"{cat['icon']} {cat['name']}", callback_data=f"adm_cat_view_{cat['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton("➕ Create New Category", callback_data="adm_new_cat")
    ])
    keyboard.append([
        InlineKeyboardButton("« Back to Admin Dashboard", callback_data="nav_admin")
    ])
    return InlineKeyboardMarkup(keyboard)

# Inside a specific Category: View its products + Add Product button
def admin_category_detail_keyboard(cat_id, products):
    keyboard = []
    for p in products:
        keyboard.append([
            InlineKeyboardButton(f"🛒 {p['name']} [Stock: {p['total_stock']}]", callback_data=f"adm_prod_view_{p['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton("➕ Add Product", callback_data=f"adm_start_add_prod_{cat_id}")
    ])
    keyboard.append([
        InlineKeyboardButton("🗑️ Delete This Category", callback_data=f"adm_del_cat_{cat_id}")
    ])
    keyboard.append([
        InlineKeyboardButton("« Back to Categories", callback_data="adm_cats")
    ])
    return InlineKeyboardMarkup(keyboard)

# Variant selection toggles for creating product
def admin_variant_toggle_keyboard(selected_variants: set):
    v_1d = "✅ 1 Day" if "1 Day" in selected_variants else "◻️ 1 Day"
    v_7d = "✅ 7 Days" if "7 Days" in selected_variants else "◻️ 7 Days"
    v_1m = "✅ 1 Month" if "1 Month" in selected_variants else "◻️ 1 Month"

    keyboard = [
        [InlineKeyboardButton(v_1d, callback_data="toggle_var_1d")],
        [InlineKeyboardButton(v_7d, callback_data="toggle_var_7d")],
        [InlineKeyboardButton(v_1m, callback_data="toggle_var_1m")],
        [
            InlineKeyboardButton("➡️ Next (Enter Prices)", callback_data="finish_var_selection"),
            InlineKeyboardButton("❌ Cancel", callback_data="adm_cats")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_product_detail_keyboard(product_id, category_id):
    keyboard = [
        [
            InlineKeyboardButton("📦 Manage Stock for Plans", callback_data=f"adm_stock_prod_{product_id}"),
            InlineKeyboardButton("🗑️ Delete Product", callback_data=f"adm_del_prod_{product_id}")
        ],
        [
            InlineKeyboardButton("« Back to Products", callback_data=f"adm_cat_view_{category_id}"),
            InlineKeyboardButton("« Admin Dashboard", callback_data="nav_admin")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Add Stock: Step 1 Categories
def admin_stock_categories_keyboard(categories):
    keyboard = []
    for cat in categories:
        keyboard.append([
            InlineKeyboardButton(f"{cat['icon']} {cat['name']}", callback_data=f"adm_stock_cat_{cat['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton("« Back to Admin Dashboard", callback_data="nav_admin")
    ])
    return InlineKeyboardMarkup(keyboard)

# Add Stock: Step 2 Products in Category
def admin_stock_products_keyboard(products, cat_id):
    keyboard = []
    for p in products:
        keyboard.append([
            InlineKeyboardButton(f"🛒 {p['name']} [Stock: {p['total_stock']}]", callback_data=f"adm_stock_prod_{p['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton("« Back to Categories", callback_data="adm_stock_cats")
    ])
    return InlineKeyboardMarkup(keyboard)

# Add Stock: Step 3 Variants in Product
def admin_stock_variants_keyboard(variants, product_id):
    keyboard = []
    for v in variants:
        keyboard.append([
            InlineKeyboardButton(f"⏱️ {v['duration_name']} [Stock: {v['in_stock']}]", callback_data=f"adm_var_stock_menu_{v['id']}")
        ])
    keyboard.append([
        InlineKeyboardButton("« Back to Categories", callback_data="adm_stock_cats")
    ])
    return InlineKeyboardMarkup(keyboard)

# Variant Stock Actions: Add, Clear, View
def admin_variant_stock_actions_keyboard(var_id, prod_id):
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Keys to Stock", callback_data=f"adm_add_keys_{var_id}"),
            InlineKeyboardButton("🗑️ Clear Unsold Stock", callback_data=f"adm_clear_stock_{var_id}")
        ],
        [
            InlineKeyboardButton("📋 View In-Stock Keys", callback_data=f"adm_view_keys_{var_id}")
        ],
        [
            InlineKeyboardButton("« Back to Duration Plans", callback_data=f"adm_stock_prod_{prod_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# User balance action buttons (Add Balance or Decline Balance)
def admin_user_balance_action_keyboard(target_user_id):
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Balance", callback_data=f"adm_bal_add_{target_user_id}"),
            InlineKeyboardButton("➖ Decline Balance", callback_data=f"adm_bal_dec_{target_user_id}")
        ],
        [
            InlineKeyboardButton("« Cancel", callback_data="nav_admin")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_back_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("« Back to Admin Dashboard", callback_data="nav_admin")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
