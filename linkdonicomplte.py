import requests
import time
import sqlite3
from datetime import datetime
from flask import Flask
import threading
import os

# ==================== تنظیمات ====================
BOT_TOKEN = "620956184:4zqEfC-Y0F9nXbZL653Yw5-nIZnkNYSEsng"
CHANNEL_IDS = ["@linkdoniraiganlink",
"@linkdoniraiganlink2",
"@linkdoniraiganlink33"]
ADMIN_ID = 377993776
SUPER_ADMIN_ID = 2021919317
BOT_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"
BOT_USERNAME = "linkdoni1_bot"
# ═══ وب‌سرور کوچیک برای Render ═══
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Linkdoni Bot is running"

@web_app.route('/health')
def health():
    return "OK"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

def start_web():
    threading.Thread(target=run_web, daemon=True).start()
    
# ✅ آیدی مالک برای پرداخت پاکت هدیه (بدون @)
OWNER_USERNAME = "Amir_X_2023"

# 💾 شماره کارت برای رسید
CARD_NUMBER = "5047061152529703"
CARD_HOLDER = "صغرا پاریاب"

# ✅ قیمت‌ها برگشت به حالت قبل:
REFERRAL_REWARD = 1000
AD_PRICES = {"text": 10000, "photo": 20000}
AD_DESCRIPTIONS = {"text": "📝 تبلیغ متنی (بدون عکس)", "photo": "🖼 تبلیغ با عکس (بنر)"}

def fmt_price(p):
    try: return f"{int(p):,}"
    except: return str(p)

def parse_number(text):
    if text is None: return None
    pd = "۰۱۲۳۴۵۶۷۸۹"; ad = "٠١٢٣٤٥٦٧٨٩"; ed = "0123456789"
    result = ""
    for ch in str(text):
        if ch in pd: result += ed[pd.index(ch)]
        elif ch in ad: result += ed[ad.index(ch)]
        else: result += ch
    result = result.replace(",", "").replace(" ", "").replace("٬", "").strip()
    try: return int(result)
    except: return None

# ==================== دیتابیس ====================
def init_db():
    conn = sqlite3.connect("bot.db"); cur = conn.cursor()
    try: cur.execute("SELECT balance, invited_by FROM users LIMIT 1")
    except:
        print("⚠️ بازسازی جدول users..."); cur.execute("DROP TABLE IF EXISTS users")
    try: cur.execute("SELECT ad_type, content, status FROM pending_ads LIMIT 1")
    except:
        print("⚠️ بازسازی جدول pending_ads..."); cur.execute("DROP TABLE IF EXISTS pending_ads")
    try: cur.execute("SELECT photo_id, status FROM receipts LIMIT 1")
    except:
        print("⚠️ بازسازی جدول receipts..."); cur.execute("DROP TABLE IF EXISTS receipts")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0, invited_by INTEGER)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS pending_ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, ad_type TEXT,
        content TEXT, photo_id TEXT, cost INTEGER, status TEXT DEFAULT 'pending', date TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount INTEGER,
        photo_id TEXT, status TEXT DEFAULT 'pending', date TEXT)""")
    conn.commit()
    cur.execute("PRAGMA table_info(users)")
    if "invited_by" not in [c[1] for c in cur.fetchall()]:
        cur.execute("ALTER TABLE users ADD COLUMN invited_by INTEGER")
    conn.commit(); conn.close()
    print("✅ دیتابیس آماده است.")

def get_user(uid):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,)); u = cur.fetchone(); c.close(); return u

def create_user(uid, un, inv=None):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, invited_by) VALUES (?,?,?)", (uid, un, inv))
    c.commit(); c.close()

def update_balance(uid, amt):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amt, uid))
    c.commit(); c.close()

def add_referral(uid):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (uid,))
    c.commit(); c.close()

def set_invited_by(uid, inv):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("UPDATE users SET invited_by=? WHERE user_id=?", (inv, uid))
    c.commit(); c.close()

def get_all_users():
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("SELECT user_id, username, balance FROM users"); u = cur.fetchall(); c.close(); return u

def save_ad(uid, atype, content, pid, cost):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("INSERT INTO pending_ads (user_id, ad_type, content, photo_id, cost, status, date) VALUES (?,?,?,?,?,'pending',?)",
                (uid, atype, content, pid, cost, datetime.now().strftime("%Y-%m-%d %H:%M")))
    c.commit(); rid = cur.lastrowid; c.close(); return rid

def get_ad(ad_id):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("SELECT * FROM pending_ads WHERE id=?", (ad_id,)); r = cur.fetchone(); c.close(); return r

def update_ad_status(ad_id, status):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("UPDATE pending_ads SET status=? WHERE id=?", (status, ad_id))
    c.commit(); c.close()

def save_receipt(uid, amount, photo_id):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("INSERT INTO receipts (user_id, amount, photo_id, status, date) VALUES (?,?,?,'pending',?)",
                (uid, amount, photo_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
    c.commit(); rid = cur.lastrowid; c.close(); return rid

def get_receipt(rid):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("SELECT * FROM receipts WHERE id=?", (rid,)); r = cur.fetchone(); c.close(); return r

def update_receipt_status(rid, status):
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("UPDATE receipts SET status=? WHERE id=?", (status, rid))
    c.commit(); c.close()

def get_pending_receipts():
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("SELECT id, user_id, amount, photo_id, date FROM receipts WHERE status='pending'")
    r = cur.fetchall(); c.close(); return r

def reset_all_data():
    c = sqlite3.connect("bot.db"); cur = c.cursor()
    cur.execute("DELETE FROM pending_ads")
    cur.execute("DELETE FROM receipts")
    cur.execute("UPDATE users SET balance = 0 WHERE user_id != ?", (SUPER_ADMIN_ID,))
    cur.execute("UPDATE users SET referrals = 0 WHERE user_id != ?", (SUPER_ADMIN_ID,))
    c.commit(); c.close()
    return True

# ==================== API ====================
def api(m, d):
    try: return requests.post(BOT_URL + m, json=d, timeout=15).json()
    except Exception as e: print(f"API Error: {e}"); return {"ok": False}

def send_message(cid, txt, rm=None):
    d = {"chat_id": cid, "text": txt}
    if rm: d["reply_markup"] = rm
    return api("sendMessage", d)

def send_photo(cid, ph, cap="", rm=None):
    if cap and len(cap) > 1020:
        cap = cap[:1017] + "..."
    d = {"chat_id": cid, "photo": ph, "caption": cap or ""}
    if rm: d["reply_markup"] = rm
    return api("sendPhoto", d)

def edit_message(cid, mid, txt, rm=None):
    d = {"chat_id": cid, "message_id": mid, "text": txt}
    if rm: d["reply_markup"] = rm
    return api("editMessageText", d)

def answer_callback(cbid, txt=None, alert=False):
    d = {"callback_query_id": cbid}
    if txt: d["text"] = txt; d["show_alert"] = alert
    return api("answerCallbackQuery", d)

def get_updates(off=None):
    p = {"timeout": 30}
    if off: p["offset"] = off
    try: return requests.get(BOT_URL + "getUpdates", params=p, timeout=40).json()
    except: return {"result": []}

def is_user_joined(uid):
    for ch in CHANNEL_IDS:
        r = api("getChatMember", {"chat_id": ch, "user_id": uid})
        if not r.get("ok") or r["result"].get("status") in ["left", "kicked"]: return False
    return True

# ==================== وضعیت ====================
user_states = {}
admin_state = {}
def is_admin(uid): return uid == ADMIN_ID or uid == SUPER_ADMIN_ID
def is_super_admin(uid): return uid == SUPER_ADMIN_ID

ALL_BUTTONS = [
    "📝 ثبت تبلیغ", "💰 افزایش موجودی", "👤 حساب کاربری", "💎 زیرمجموعه گیری",
    "📚 تعرفه ثبت", "💬 پشتیبانی", "👑 پنل مدیریت",
    "💳 تایید تبلیغات", "💳 تایید رسیدها", "👥 کاربران", "➕ شارژ دستی",
    "📊 آمار ربات", "🔙 خروج از پنل", "❌ انصراف", "🔄 ریست کامل"
]

# ==================== کیبوردها ====================
def kb_join():
    b = []
    for i, ch in enumerate(CHANNEL_IDS, 1):
        b.append([{"text": f"🔗 عضویت در کانال {i}", "url": f"https://ble.ir/{ch.replace('@','')}"}])
    b.append([{"text": "✅ عضو شدم", "callback_data": "check_join"}])
    return {"inline_keyboard": b}

def kb_main():
    return {"keyboard": [
        [{"text": "📝 ثبت تبلیغ"}, {"text": "💰 افزایش موجودی"}],
        [{"text": "👤 حساب کاربری"}, {"text": "💎 زیرمجموعه گیری"}],
        [{"text": "📚 تعرفه ثبت"}, {"text": "💬 پشتیبانی"}],
        [{"text": "👑 پنل مدیریت"}]
    ], "resize_keyboard": True}

def kb_admin(uid=None):
    kb = [
        [{"text": "💳 تایید تبلیغات"}, {"text": "💳 تایید رسیدها"}],
        [{"text": "👥 کاربران"}, {"text": "➕ شارژ دستی"}],
        [{"text": "📊 آمار ربات"}, {"text": "🔙 خروج از پنل"}],
        [{"text": "❌ انصراف"}]
    ]
    if uid and is_super_admin(uid):
        kb.append([{"text": "🔄 ریست کامل"}])
    return {"keyboard": kb, "resize_keyboard": True}

def kb_pay():
    return {"inline_keyboard": [
        [{"text": "20,000 تومان", "callback_data": "pay_20000"},
         {"text": "50,000 تومان", "callback_data": "pay_50000"}],
        [{"text": "100,000 تومان", "callback_data": "pay_100000"},
         {"text": "200,000 تومان", "callback_data": "pay_200000"}],
        [{"text": "🔙 بازگشت", "callback_data": "back_main"}]
    ]}

def kb_charge_needed():
    return {"inline_keyboard": [
        [{"text": "💰 افزایش موجودی", "callback_data": "open_pay"}],
        [{"text": "🔙 بازگشت", "callback_data": "back_main"}]
    ]}

def kb_channel_link():
    return {"inline_keyboard": [
        [{"text": "🤖 ربات لینکدونی", "url": f"https://ble.ir/{BOT_USERNAME}"}]
    ]}

def kb_ad_approve(ad_id):
    return {"inline_keyboard": [
        [{"text": "✅ تایید و انتشار در کانال‌ها", "callback_data": f"approvead_{ad_id}"},
         {"text": "❌ رد تبلیغ", "callback_data": f"rejectad_{ad_id}"}]
    ]}

def kb_receipt_approve(rid, uid, amt):
    return {"inline_keyboard": [
        [{"text": "✅ تایید شارژ", "callback_data": f"approverec_{rid}_{uid}_{amt}"},
         {"text": "❌ رد رسید", "callback_data": f"rejectrec_{rid}_{uid}"}]
    ]}

def kb_reset_confirm():
    return {"inline_keyboard": [
        [{"text": "✅ بله، ریست کن", "callback_data": "confirm_reset"},
         {"text": "❌ لغو", "callback_data": "cancel_reset"}]
    ]}

# ==================== هندلر پیام ====================
def handle_message(msg):
    if "from" not in msg or not msg.get("from"): return
    if "chat" not in msg or not msg.get("chat"): return
    chat_type = msg["chat"].get("type", "private")
    if chat_type != "private": return

    cid = msg["chat"]["id"]
    uid = msg["from"]["id"]
    text = (msg.get("text") or msg.get("caption") or "").strip()
    photo = msg.get("photo")

    if not get_user(uid):
        create_user(uid, msg["from"].get("username", "بدون نام"))

    if text == "❌ انصراف":
        if uid in admin_state: del admin_state[uid]
        if uid in user_states: del user_states[uid]
        send_message(cid, "✅ عملیات لغو شد.", kb_admin(uid) if is_admin(uid) else kb_main())
        return

    if text in ALL_BUTTONS:
        if uid in admin_state: del admin_state[uid]
        if uid in user_states: del user_states[uid]

    # ============ پنل مدیریت: شارژ دستی ============
    if is_admin(uid) and uid in admin_state:
        state = admin_state[uid]
        if state == "waiting_user_id":
            target = parse_number(text)
            if target is None:
                send_message(cid, "❌ آیدی نامعتبر. لطفاً فقط عدد بفرستید.\nمثال: 123456789", kb_admin(uid))
                return
            if not get_user(target):
                send_message(cid, f"❌ کاربر {target} در ربات ثبت نشده است.", kb_admin(uid))
                del admin_state[uid]; return
            admin_state[uid] = {"state": "waiting_amount", "target": target}
            u = get_user(target)
            un = u[1] if u and u[1] else "بی‌نام"
            send_message(cid, f"💰 مبلغ شارژ (تومان) را وارد کنید:\n\n👤 کاربر: {target}\n📛 نام: @{un}\n\n(برای لغو، ❌ انصراف)")
            return
        elif isinstance(state, dict) and state.get("state") == "waiting_amount":
            amt = parse_number(text)
            if amt is None or amt <= 0:
                send_message(cid, "❌ مبلغ نامعتبر. لطفاً فقط عدد بفرستید.\nمثال: 50000 یا 50,000", kb_admin(uid))
                return
            target = state["target"]
            update_balance(target, amt)
            send_message(cid, f"✅ شارژ موفق!\n\n👤 کاربر: {target}\n💰 مبلغ: {fmt_price(amt)} تومان", kb_admin(uid))
            try: send_message(target, f"💰 حساب شما به مبلغ {fmt_price(amt)} تومان شارژ شد.\n\nبا تشکر 🙏")
            except: pass
            del admin_state[uid]
            return

    # ============ بررسی عضویت ============
    if not is_admin(uid) and not is_user_joined(uid) and text != "/start":
        send_message(cid, "⚠️ ابتدا در کانال‌ها عضو شوید:", kb_join())
        return

    # ============ /start ============
    if text == "/start":
        if uid in user_states: del user_states[uid]
        if uid in admin_state: del admin_state[uid]
        if not is_user_joined(uid) and not is_admin(uid):
            send_message(cid, "⚠️ برای استفاده، ابتدا در کانال‌های زیر عضو شوید:", kb_join())
            return
        parts = text.split()
        if len(parts) > 1:
            try:
                inv = int(parts[1])
                u = get_user(uid)
                if inv != uid and u and u[4] is None:
                    set_invited_by(uid, inv)
                    update_balance(inv, REFERRAL_REWARD)
                    add_referral(inv)
                    try: send_message(inv, f"🎉 یک کاربر جدید با لینک شما وارد شد!\n💰 {fmt_price(REFERRAL_REWARD)} تومان دریافت کردید.")
                    except: pass
            except: pass
        send_message(cid, "🎉 به ربات لینکدونی خوش آمدید!\nاز منوی زیر استفاده کنید:", kb_main())
        return

    # ============ پنل مدیریت ============
    if text == "👑 پنل مدیریت":
        if is_admin(uid): send_message(cid, "👑 به پنل مدیریت خوش آمدید:", kb_admin(uid))
        else: send_message(cid, "⛔ شما دسترسی به پنل مدیریت ندارید.", kb_main())
        return

    # ============ دکمه‌های پنل ادمین ============
    if is_admin(uid):
        if text == "💳 تایید تبلیغات":
            c = sqlite3.connect("bot.db"); cur = c.cursor()
            cur.execute("SELECT id, user_id, ad_type, content, photo_id, cost, date FROM pending_ads WHERE status='pending'")
            ads = cur.fetchall(); c.close()
            if not ads:
                send_message(cid, "📭 هیچ تبلیغی در انتظار تایید نیست.", kb_admin(uid))
            else:
                send_message(cid, f"📥 {len(ads)} تبلیغ در انتظار تایید:", kb_admin(uid))
                for ad in ads:
                    ad_id, tuid, atype, content, pid, cost, dt = ad
                    u = get_user(tuid)
                    un = u[1] if u and u[1] else "بی‌نام"
                    bal = int(u[2]) if u and u[2] else 0
                    bal_text = "∞ (نامحدود)" if is_super_admin(tuid) else f"{fmt_price(bal)} تومان"
                    cap = (f"📥 تبلیغ #{ad_id}\n\n"
                           f"👤 کاربر: {tuid}\n"
                           f"📛 نام: @{un}\n"
                           f"💰 موجودی کاربر: {bal_text}\n"
                           f"🎯 نوع: {AD_DESCRIPTIONS.get(atype, atype)}\n"
                           f"💵 هزینه: {fmt_price(cost)} تومان\n"
                           f"📅 تاریخ: {dt}\n"
                           f"📝 محتوا:\n{(content or 'بدون متن')[:400]}")
                    if pid:
                        send_photo(cid, pid, cap, kb_ad_approve(ad_id))
                    else:
                        send_message(cid, cap, kb_ad_approve(ad_id))
            return
        elif text == "💳 تایید رسیدها":
            rs = get_pending_receipts()
            if not rs:
                send_message(cid, "📭 هیچ رسیدی در انتظار تایید نیست.", kb_admin(uid))
            else:
                send_message(cid, f"📥 {len(rs)} رسید در انتظار تایید:", kb_admin(uid))
                for r in rs:
                    rid, tuid, amt, pid, dt = r
                    u = get_user(tuid)
                    un = u[1] if u and u[1] else "بی‌نام"
                    cap = (f"📥 رسید شارژ #{rid}\n\n"
                           f"👤 کاربر: {tuid}\n"
                           f"📛 نام: @{un}\n"
                           f"💰 مبلغ: {fmt_price(amt)} تومان\n"
                           f"📅 {dt}")
                    send_photo(cid, pid, cap, kb_receipt_approve(rid, tuid, amt))
            return
        elif text == "👥 کاربران":
            users = get_all_users()
            if not users: send_message(cid, "📭 هیچ کاربری نیست.", kb_admin(uid))
            else:
                txt = f"👥 کاربران ({len(users)} نفر):\n\n"
                count = 0
                for u in users:
                    if is_super_admin(u[0]):
                        continue
                    if count >= 30: break
                    un = u[1] if u[1] else "بی‌نام"
                    bal = int(u[2]) if u[2] else 0
                    txt += f"🆔 {u[0]} | @{un} | 💰 {fmt_price(bal)}\n"
                    count += 1
                if len(users) - 1 > 30:
                    txt += f"\n... و {len(users) - 31} نفر دیگر"
                send_message(cid, txt, kb_admin(uid))
            return
        elif text == "➕ شارژ دستی":
            admin_state[uid] = "waiting_user_id"
            send_message(cid, "🆔 آیدی عددی کاربر را وارد کنید:\n\n(مثال: 123456789)\n\n(برای لغو، ❌ انصراف)", kb_admin(uid))
            return
        elif text == "📊 آمار ربات":
            users = get_all_users()
            tb = 0
            real_user_count = 0
            for u in users:
                if is_super_admin(u[0]):
                    continue
                real_user_count += 1
                try: tb += int(u[2]) if u[2] else 0
                except: pass
            c = sqlite3.connect("bot.db"); cur = c.cursor()
            cur.execute("SELECT COUNT(*) FROM pending_ads WHERE status='pending'")
            pending_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM receipts WHERE status='pending'")
            receipts_count = cur.fetchone()[0]
            c.close()
            txt = (f"📊 آمار ربات\n\n"
                   f"👥 کاربران عادی: {real_user_count} نفر\n"
                   f"💰 مجموع موجودی کاربران: {fmt_price(tb)} تومان\n"
                   f"📥 تبلیغات در انتظار تایید: {pending_count}\n"
                   f"📥 رسیدهای در انتظار تایید: {receipts_count}\n"
                   f"📢 کانال‌ها: {len(CHANNEL_IDS)}\n\n"
                   f"💵 تعرفه متنی: {fmt_price(AD_PRICES['text'])} تومان\n"
                   f"🖼 تعرفه عکس: {fmt_price(AD_PRICES['photo'])} تومان")
            send_message(cid, txt, kb_admin(uid))
            return
        elif text == "🔙 خروج از پنل":
            send_message(cid, "از پنل خارج شدید.", kb_main())
            return
        elif text == "🔄 ریست کامل":
            if not is_super_admin(uid):
                send_message(cid, "⛔ شما دسترسی به این بخش ندارید.", kb_admin(uid))
                return
            send_message(cid,
                "⚠️ هشدار!\n\n"
                "این عملیات باعث می‌شود:\n"
                "• تمام تبلیغات پاک شوند\n"
                "• تمام رسیدها پاک شوند\n"
                "• موجودی تمام کاربران صفر شود\n"
                "• زیرمجموعه‌ها صفر شوند\n\n"
                "💰 موجودی سوپر ادمین دست‌نخورده می‌ماند.\n\n"
                "آیا مطمئن هستید؟",
                kb_reset_confirm())
            return

    # ============ 👤 حساب کاربری ============
    if text == "👤 حساب کاربری":
        u = get_user(uid)
        if u:
            if is_super_admin(uid):
                send_message(cid, f"📌 اطلاعات شما:\n\n🖊 شناسه: «{uid}»\n💰 موجودی: «∞ (نامحدود)»\n👑 شما سوپر ادمین هستید")
            else:
                try: bal = int(u[2]) if u[2] else 0
                except: bal = 0
                try: refs = int(u[3]) if u[3] else 0
                except: refs = 0
                send_message(cid, f"📌 اطلاعات شما:\n\n🖊 شناسه: «{uid}»\n💰 موجودی: «{fmt_price(bal)} تومان»\n👥 زیرمجموعه: «{refs} نفر»")

    # ============ 💰 افزایش موجودی ============
    elif text == "💰 افزایش موجودی":
        if is_super_admin(uid):
            send_message(cid, "👑 شما سوپر ادمین هستید و موجودی نامحدود دارید!")
        else:
            send_message(cid,
                f"💰 افزایش موجودی حساب\n\n"
                f"💳 یکی از پکیج‌های زیر را انتخاب کنید:\n\n"
                f"🎁 همچنین می‌توانید پاکت هدیه به پیوی مالک ارسال کنید:\n"
                f"👤 @{OWNER_USERNAME}\n\n"
                f"پس از واریز، رسید خود را برای ربات ارسال کنید تا ادمین تایید کند.",
                kb_pay())

    # ============ 💎 زیرمجموعه گیری ============
    elif text == "💎 زیرمجموعه گیری":
        link = f"https://ble.ir/{BOT_USERNAME}?start={uid}"
        send_message(cid, f"🌟 لینک دعوت اختصاصی شما:\n\n🔗 {link}\n\n💰 با هر نفر جدید {fmt_price(REFERRAL_REWARD)} تومان دریافت می‌کنید.")

    # ============ 📚 تعرفه ثبت ============
    elif text == "📚 تعرفه ثبت":
        send_message(cid, 
            f"📋 تعرفه‌های ثبت تبلیغ:\n\n"
            f"1️⃣ {AD_DESCRIPTIONS['text']}: {fmt_price(AD_PRICES['text'])} تومان\n"
            f"2️⃣ {AD_DESCRIPTIONS['photo']}: {fmt_price(AD_PRICES['photo'])} تومان\n\n"
            f"💳 شماره کارت: {CARD_NUMBER}\n"
            f"👤 به نام: {CARD_HOLDER}\n\n"
            f"🎁 می‌توانید پاکت هدیه به پیوی مالک ارسال کنید:\n👤 @{OWNER_USERNAME}")

    # ============ 💬 پشتیبانی ============
    elif text == "💬 پشتیبانی":
        send_message(cid, f"💬 برای ارتباط با پشتیبانی پیام دهید:\n👤 @{OWNER_USERNAME}")

    # ============ 📝 ثبت تبلیغ ============
    elif text == "📝 ثبت تبلیغ":
        user_states[uid] = {"state": "waiting_ad_content"}
        send_message(cid,
            "📝 ثبت تبلیغ در لینکدونی\n\n"
            "برای ثبت تبلیغ در لینکدونی، لطفاً ابتدا متن یا بنر خود را ارسال کنید.\n\n"
            "شما می‌توانید تبلیغات خود را به دو روش مختلف ثبت کنید:\n\n"
            "1️⃣ ارسال متن\n"
            "در این روش شما تنها یک پیام متنی ارسال می‌کنید و آن متن به همان صورت در کانال قرار خواهد گرفت.\n\n"
            "2️⃣ ارسال بنر تصویری\n"
            "در این روش شما یک بنر تصویری ارسال می‌کنید. همچنین متنی که می‌خواهید زیر تصویر نمایش داده شود را به عنوان کپشن در کنار تصویر قرار دهید.\n\n"
            "💡 لطفاً متن تبلیغ یا عکس تبلیغ خود را همراه کپشن ارسال کنید:\n\n"
            f"💰 تعرفه‌ها:\n"
            f"▫️ متن: {fmt_price(AD_PRICES['text'])} تومان\n"
            f"▫️ عکس: {fmt_price(AD_PRICES['photo'])} تومان\n\n"
            "⚠️ توجه: تبلیغ شما پس از ثبت، ابتدا توسط ادمین بررسی و تایید می‌شود و سپس در کانال‌ها منتشر خواهد شد.\n"
            "💰 هزینه فقط پس از تایید ادمین از حساب شما کسر می‌شود.\n\n"
            "(برای لغو، ❌ انصراف)")
        return

    # ============ دریافت محتوای تبلیغ ============
    elif uid in user_states and user_states[uid].get("state") == "waiting_ad_content":
        u = get_user(uid)
        bal = int(u[2]) if u and u[2] else 0
        unlimited = is_super_admin(uid)

        if photo:
            cost = AD_PRICES["photo"]
            if not unlimited and bal < cost:
                send_message(cid,
                    f"❌ موجودی شما کافی نیست!\n\n"
                    f"💰 موجودی فعلی: {fmt_price(bal)} تومان\n"
                    f"💰 مورد نیاز: {fmt_price(cost)} تومان\n\n"
                    f"لطفاً ابتدا حساب خود را شارژ کنید.",
                    kb_charge_needed())
                del user_states[uid]
                return
            ad_id = save_ad(uid, "photo", text or "", photo[-1]["file_id"], cost)
            bal_text = "∞ (نامحدود)" if unlimited else f"{fmt_price(bal)} تومان"
            send_message(cid,
                f"⏳ تبلیغ شما در حال بررسی توسط ادمین است...\n\n"
                f"📝 پس از تایید ادمین، تبلیغ شما در کانال‌ها منتشر خواهد شد.\n\n"
                f"💰 هزینه پس از تایید کسر می‌شود: {fmt_price(cost)} تومان\n"
                f"💳 موجودی فعلی شما: {bal_text}\n\n"
                f"🆔 کد پیگیری تبلیغ: #{ad_id}")
            un = u[1] if u and u[1] else "بی‌نام"
            admin_cap = (f"📥 تبلیغ جدید #{ad_id}\n\n"
                         f"👤 کاربر: {uid}\n"
                         f"📛 نام: @{un}\n"
                         f"💰 موجودی کاربر: {bal_text}\n"
                         f"🎯 نوع: {AD_DESCRIPTIONS['photo']}\n"
                         f"💵 هزینه: {fmt_price(cost)} تومان\n"
                         f"📝 کپشن: {text or 'بدون متن'}")
            send_photo(ADMIN_ID, photo[-1]["file_id"], admin_cap, kb_ad_approve(ad_id))
            del user_states[uid]

        elif text and text not in ALL_BUTTONS:
            cost = AD_PRICES["text"]
            if not unlimited and bal < cost:
                send_message(cid,
                    f"❌ موجودی شما کافی نیست!\n\n"
                    f"💰 موجودی فعلی: {fmt_price(bal)} تومان\n"
                    f"💰 مورد نیاز: {fmt_price(cost)} تومان\n\n"
                    f"لطفاً ابتدا حساب خود را شارژ کنید.",
                    kb_charge_needed())
                del user_states[uid]
                return
            ad_id = save_ad(uid, "text", text, None, cost)
            bal_text = "∞ (نامحدود)" if unlimited else f"{fmt_price(bal)} تومان"
            send_message(cid,
                f"⏳ تبلیغ شما در حال بررسی توسط ادمین است...\n\n"
                f"📝 پس از تایید ادمین، تبلیغ شما در کانال‌ها منتشر خواهد شد.\n\n"
                f"💰 هزینه پس از تایید کسر می‌شود: {fmt_price(cost)} تومان\n"
                f"💳 موجودی فعلی شما: {bal_text}\n\n"
                f"🆔 کد پیگیری تبلیغ: #{ad_id}")
            un = u[1] if u and u[1] else "بی‌نام"
            admin_cap = (f"📥 تبلیغ جدید #{ad_id}\n\n"
                         f"👤 کاربر: {uid}\n"
                         f"📛 نام: @{un}\n"
                         f"💰 موجودی کاربر: {bal_text}\n"
                         f"🎯 نوع: {AD_DESCRIPTIONS['text']}\n"
                         f"💵 هزینه: {fmt_price(cost)} تومان\n"
                         f"📝 متن:\n{text[:500]}")
            send_message(ADMIN_ID, admin_cap, kb_ad_approve(ad_id))
            del user_states[uid]
        else:
            send_message(cid, "❌ لطفاً متن یا عکس تبلیغ خود را ارسال کنید.")

    # ============ دریافت رسید شارژ ============
    elif uid in user_states and user_states[uid].get("state") == "waiting_receipt":
        if photo:
            amt = user_states[uid]["amount"]
            rid = save_receipt(uid, amt, photo[-1]["file_id"])
            u = get_user(uid)
            un = u[1] if u and u[1] else "بی‌نام"
            # ارسال به ادمین
            cap = (f"📥 رسید شارژ جدید #{rid}\n\n"
                   f"👤 کاربر: {uid}\n"
                   f"📛 نام: @{un}\n"
                   f"💰 مبلغ: {fmt_price(amt)} تومان")
            send_photo(ADMIN_ID, photo[-1]["file_id"], cap, kb_receipt_approve(rid, uid, amt))
            send_message(cid, "✅ رسید شما دریافت شد. پس از تایید ادمین، حساب شما شارژ می‌شود.")
            del user_states[uid]
        else:
            send_message(cid, "❌ لطفاً عکس رسید را ارسال کنید.")

# ==================== هندلر callback ====================
def handle_callback(cb):
    if "from" not in cb or not cb.get("from"): return
    if "message" not in cb or not cb.get("message"): return

    cbid = cb["id"]; cid = cb["message"]["chat"]["id"]
    mid = cb["message"]["message_id"]; uid = cb["from"]["id"]
    data = cb["data"]

    if data == "check_join":
        if is_user_joined(uid):
            answer_callback(cbid, "✅ عضویت تایید شد!")
            edit_message(cid, mid, "✅ عضویت تایید شد!\nاز منو استفاده کنید.", kb_main())
        else: answer_callback(cbid, "❌ هنوز در همه کانال‌ها عضو نشده‌اید!", True)

    elif data == "back_main":
        answer_callback(cbid)
        if uid in user_states: del user_states[uid]
        edit_message(cid, mid, "به منوی اصلی بازگشتید.", kb_main())

    elif data == "open_pay":
        answer_callback(cbid)
        edit_message(cid, mid,
            f"💰 افزایش موجودی حساب\n\n"
            f"💳 یکی از پکیج‌های زیر را انتخاب کنید:\n\n"
            f"🎁 همچنین می‌توانید پاکت هدیه به پیوی مالک ارسال کنید:\n"
            f"👤 @{OWNER_USERNAME}",
            kb_pay())

    # --- انتخاب پکیج شارژ → درخواست رسید ---
    elif data.startswith("pay_"):
        try:
            amt = int(data.split("_")[1])
        except:
            answer_callback(cbid, "❌ خطا در پکیج")
            return
        user_states[uid] = {"state": "waiting_receipt", "amount": amt}
        answer_callback(cbid, "💳 شماره کارت ارسال شد.")
        try:
            edit_message(cid, mid,
                f"💳 افزایش اعتبار\n\n"
                f"💰 مبلغ: {fmt_price(amt)} تومان\n"
                f"💳 شماره کارت: {CARD_NUMBER}\n"
                f"👤 به نام: {CARD_HOLDER}\n\n"
                f"لطفاً مبلغ را از طریق کیف پول بله به کارت بالا واریز کنید.\n\n"
                f"سپس **عکس رسید** را برای ربات ارسال کنید تا پس از تایید ادمین، حساب شما شارژ شود.\n\n"
                f"🎁 همچنین می‌توانید پاکت هدیه به پیوی مالک ارسال کنید:\n"
                f"👤 @{OWNER_USERNAME}",
                None)
        except: pass

    # ============ تایید شارژ توسط ادمین ============
    elif data.startswith("approverec_"):
        if not is_admin(uid):
            answer_callback(cbid, "⛔ فقط ادمین!")
            return
        try:
            parts = data.split("_")
            rid = int(parts[1]); tuid = int(parts[2]); amt = int(parts[3])
        except:
            answer_callback(cbid, "❌ خطا در اطلاعات")
            return
        update_balance(tuid, amt)
        update_receipt_status(rid, "approved")
        answer_callback(cbid, "✅ شارژ انجام شد.")
        try:
            edit_message(cid, mid,
                f"✅ رسید #{rid} تایید شد.\n"
                f"💰 {fmt_price(amt)} تومان به کاربر {tuid} اضافه شد.",
                None)
        except: pass
        try:
            u = get_user(tuid)
            bal = int(u[2]) if u and u[2] else 0
            send_message(tuid,
                f"✅ رسید شما تایید شد!\n\n"
                f"💰 مبلغ: {fmt_price(amt)} تومان\n"
                f"💳 موجودی جدید: {fmt_price(bal)} تومان\n\n"
                f"با تشکر 🙏")
        except: pass

    # ============ رد رسید توسط ادمین ============
    elif data.startswith("rejectrec_"):
        if not is_admin(uid):
            answer_callback(cbid, "⛔ فقط ادمین!")
            return
        try:
            parts = data.split("_")
            rid = int(parts[1]); tuid = int(parts[2])
        except:
            answer_callback(cbid, "❌ خطا در اطلاعات")
            return
        update_receipt_status(rid, "rejected")
        answer_callback(cbid, "❌ رسید رد شد.")
        try:
            edit_message(cid, mid, f"❌ رسید #{rid} رد شد.", None)
        except: pass
        try:
            send_message(tuid,
                f"❌ متاسفانه رسید شما رد شد.\n\n"
                f"لطفاً با پشتیبانی تماس بگیرید:\n👤 @{OWNER_USERNAME}")
        except: pass

    # ============ تایید تبلیغ ============
    elif data.startswith("approvead_"):
        if not is_admin(uid):
            answer_callback(cbid, "⛔ فقط ادمین!")
            return
        try:
            ad_id = int(data.split("_")[1])
        except:
            answer_callback(cbid, "❌ خطا در شناسه تبلیغ")
            return
        ad = get_ad(ad_id)
        if not ad:
            edit_message(cid, mid, "❌ تبلیغ پیدا نشد.")
            return
        tuid, atype, content, ad_pid, cost = ad[1], ad[2], ad[3], ad[4], ad[5]

        u = get_user(tuid)
        bal = int(u[2]) if u and u[2] else 0
        unlimited = is_super_admin(tuid)

        if not unlimited and bal < cost:
            update_ad_status(ad_id, "rejected")
            answer_callback(cbid, "❌ موجودی کاربر کافی نیست!")
            try:
                edit_message(cid, mid,
                    f"❌ تبلیغ #{ad_id} تایید نشد!\n\n"
                    f"موجودی کاربر ({fmt_price(bal)} تومان) از هزینه ({fmt_price(cost)} تومان) کمتر است.",
                    None)
            except: pass
            try:
                send_message(tuid,
                    f"❌ تبلیغ شما تایید نشد!\n\n"
                    f"💰 موجودی فعلی شما: {fmt_price(bal)} تومان\n"
                    f"💵 هزینه تبلیغ: {fmt_price(cost)} تومان\n\n"
                    f"لطفاً ابتدا حساب خود را شارژ کنید و مجدداً تبلیغ ثبت کنید.")
            except: pass
            return

        new_bal = bal
        if not unlimited:
            update_balance(tuid, -cost)
            new_bal = bal - cost

        sent = 0
        for ch in CHANNEL_IDS:
            if atype == "photo" and ad_pid:
                r = send_photo(ch, ad_pid, content or "", kb_channel_link())
            else:
                r = send_message(ch, content or "", kb_channel_link())
            if r.get("ok"): sent += 1

        update_ad_status(ad_id, "approved")
        answer_callback(cbid, f"✅ تبلیغ منتشر شد ({sent} کانال).")
        deduct_text = "∞ (سوپر ادمین)" if unlimited else f"{fmt_price(cost)} تومان"
        try:
            edit_message(cid, mid,
                f"✅ تبلیغ #{ad_id} تایید شد.\n"
                f"📤 منتشر شده در {sent} از {len(CHANNEL_IDS)} کانال\n"
                f"💰 کسر شده: {deduct_text}",
                None)
        except: pass
        try:
            if unlimited:
                send_message(tuid,
                    f"✅ تبلیغ شما تایید و در {sent} کانال منتشر شد!\n\n"
                    f"👑 موجودی شما نامحدود است\n"
                    f"🆔 کد پیگیری: #{ad_id}")
            else:
                send_message(tuid,
                    f"✅ تبلیغ شما تایید و در {sent} کانال منتشر شد!\n\n"
                    f"💰 مبلغ کسر شده: {fmt_price(cost)} تومان\n"
                    f"💳 موجودی جدید: {fmt_price(new_bal)} تومان\n"
                    f"🆔 کد پیگیری: #{ad_id}")
        except: pass

    # ============ رد تبلیغ ============
    elif data.startswith("rejectad_"):
        if not is_admin(uid):
            answer_callback(cbid, "⛔ فقط ادمین!")
            return
        try:
            ad_id = int(data.split("_")[1])
        except:
            answer_callback(cbid, "❌ خطا در شناسه تبلیغ")
            return
        ad = get_ad(ad_id)
        if not ad:
            edit_message(cid, mid, "❌ تبلیغ پیدا نشد.")
            return
        tuid = ad[1]
        update_ad_status(ad_id, "rejected")
        answer_callback(cbid, "❌ تبلیغ رد شد.")
        try:
            edit_message(cid, mid,
                f"❌ تبلیغ #{ad_id} رد شد.\n"
                f"💰 هیچ مبلغی از کاربر کسر نشده بود.",
                None)
        except: pass
        try:
            send_message(tuid,
                f"❌ متاسفانه تبلیغ شما توسط ادمین رد شد.\n\n"
                f"💰 هیچ مبلغی از حساب شما کسر نشده است.\n\n"
                f"🆔 کد پیگیری: #{ad_id}")
        except: pass

    # ============ تایید ریست ============
    elif data == "confirm_reset":
        if not is_super_admin(uid):
            answer_callback(cbid, "⛔ فقط سوپر ادمین!", True)
            return
        reset_all_data()
        answer_callback(cbid, "✅ ریست انجام شد.")
        edit_message(cid, mid,
            "✅ ریست کامل انجام شد!\n\n"
            "• تمام تبلیغات پاک شدند\n"
            "• تمام رسیدها پاک شدند\n"
            "• موجودی همه کاربران صفر شد\n"
            "• زیرمجموعه‌ها صفر شدند\n\n"
            "👑 موجودی سوپر ادمین دست‌نخورده ماند.",
            None)

    elif data == "cancel_reset":
        answer_callback(cbid, "❌ ریست لغو شد.")
        edit_message(cid, mid, "❌ عملیات ریست لغو شد.", kb_admin(uid))

# ==================== حلقه اصلی ====================
def main():
    init_db()
    print("🤖 ربات لینکدونی در حال اجراست...")
    print(f"👑 سوپر ادمین: {SUPER_ADMIN_ID}")
    off = None
    while True:
        try:
            ups = get_updates(off)
            if "result" in ups:
                for u in ups["result"]:
                    off = u["update_id"] + 1
                    if "message" in u:
                        handle_message(u["message"])
                    elif "callback_query" in u:
                        handle_callback(u["callback_query"])
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.5)

if __name__ == "__main__":
    start_web()
    main()
