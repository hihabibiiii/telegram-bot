import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters
)

import urllib.parse

from menu import MENU
from order_manager import get_order, reset_order

# ================= CONFIG =================

BOT_TOKEN = os.environ.get("BOT_TOKEN")   
OWNER_CHAT_ID = 5618584289

UPI_ID = "habib@ybl"
MERCHANT_NAME = "Habib Biryani "

# ================= UPI LINK =================

def generate_upi_link(amount, note="Food Order"):
    params = {
        "pa": UPI_ID,
        "pn": MERCHANT_NAME,
        "am": str(amount),
        "cu": "INR",
        "tn": note
    }
    return "upi://pay?" + urllib.parse.urlencode(params)

# ================= BOT HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        msg = update.message.text.strip()
        msg_l = msg.lower()
        order = get_order(user_id)

        print("📩", user_id, msg_l, order["stage"])

        # 1️⃣ HI / START → MENU AUTO
        if msg_l in ["hi", "hello", "/start"] and order["stage"] == "START":
            menu_text = "🍗 MENU:\n"
            for item, price in MENU.items():
                menu_text += f"{item.title()} - ₹{price}\n"
            menu_text += "\n👉 Aap kya order karna chahenge?"
            order["stage"] = "ITEM"
            await update.message.reply_text(menu_text)
            return

        # 2️⃣ ITEM SELECT
        if order["stage"] == "ITEM":
            for item in MENU:
                if item in msg_l:
                    order["current_item"] = item
                    order["stage"] = "QTY"
                    await update.message.reply_text(
                        f"👍 {item.title()} ki quantity batayein"
                    )
                    return
            await update.message.reply_text("❗ Menu se item choose karein")
            return

        # 3️⃣ QUANTITY
        if order["stage"] == "QTY":
            if msg_l.isdigit() and int(msg_l) > 0:
                order["items"].append({
                    "item": order["current_item"],
                    "qty": int(msg_l)
                })
                order.pop("current_item", None)
                order["stage"] = "ADD_MORE"
                await update.message.reply_text(
                    "➕ Kya aap aur kuch add karna chahenge? (haan / nahi)"
                )
                return
            await update.message.reply_text("❗ Sirf number likhein (jaise: 2)")
            return

        # 4️⃣ ADD MORE LOOP
        if order["stage"] == "ADD_MORE":
            if msg_l in ["haan", "ha", "yes"]:
                menu_text = "🍗 MENU:\n"
                for item, price in MENU.items():
                    menu_text += f"{item.title()} - ₹{price}\n"
                menu_text += "\n👉 Aur kya order karna chahenge?"
                order["stage"] = "ITEM"
                await update.message.reply_text(menu_text)
                return

            if msg_l in ["nahi", "no"]:
                order["stage"] = "NAME"
                await update.message.reply_text("👤 Aapka naam batayein")
                return

            await update.message.reply_text("❓ Sirf 'haan' ya 'nahi' likhein")
            return

        # 5️⃣ NAME
        if order["stage"] == "NAME":
            order["name"] = msg
            order["stage"] = "PHONE"
            await update.message.reply_text("📱 Apna 10-digit mobile number batayein")
            return

        # 6️⃣ PHONE
        if order["stage"] == "PHONE":
            if msg_l.isdigit() and len(msg_l) == 10:
                order["phone"] = msg_l
                order["stage"] = "ADDRESS"
                await update.message.reply_text("📍 Delivery address batayein")
                return
            await update.message.reply_text("❗ Valid 10-digit number likhein")
            return

        # 7️⃣ ADDRESS → PAYMENT OPTIONS
        if order["stage"] == "ADDRESS":
            order["address"] = msg
            order["stage"] = "PAYMENT"

            total = 0
            items_text = ""
            for i in order["items"]:
                price = MENU[i["item"]] * i["qty"]
                total += price
                items_text += f"{i['item'].title()} x {i['qty']}\n"

            order["total"] = total
            order["items_text"] = items_text

            await update.message.reply_text(
                f"""🧾 Order Summary

🍗 Items:
{items_text}
💰 Total: ₹{total}
📍 Address: {order['address']}

💳 Payment Options:
1️⃣ UPI
2️⃣ QR
3️⃣ Cash on Delivery

👉 Reply karein: upi / qr / cod
"""
            )
            return

        # 8️⃣ PAYMENT HANDLER
        if order["stage"] == "PAYMENT":
            choice = msg_l

            if choice == "upi":
                upi_link = generate_upi_link(order["total"], f"Order by {order['name']}")
                await update.message.reply_text(
                    f"""💳 UPI Payment

UPI ID: {UPI_ID}
👉 Pay here:
{upi_link}

📸 Payment ke baad screenshot bhej sakte hain
"""
                )

            elif choice == "qr":
                await context.bot.send_photo(
                    chat_id=update.message.chat.id,
                    photo=open("upi_qr.jpeg", "rb"),
                    caption=f"""📷 Scan QR to Pay

UPI ID: {UPI_ID}
Amount: ₹{order['total']}
"""
                )

            elif choice == "cod":
                await update.message.reply_text(
                    "💵 Cash on Delivery selected\n🚚 Delivery ke time payment kar sakte hain"
                )

            else:
                await update.message.reply_text("❗ Reply karein: upi / qr / cod")
                return

            # OWNER NOTIFICATION
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=f"""📦 NEW ORDER RECEIVED

👤 Name: {order['name']}
🍗 Items:
{order['items_text']}
📱 Phone: {order['phone']}
💰 Amount: ₹{order['total']}
📍 Address: {order['address']}
💳 Payment: {choice.upper()}
"""
            )

            reset_order(user_id)
            return

    except Exception as e:
        print("❌ ERROR:", e)
        try:
            await update.message.reply_text(
                "⚠️ Network issue, please thodi der baad try karein 🙏"
            )
        except:
            pass

# ================= RUN BOT =================

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Biryani AI Bot started...")
    app.run_polling()
