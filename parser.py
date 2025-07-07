# parser.py (Версия 5.6 для Wolt - Возвращена плавная прокрутка)

import os
import time
import random
import csv
import requests
import sys
import shutil
from seleniumwire import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# --- КОНФИГУРАЦИЯ ---
START_URL = 'https://wolt.com/az/aze/baku/venue/araz-yasamal-3-superstore-f'
for arg in sys.argv[1:]:
    if not arg.startswith('--'):
        START_URL = arg
        break

print(f"Информация: Используется ссылка для парсинга: {START_URL}")

DEBUG_DIR = 'debug_files'
PHOTO_DIR = 'photos'
CSV_PATH = 'bazarstore_products.csv'
LIMIT = 100000
USE_PROXY_FLAG = '--use-proxy' in sys.argv

# --- ОЧИСТКА ---
print("Очистка старых файлов...")
if os.path.exists(CSV_PATH): os.remove(CSV_PATH)
if os.path.exists(PHOTO_DIR): shutil.rmtree(PHOTO_DIR)
if os.path.exists(DEBUG_DIR): shutil.rmtree(DEBUG_DIR)
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)
print("Очистка завершена.")

# --- УТИЛИТЫ И ГЛАВНЫЙ ОБРАБОТЧИК ---
USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15"]
session_user_agent = random.choice(USER_AGENTS)

def handle_all_popups(driver, timeout=3):
    """
    Универсальный обработчик для всех известных всплывающих окон.
    """
    # 1. Модальное окно товара
    try:
        wait = WebDriverWait(driver, timeout)
        close_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-test-id='modal-close-button']")))
        print("! ОБНАРУЖЕНО модальное окно товара. Принудительно закрываем...")
        driver.execute_script("arguments[0].click();", close_button)
        time.sleep(random.uniform(1, 1.5))
    except TimeoutException:
        pass

    # 2. Окно с предложением уведомлений ("Icazə verin")
    try:
        wait = WebDriverWait(driver, timeout)
        notifications_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test-id='enable-notifications-button']")))
        print("! ОБНАРУЖЕНО окно с уведомлениями. Нажимаем 'Icazə verin'...")
        notifications_button.click()
        time.sleep(random.uniform(1, 1.5))
    except TimeoutException:
        pass

    # 3. Окно cookie
    try:
        wait = WebDriverWait(driver, timeout)
        cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test-id='allow-button']")))
        print("! ОБНАРУЖЕНО окно cookie. Нажимаем 'Принять'...")
        cookie_button.click()
        time.sleep(random.uniform(1, 1.5))
    except TimeoutException:
        pass

def save_debug_info(driver, reason):
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename_base = os.path.join(DEBUG_DIR, f"{timestamp}_{reason}")
        screenshot_path = f"{filename_base}.png"
        html_path = f"{filename_base}.html"
        driver.save_screenshot(screenshot_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"ОТЛАДКА: Сохранены файлы для анализа: {screenshot_path} и {html_path}")
    except Exception as e:
        print(f"ОТЛАДКА: Не удалось сохранить файлы отладки по причине '{reason}': {e}")

def human_mouse_move(driver):
    try:
        width = driver.execute_script("return window.innerWidth;")
        height = driver.execute_script("return window.innerHeight;")
        actions = ActionChains(driver)
        for _ in range(random.randint(1, 3)):
            x_offset = random.randint(int(-width/4), int(width/4))
            y_offset = random.randint(int(-height/4), int(height/4))
            actions.move_by_offset(x_offset, y_offset)
            actions.perform()
            actions = ActionChains(driver)
            time.sleep(random.uniform(0.1, 0.3))
    except Exception:
        pass

def random_wait(action_counter=0, type_of_action="item_process", base_min=0.5, base_max=1.5):
    base_t_min, base_t_max = base_min, base_max
    if type_of_action == "scroll": base_t_min, base_t_max = 2.0, 3.0
    elif type_of_action == "item_process":
        if action_counter > 0 and action_counter % random.randint(55, 85) == 0:
            coffee_break = random.uniform(45, 70)
            print(f"Имитация 'кофе-брейка' на {int(coffee_break)} секунд после {action_counter} товаров...")
            base_t_max += coffee_break
        elif action_counter > 0 and action_counter % random.randint(15, 25) == 0:
            smoke_break = random.uniform(10, 20)
            print(f"Имитация 'перекура' на {int(smoke_break)} секунд после {action_counter} товаров...")
            base_t_max += smoke_break
    sleep_duration = random.uniform(base_t_min, base_t_max)
    if sleep_duration > 3: print(f"Пауза на {sleep_duration:.1f} секунд...")
    time.sleep(sleep_duration)

def download_images(products_data, proxies):
    print(f"\nНачинаем скачивание {len(products_data)} изображений...")
    headers = {"User-Agent": session_user_agent, "Referer": START_URL}
    for i, product in enumerate(products_data):
        photo_url = product.get('photo_url_full')
        if not photo_url: continue
        try:
            photo_filename_base = photo_url.split('/')[-1].split('?')[0]
            valid_chars = "-_.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            photo_filename_base = ''.join(c for c in photo_filename_base if c in valid_chars)
            if not photo_filename_base or photo_filename_base == '.': photo_filename_base = f"product_{i + 1}_photo.jpg"
            if not os.path.splitext(photo_filename_base)[1]: photo_filename_base += ".jpg"
            local_photo_filepath = os.path.join(PHOTO_DIR, photo_filename_base)
            r_photo = requests.get(photo_url, headers=headers, timeout=25, stream=True, proxies=proxies)
            if r_photo.status_code == 200:
                with open(local_photo_filepath, 'wb') as f_photo: shutil.copyfileobj(r_photo.raw, f_photo)
                product['photo_path'] = local_photo_filepath
                print(f"[{i+1}/{len(products_data)}] Скачано: {photo_filename_base}")
            else: print(f"Не удалось скачать фото {photo_url} (Код {r_photo.status_code})")
        except Exception as e: print(f"Ошибка скачивания фото {photo_url}: {e}")
        time.sleep(random.uniform(0.1, 0.3))

# --- Инициализация WebDriver и прокси ---
driver = None
proxies_for_requests = {}
selenium_wire_options = {}
if USE_PROXY_FLAG:
    print("Информация: Используется флаг --use-proxy. Настраиваем прокси.")
    PROXY_HOST = "brd.superproxy.io"; PROXY_PORT = 33335
    PROXY_USER = "brd-customer-hl_335cad1c-zone-datacenter_proxy1"; PROXY_PASS = "fcxp876yscbo"
    proxy_string_for_requests = f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
    proxies_for_requests = {'http': proxy_string_for_requests, 'https': proxy_string_for_requests}
    session_id = random.randint(10000, 999999)
    proxy_user_with_session = f'{PROXY_USER}-session-{session_id}'
    selenium_wire_options = {
        'proxy': {
            'http': f'http://{proxy_user_with_session}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
            'https': f'https://{proxy_user_with_session}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
            'no_proxy': 'localhost,127.0.0.1'
        }
    }
else:
    print("Информация: Запуск без прокси.")
chrome_options = Options()
# chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument(f"user-agent={session_user_agent}")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)


try:
    print("Запускаем браузер...")
    driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=selenium_wire_options)
    
    print("Проверяем IP-адрес браузера...")
    driver.set_page_load_timeout(45)
    driver.get('https://httpbin.org/ip')
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
    ip_info_element = driver.find_element(By.TAG_NAME, 'pre')
    ip_address_json = ip_info_element.text
    print(f"УСПЕХ! Браузер работает. IP АДРЕС: {ip_address_json.strip()}")
    
    driver.set_page_load_timeout(60)

    # --- ОСНОВНАЯ ЛОГИКА ---
    print(f"\nЗагружаем страницу: {START_URL}")
    driver.get(START_URL)
    WebDriverWait(driver, 45).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='ItemCard']")))
    print("Страница загружена.")

    print("\n--- Первичная очистка страницы от всплывающих окон ---")
    handle_all_popups(driver, timeout=5)

    print("\n--- Начинаем инкрементальный парсинг с человеческим поведением ---")
    processed_urls = set()
    products_data = []
    stale_scrolls = 0

    while stale_scrolls < 8:
        print("\n--- Проверка на всплывающие окна перед сбором данных ---")
        handle_all_popups(driver)

        count_before_scroll = len(processed_urls)
        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-test-id='ItemCard']")

        for card in cards:
            try:
                card_html = card.get_attribute('outerHTML')
                soup = BeautifulSoup(card_html, 'html.parser')
                link_tag = soup.find('a', attrs={'data-test-id': 'CardLinkButton'})
                if not link_tag: continue
                product_url = 'https://wolt.com' + link_tag['href']
                if product_url in processed_urls: continue
                name_tag = soup.find('h3', attrs={'data-test-id': 'ImageCentricProductCard.Title'})
                name = name_tag.get_text(strip=True) if name_tag else "N/A"
                price_new_tag = soup.find('span', {'aria-label': lambda x: x and (x.startswith('Endirimli qiymət') or x.startswith('Qiymət'))})
                price_new = price_new_tag.get_text(strip=True) if price_new_tag else ""
                price_old_tag = soup.find('s', {'aria-label': lambda x: x and x.startswith('Köhnə qiymət')})
                price_old = price_old_tag.get_text(strip=True) if price_old_tag else ""
                img_tag = soup.find('img')
                photo_url_full = img_tag['src'] if img_tag and img_tag.has_attr('src') and 'placeholder' not in img_tag['src'] else ""
                product_info = {'name': name, 'price_new': price_new, 'price_old': price_old, 'product_url': product_url, 'photo_url_full': photo_url_full, 'photo_path': ''}
                products_data.append(product_info)
                processed_urls.add(product_url)
                print(f"[{len(processed_urls)}] Спарсен: {name}")
                random_wait(action_counter=len(processed_urls), type_of_action="item_process")
            except Exception as e:
                print(f"Предупреждение: Пропущена карточка из-за ошибки: {e}")
                continue

        # --- ИЗМЕНЕНИЕ: ВОЗВРАЩЕНА СТАРАЯ ЛОГИКА ПРОКРУТКИ ---
        print("...плавная прокрутка страницы до конца...")
        current_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            human_mouse_move(driver)
            time.sleep(random.uniform(1.5, 2.5))
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == current_height:
                break
            current_height = new_height
        print("...достигнут конец текущего списка...")
        # --- КОНЕЦ БЛОКА ПРОКРУТКИ ---
        
        random_wait(type_of_action="scroll")

        if len(processed_urls) == count_before_scroll:
            stale_scrolls += 1
            print(f"Новых товаров не найдено. Попытка {stale_scrolls}/8...")
            save_debug_info(driver, f"stale_scroll_{stale_scrolls}")
        else:
            stale_scrolls = 0

        if len(processed_urls) >= LIMIT:
            print(f"Достигнут лимит в {LIMIT} товаров.")
            break

    print("\nПарсинг завершен. Сохраняем финальное состояние страницы для анализа...")
    save_debug_info(driver, "final_state")
    print(f"\nВсего найдено уникальных товаров: {len(products_data)}")

    if products_data:
        download_images(products_data, proxies_for_requests)

    print(f"\nЗапись {len(products_data)} товаров в {CSV_PATH}...")
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'price_new', 'price_old', 'photo_path', 'product_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for product in products_data:
            product.pop('photo_url_full', None)
            writer.writerow(product)
    print("Данные успешно сохранены.")

except Exception as e:
    print(f"КРИТИЧЕСКАЯ ОШИБКА в основном блоке: {e}")
    if driver:
        save_debug_info(driver, "critical_error")

finally:
    if driver:
        driver.quit()
        print("\nБраузер закрыт.")