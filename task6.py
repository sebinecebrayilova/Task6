import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Təhlükəsiz Token
TOKEN = os.getenv("8130075983:AAFU5JOhKqjABxMGVJgIzHHcUfHuHf-pVQc") or "8130075983:AAFU5JOhKqjABxMGVJgIzHHcUfHuHf-pVQc"

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Köynəkləri göstər", callback_data='get_shirts')],
        [InlineKeyboardButton("Kömək", callback_data='help')]
    ]
    await update.message.reply_text(
        "Zara məhsulları üçün bot. Aşağıdakı düymələrdən istifadə edin:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'get_shirts':
        await query.edit_message_text(text="🔍 Məhsullar axtarılır...")
        try:
            products = scrape_zara_products()
            if products:
                message = "👕 Zara Köynəkləri:\n\n" + "\n".join(
                    f"{idx}. {p['title']} - {p['price']}" 
                    for idx, p in enumerate(products[:10], 1)
                )
            else:
                message = "❌ Məhsul tapılmadı"
            await query.edit_message_text(text=message)
        except Exception as e:
            logger.error(f"Xəta: {e}")
            await query.edit_message_text(text="⚠️ Xəta baş verdi. Yenidən cəhd edin.")

def scrape_zara_products():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    service = Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    products = []
    try:
        driver.get("https://www.zara.com/ww/en/woman-shirts-l1335.html")
        for _ in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
        wait = WebDriverWait(driver, 30)
        items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-grid-product")))
        
        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, "[class*='product-name']").text
                price = item.find_element(By.CSS_SELECTOR, "[class*='price-current']").text
                products.append({"title": title.strip(), "price": price.strip()})
                logger.info(f"Found item: {title}")
            except Exception as e:
                logger.warning(f"Element tapılmadı: {e}")
                continue
                
    finally:
        driver.quit()
    
    return products

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()
