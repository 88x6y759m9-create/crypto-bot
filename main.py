import os
import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

alerts = {}

def get_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    try:
        response = requests.get(url).json()
        if coin in response:
            return response[coin]["usd"]
    except:
        return None
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚀 Крипто бот запущен!\n\n"
        "Команды:\n"
        "/price bitcoin\n"
        "/price ethereum\n"
        "/alert bitcoin 50000\n"
        "/alerts"
    )
    await update.message.reply_text(text)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: /price bitcoin")
        return

    coin = context.args[0].lower()
    current_price = get_price(coin)

    if current_price:
        await update.message.reply_text(f"💰 {coin.upper()} = ${current_price}")
    else:
        await update.message.reply_text("❌ Монета не найдена")

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Пример: /alert bitcoin 50000")
        return

    coin = context.args[0].lower()

    try:
        target_price = float(context.args[1])
    except:
        await update.message.reply_text("Цена должна быть числом")
        return

    chat_id = update.effective_chat.id

    if chat_id not in alerts:
        alerts[chat_id] = []

    alerts[chat_id].append((coin, target_price))

    await update.message.reply_text(
        f"🔔 Алерт установлен!\n{coin.upper()} ≥ ${target_price}"
    )

async def show_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in alerts or not alerts[chat_id]:
        await update.message.reply_text("Нет активных алертов")
        return

    text = "📌 Твои алерты:\n"
    for coin, price_value in alerts[chat_id]:
        text += f"- {coin.upper()} ≥ ${price_value}\n"

    await update.message.reply_text(text)

async def check_prices(app):
    while True:
        for chat_id in list(alerts.keys()):
            user_alerts = alerts.get(chat_id, [])

            for coin, target_price in user_alerts[:]:
                current_price = get_price(coin)

                if current_price and current_price >= target_price:
                    await app.bot.send_message(
                        chat_id,
                        f"🚀 {coin.upper()} достиг ${current_price}!"
                    )
                    alerts[chat_id].remove((coin, target_price))

        await asyncio.sleep(60)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("alerts", show_alerts))

    app.create_task(check_prices(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
