import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        balance REAL DEFAULT 0.0,
        total_spent REAL DEFAULT 0.0,
        orders_count INTEGER DEFAULT 0,
        referred_by INTEGER DEFAULT NULL,
        ref_earnings REAL DEFAULT 0.0,
        last_spin_time TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        icon TEXT DEFAULT '📁'
    )
    """)

    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    """)

    # Product Variants (e.g. 1 Day, 7 Days, 1 Month)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        duration_name TEXT NOT NULL,
        price REAL NOT NULL,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    """)

    # Product stock items (assigned to specific variant)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        variant_id INTEGER NOT NULL,
        item_content TEXT NOT NULL,
        is_sold INTEGER DEFAULT 0,
        sold_to INTEGER DEFAULT NULL,
        sold_at TIMESTAMP DEFAULT NULL,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (variant_id) REFERENCES product_variants (id)
    )
    """)

    # Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        variant_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        duration_name TEXT NOT NULL,
        price REAL NOT NULL,
        item_content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Settings table (for dynamic store name, support username, deposit username)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    default_settings = [
        ("store_name", "RINKU PANEL STORE"),
        ("support_username", "all_iosx"),
        ("deposit_admin_username", "all_iosx")
    ]
    for k, v in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Seed initial demo categories and products if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM categories")
    if cursor.fetchone()["cnt"] == 0:
        seed_initial_data(cursor)

    conn.commit()
    conn.close()

def get_setting(key, default=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()

def get_all_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row["key"]: row["value"] for row in cursor.fetchall()}
    conn.close()
    return settings

def seed_initial_data(cursor):
    categories = [
        ("iPhone (iOS)", "🍎"),
        ("Android", "🤖"),
        ("External Proxy", "🌐"),
        ("PC Software", "💻"),
    ]

    for name, icon in categories:
        cursor.execute("INSERT INTO categories (name, icon) VALUES (?, ?)", (name, icon))

    # Sample Products with 1 Day, 7 Days, 1 Month variants & stock
    # (Category 1: iPhone)
    cursor.execute("INSERT INTO products (category_id, name, description) VALUES (?, ?, ?)",
                   (1, "EXTERNAL PROXY", "High speed low latency private proxy server for iOS devices."))
    prod1_id = cursor.lastrowid

    variants_data = [
        ("1 Day", 0.30, [
            "PROXY-IOS-1D-89F1-23B1",
            "PROXY-IOS-1D-44C9-88E2",
            "PROXY-IOS-1D-11A3-99D4"
        ]),
        ("7 Days", 0.70, [
            "PROXY-IOS-7D-55K2-77L1",
            "PROXY-IOS-7D-33M8-66P4"
        ]),
        ("1 Month", 1.50, [
            "PROXY-IOS-30D-99X1-00Y2",
            "PROXY-IOS-30D-88Z4-11W3",
            "PROXY-IOS-30D-77V5-22T6"
        ])
    ]

    for dur, price, stocks in variants_data:
        cursor.execute("INSERT INTO product_variants (product_id, duration_name, price) VALUES (?, ?, ?)",
                       (prod1_id, dur, price))
        var_id = cursor.lastrowid
        for s in stocks:
            cursor.execute("INSERT INTO product_stock (product_id, variant_id, item_content) VALUES (?, ?, ?)",
                           (prod1_id, var_id, s))

    # Another iPhone product
    cursor.execute("INSERT INTO products (category_id, name, description) VALUES (?, ?, ?)",
                   (1, "VIP ZERO RECOIL (iOS)", "Premium zero recoil & aim lock helper for iOS."))
    prod2_id = cursor.lastrowid
    for dur, price in [("1 Day", 0.50), ("7 Days", 1.20), ("1 Month", 2.50)]:
        cursor.execute("INSERT INTO product_variants (product_id, duration_name, price) VALUES (?, ?, ?)",
                       (prod2_id, dur, price))
        var_id = cursor.lastrowid
        cursor.execute("INSERT INTO product_stock (product_id, variant_id, item_content) VALUES (?, ?, ?)",
                       (prod2_id, var_id, f"VIP-IOS-{dur[:2]}-DEMO-KEY-8821"))

    # (Category 2: Android)
    cursor.execute("INSERT INTO products (category_id, name, description) VALUES (?, ?, ?)",
                   (2, "EXTERNAL PROXY (Android)", "Dedicated mobile proxy solution with auto IP rotation."))
    prod3_id = cursor.lastrowid
    for dur, price in [("1 Day", 0.30), ("7 Days", 0.70), ("1 Month", 1.50)]:
        cursor.execute("INSERT INTO product_variants (product_id, duration_name, price) VALUES (?, ?, ?)",
                       (prod3_id, dur, price))
        var_id = cursor.lastrowid
        cursor.execute("INSERT INTO product_stock (product_id, variant_id, item_content) VALUES (?, ?, ?)",
                       (prod3_id, var_id, f"PROXY-AND-{dur[:2]}-DEMO-KEY-4491"))

def get_or_create_user(user_id, username, first_name, referrer_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        valid_ref = None
        if referrer_id and referrer_id != user_id:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,))
            if cursor.fetchone():
                valid_ref = referrer_id

        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, referred_by) VALUES (?, ?, ?, ?)",
            (user_id, username, first_name, valid_ref)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    else:
        cursor.execute(
            "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
            (username, first_name, user_id)
        )
        conn.commit()

    conn.close()
    return dict(user)

def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_balance(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def deduct_user_balance(user_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = MAX(0, balance - ?) WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_categories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY id ASC")
    cats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return cats

def get_category(cat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
    cat = cursor.fetchone()
    conn.close()
    return dict(cat) if cat else None

def get_products_by_category(category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, COUNT(s.id) as total_stock
        FROM products p
        LEFT JOIN product_stock s ON p.id = s.product_id AND s.is_sold = 0
        WHERE p.category_id = ?
        GROUP BY p.id
        ORDER BY p.id ASC
    """, (category_id,))
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return products

def get_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, c.name as category_name, c.icon as category_icon
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    """, (product_id,))
    prod = cursor.fetchone()
    conn.close()
    return dict(prod) if prod else None

def get_product_variants_with_stock(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.*, COUNT(s.id) as in_stock
        FROM product_variants v
        LEFT JOIN product_stock s ON v.id = s.variant_id AND s.is_sold = 0
        WHERE v.product_id = ?
        GROUP BY v.id
        ORDER BY v.price ASC
    """, (product_id,))
    variants = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return variants

def get_variant(variant_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.*, p.name as product_name, p.category_id, COUNT(s.id) as in_stock
        FROM product_variants v
        JOIN products p ON v.product_id = p.id
        LEFT JOIN product_stock s ON v.id = s.variant_id AND s.is_sold = 0
        WHERE v.id = ?
        GROUP BY v.id
    """, (variant_id,))
    var = cursor.fetchone()
    conn.close()
    return dict(var) if var else None

def purchase_variant(user_id, variant_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check user
        cursor.execute("SELECT balance, total_spent, orders_count FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return {"success": False, "error": "User not found"}

        # Check variant
        cursor.execute("""
            SELECT v.*, p.name as product_name, p.id as product_id
            FROM product_variants v
            JOIN products p ON v.product_id = p.id
            WHERE v.id = ?
        """, (variant_id,))
        variant = cursor.fetchone()
        if not variant:
            return {"success": False, "error": "Variant not found"}

        price = variant["price"]
        if user["balance"] < price:
            return {"success": False, "error": "INSUFFICIENT_BALANCE", "required": price, "current": user["balance"]}

        # Check stock for this specific variant
        cursor.execute("SELECT id, item_content FROM product_stock WHERE variant_id = ? AND is_sold = 0 LIMIT 1", (variant_id,))
        stock = cursor.fetchone()
        if not stock:
            return {"success": False, "error": "OUT_OF_STOCK"}

        # Deduct user balance
        cursor.execute("""
            UPDATE users 
            SET balance = balance - ?, total_spent = total_spent + ?, orders_count = orders_count + 1 
            WHERE user_id = ?
        """, (price, price, user_id))

        # Mark stock sold
        now = datetime.now().isoformat()
        cursor.execute("UPDATE product_stock SET is_sold = 1, sold_to = ?, sold_at = ? WHERE id = ?", (user_id, now, stock["id"]))

        # Record order
        cursor.execute("""
            INSERT INTO orders (user_id, product_id, variant_id, product_name, duration_name, price, item_content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, variant["product_id"], variant_id, variant["product_name"], variant["duration_name"], price, stock["item_content"]))
        order_id = cursor.lastrowid

        conn.commit()
        return {
            "success": True,
            "order_id": order_id,
            "product_name": variant["product_name"],
            "duration_name": variant["duration_name"],
            "price": price,
            "item_content": stock["item_content"]
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def get_user_orders(user_id, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return orders

def get_referral_stats(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE referred_by = ?", (user_id,))
    ref_count = cursor.fetchone()["count"]

    cursor.execute("SELECT ref_earnings FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    earnings = row["ref_earnings"] if row else 0.0
    conn.close()
    return {"count": ref_count, "earnings": earnings}

def can_user_spin(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_spin_time FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["last_spin_time"]:
        return True, 0

    last_spin = datetime.fromisoformat(row["last_spin_time"])
    diff = (datetime.now() - last_spin).total_seconds()
    cooldown = 24 * 3600

    if diff >= cooldown:
        return True, 0
    return False, int(cooldown - diff)

def record_spin_reward(user_id, reward_amount):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("UPDATE users SET balance = balance + ?, last_spin_time = ? WHERE user_id = ?", (reward_amount, now, user_id))
    conn.commit()
    conn.close()

# ----------------- ADMIN DB FUNCTIONS -----------------

def get_admin_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count, COALESCE(SUM(price), 0) as total_rev FROM orders")
    order_row = cursor.fetchone()
    total_orders = order_row["count"]
    total_revenue = order_row["total_rev"]

    cursor.execute("SELECT COUNT(*) as count FROM products")
    total_products = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM product_stock WHERE is_sold = 0")
    total_stock = cursor.fetchone()["count"]

    conn.close()
    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_products": total_products,
        "total_stock": total_stock
    }

def get_all_products_with_stock():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, c.name as category_name, COUNT(s.id) as total_stock
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_stock s ON p.id = s.product_id AND s.is_sold = 0
        GROUP BY p.id
        ORDER BY c.id ASC, p.id ASC
    """)
    prods = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return prods

def add_stock_bulk(product_id, variant_id, items_list):
    conn = get_connection()
    cursor = conn.cursor()
    added = 0
    for item in items_list:
        item = item.strip()
        if item:
            cursor.execute("INSERT INTO product_stock (product_id, variant_id, item_content) VALUES (?, ?, ?)",
                           (product_id, variant_id, item))
            added += 1
    conn.commit()
    conn.close()
    return added

def clear_variant_stock(variant_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_stock WHERE variant_id = ? AND is_sold = 0", (variant_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def get_variant_unsold_stock(variant_id, limit=30):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_content FROM product_stock WHERE variant_id = ? AND is_sold = 0 LIMIT ?", (variant_id, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def delete_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_stock WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM product_variants WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def add_category(name, icon="📁"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO categories (name, icon) VALUES (?, ?)", (name, icon))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def delete_category(category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_stock WHERE product_id IN (SELECT id FROM products WHERE category_id = ?)", (category_id,))
    cursor.execute("DELETE FROM product_variants WHERE product_id IN (SELECT id FROM products WHERE category_id = ?)", (category_id,))
    cursor.execute("DELETE FROM products WHERE category_id = ?", (category_id,))
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()

def add_product_with_default_variants(category_id, name, description, price_1d, price_7d, price_1m):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (category_id, name, description) VALUES (?, ?, ?)",
                   (category_id, name, description))
    product_id = cursor.lastrowid

    variants = [
        ("1 Day", price_1d),
        ("7 Days", price_7d),
        ("1 Month", price_1m)
    ]
    for dur, pr in variants:
        cursor.execute("INSERT INTO product_variants (product_id, duration_name, price) VALUES (?, ?, ?)",
                       (product_id, dur, pr))

    conn.commit()
    conn.close()
    return product_id

def add_product_with_custom_variants(category_id, name, description, variants_list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (category_id, name, description) VALUES (?, ?, ?)",
                   (category_id, name, description))
    product_id = cursor.lastrowid

    for dur, pr in variants_list:
        cursor.execute("INSERT INTO product_variants (product_id, duration_name, price) VALUES (?, ?, ?)",
                       (product_id, dur, pr))

    conn.commit()
    conn.close()
    return product_id

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, balance FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

