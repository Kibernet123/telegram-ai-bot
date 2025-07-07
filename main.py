import os
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

def ask_ai(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
        r.raise_for_status()
        result = r.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("Error in ask_ai:", e)
        return "Виникла помилка при зверненні до AI."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Напиши мені щось — я відповім :)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    response = ask_ai(update.message.text)
    await update.message.reply_text(response)

async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.update_queue.put(update)
    return web.Response()

async def on_startup(app):
    await bot_app.bot.set_webhook(url=WEBHOOK_URL + "/webhook")
    print("Webhook встановлено:", WEBHOOK_URL + "/webhook")

async def main():
    global bot_app
    bot_app = Application.builder().token(BOT_TOKEN).build()

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    web_app = web.Application()
    web_app.router.add_post("/webhook", webhook_handler)
    web_app.on_startup.append(on_startup)

    await bot_app.initialize()
    await bot_app.start()

    port = int(os.getenv("PORT", 10000))
    print(f"Starting server on port {port}...")
    await web._run_app(web_app, host="0.0.0.0", port=port)

    await bot_app.stop()

if __name__ == "__main__":
    asyncio.run(main())
