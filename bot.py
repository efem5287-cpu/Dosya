import os
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiohttp import web

# --- RENDER İÇİN WEB SUNUCUSU (Aiohttp) ---
async def handle(request):
    return web.Response(text="Bot aktif ve çalışıyor!")

async def web_server():
    app_web = web.Application()
    app_web.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- BİLGİLER ---
API_ID = 35762182
API_HASH = "126917ba7359f8cddb0780ad16e0b1ba"
BOT_TOKEN = "8822219525:AAFVve49cyixXgbTVRYKsxzQsht-NuXMaMw"
VT_API_KEY = "Dd879532277e4c9e19490a5c4e348ab1f714d03792b4046e7b017aa9d36d38aa"

CHANNEL_USERNAME = "swarovskiyeniden"
CHANNEL_LINK = "https://t.me/swarovskiyeniden"

app = Client(
    "vt_scanner_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

users_db = {}

def check_subscription(client, user_id):
    try:
        member = client.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        pass
    return False

@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if user_id not in users_db:
        users_db[user_id] = {"referred": False, "invited_count": 0}
        if len(args) > 1 and args[1].isdigit():
            referrer_id = int(args[1])
            if referrer_id != user_id and referrer_id in users_db:
                users_db[referrer_id]["invited_count"] += 1
                users_db[user_id]["referred"] = True

    is_subscribed = check_subscription(client, user_id)
    ref_data = users_db.get(user_id, {"invited_count": 0})
    has_referred = ref_data["invited_count"] > 0 or ref_data.get("referred", False)

    if not is_subscribed or not has_referred:
        bot_username = (await client.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        
        text = (
            "⚠️ **Botu kullanabilmek için şartları tamamlamalısın:**\n\n"
            f"1️⃣ Kanalımıza katıl: {CHANNEL_LINK}\n"
            "2️⃣ En az **1 kişiyi** davet et!\n\n"
            f"🔗 **Senin Davet Linkin:**\n`{ref_link}`"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Kanala Katıl", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🔄 Kontrol Et", callback_data="check_sub")]
        ])
        await message.reply_text(text, reply_markup=keyboard)
        return

    await message.reply_text("👋 **Hoş geldin!** Bot aktif. Dosyalarını ve linklerini taratabilirsin.")

@app.on_callback_query(filters.regex("check_sub"))
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    is_subscribed = check_subscription(client, user_id)
    ref_data = users_db.get(user_id, {"invited_count": 0})
    has_referred = ref_data["invited_count"] > 0 or ref_data.get("referred", False)

    if is_subscribed and has_referred:
        await callback_query.message.edit_text("✅ **Tebrikler!** Şartları sağladın, botu kullanabilirsin.")
    else:
        await callback_query.answer("❌ Şartları henüz tamamlamadın!", show_alert=True)

@app.on_message(filters.document | filters.audio | filters.video | filters.text)
async def scan_handler(client: Client, message: Message):
    if message.text and message.text.startswith("/"):
        return

    user_id = message.from_user.id
    if not check_subscription(client, user_id):
        return

    if message.document or message.video or message.audio:
        status_msg = await message.reply_text("📥 **Dosya indiriliyor ve VirusTotal'e gönderiliyor...**")
        file_path = await client.download_media(message)
        
        headers = {"x-apikey": VT_API_KEY}
        with open(file_path, "rb") as file_to_scan:
            files = {"file": (os.path.basename(file_path), file_to_scan)}
            response = requests.post("https://www.virustotal.com/api/v3/files", headers=headers, files=files)
            
        if response.status_code == 200:
            analysis_id = response.json()["data"]["id"]
            await status_msg.edit_text(f"✅ **Dosya VirusTotal'e yüklendi!**\nAnaliz ID: `{analysis_id}`")
        else:
            await status_msg.edit_text("❌ VirusTotal hatası oluştu.")
            
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    # Web sunucusunu başlat (Render uyutmasın diye)
    await web_server()
    # Botu başlat
    await app.start()
    print("Bot başarıyla başlatıldı!")
    # Botun kapanmaması için askıda tut
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    
