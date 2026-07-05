import time
import json
import os
import threading
import warnings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from groq import Groq
from flask import Flask

# --- AYARLAR ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
YAYIN_URL = os.environ.get("YAYIN_URL", "https://www.youtube.com/watch?v=5jka-H-Hvy4")

# --- FLASK (Render Port Yönetimi) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot aktif ve çalışıyor!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- BOT MANTIĞI ---
def run_bot():
    warnings.filterwarnings("ignore")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(YAYIN_URL)
    
    # Çerezleri Yükle
    try:
        with open('cookies.txt', 'r') as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(5)
    except:
        print("Çerez dosyası bulunamadı, devam ediliyor.")

    # Iframe'i Bekle ve Bağlan
    wait = WebDriverWait(driver, 20)
    chat_frame = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#chatframe")))
    driver.switch_to.frame(chat_frame)
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    okunan_mesajlar = set()
    print("Bot başarıyla chat'e odaklandı!")

    while True:
        try:
            mesajlar = driver.find_elements(By.CSS_SELECTOR, "yt-live-chat-text-message-renderer")
            for el in mesajlar:
                msg_id = el.get_attribute("id")
                if msg_id in okunan_mesajlar: continue
                
                kullanici = el.find_element(By.CSS_SELECTOR, "#author-name").text
                mesaj_metni = el.find_element(By.CSS_SELECTOR, "#message").text
                okunan_mesajlar.add(msg_id)
                
                if mesaj_metni.startswith("!bot"):
                    soru = mesaj_metni.replace("!bot", "").strip()
                    if soru:
                        response = groq_client.chat.completions.create(
                            messages=[{"role": "user", "content": soru}],
                            model="llama-3.1-8b-instant"
                        )
                        cevap = f"@{kullanici} {response.choices[0].message.content[:190]}"
                        kutusu = driver.find_element(By.CSS_SELECTOR, "#input.yt-live-chat-text-input-field-renderer")
                        kutusu.send_keys(cevap)
                        kutusu.send_keys(Keys.ENTER)
                        time.sleep(2)
        except Exception as e:
            print(f"Döngü hatası: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_flask()
