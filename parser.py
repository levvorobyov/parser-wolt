# parser.py (Полная исправленная версия)

import os
import time
import random
import csv
import requests
import sys
from seleniumwire import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import shutil

# --- Определение путей и констант ---
START_URL = 'https://wolt.com/az/aze/baku/venue/araz-yasamal-3-superstore-f/items/saqqz-95' # Ссылка по умолчанию
for arg in sys.argv[1:]:
    if not arg.startswith('--'):
        START_URL = arg
        break

print(f"Информация: Используется ссылка для парсинга: {START_URL}")

PHOTO_DIR = 'photos'
CSV_PATH = 'bazarstore_products.csv'
LIMIT = 1700
MAX_RETRIES = 1

# --- ПРОВЕРКА ФЛАГА ИСПОЛЬЗОВАНИЯ ПРОКСИ ---
USE_PROXY_FLAG = '--use-proxy' in sys.argv

# --- БЛОК ОЧИСТКИ СТАРЫХ ФАЙЛОВ ---
print("Очистка старых файлов перед запуском...")
DEBUG_FILES = ["goods_initial.png", "goods_initial.html", "error_goods_initial.png", "error_goods_initial.html", "goods_final_before_parse.png", "goods_final_before_parse.html", "proxy_error.png", "proxy_error.html", "goods_page_load_error.png", "goods_page_load_error.html"]
if os.path.exists(CSV_PATH):
    try:
        os.remove(CSV_PATH)
        print(f"Файл '{CSV_PATH}' удален.")
    except OSError as e:
        print(f"Ошибка при удалении файла {CSV_PATH}: {e}")
if os.path.exists(PHOTO_DIR):
    try:
        shutil.rmtree(PHOTO_DIR)
        print(f"Папка '{PHOTO_DIR}' и ее содержимое удалены.")
    except OSError as e:
        print(f"Ошибка при удалении папки {PHOTO_DIR}: {e}")
for f in DEBUG_FILES:
    if os.path.exists(f):
        try:
            os.remove(f)
        except OSError as e:
            pass
print("Очистка завершена.")


USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"]
session_user_agent = random.choice(USER_AGENTS)
os.makedirs(PHOTO_DIR, exist_ok=True)

def human_mouse_move(driver):
    width = driver.execute_script("return window.innerWidth")
    height = driver.execute_script("return window.innerHeight")
    actions = ActionChains(driver)
    for _ in range(random.randint(2, 5)):
        try:
            x_offset = random.randint(-int(width/4), int(width/4))
            y_offset = random.randint(-int(height/4), int(height/4))
            actions.move_by_offset(x_offset, y_offset)
            actions.perform()
            actions = ActionChains(driver)
        except Exception:
            pass
        time.sleep(random.uniform(0.2, 0.6))

def human_scroll(driver):
    print("Плавно скроллим страницу...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(random.randint(3, 6)):
        scroll_increment = random.randint(int(driver.execute_script("return window.innerHeight")*0.4), int(driver.execute_script("return window.innerHeight")*0.9))
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        human_mouse_move(driver)
        time.sleep(random.uniform(0.7, 2.0))
        new_height = driver.execute_script("return document.body.scrollHeight")
        current_scroll = driver.execute_script("return window.pageYOffset + window.innerHeight")
        if new_height == last_height and current_scroll >= new_height - 10:
            break
        last_height = new_height

    if random.random() < 0.4:
        print("Немного скроллим вверх...")
        driver.execute_script(f"window.scrollBy(0, -{random.randint(250, 600)});")
        human_mouse_move(driver)
        time.sleep(random.uniform(0.5, 1.2))

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(0.8, 1.8))


def random_wait(action_counter=0, type_of_action="item", base_min=None, base_max=None):
    if base_min is not None and base_max is not None:
        base_t_min, base_t_max = base_min, base_max
    else:
        base_t_min, base_t_max = 0.5, 1.5
        if type_of_action == "page_click":
            base_t_min, base_t_max = 4.0, 10.0
            if action_counter % random.randint(7, 12) == 0:
                extra_pause = random.uniform(15, 45)
                print(f"Длительная пауза после загрузки {action_counter} страниц: {int(extra_pause)} сек.")
                base_t_max += extra_pause
        elif type_of_action == "item_process":
            if action_counter % random.randint(45, 75) == 0:
                coffee_break = random.uniform(60, 90)
                print(f"Имитация 'кофе-брейка' на {int(coffee_break)} секунд после {action_counter} товаров...")
                base_t_max += coffee_break
            elif action_counter % random.randint(15, 25) == 0:
                smoke_break = random.uniform(10, 30)
                print(f"Имитация 'перекура' на {int(smoke_break)} секунд после {action_counter} товаров...")
                base_t_max += smoke_break
            elif random.random() < 0.1:
                 base_t_max += random.uniform(2, 5)

    sleep_duration = random.uniform(base_t_min, base_t_max)

    if sleep_duration > 3:
        print(f"Пауза на {sleep_duration:.1f} секунд...")
    time.sleep(sleep_duration)


# --- Инициализация переменных для драйвера и прокси ---
driver = None
selenium_wire_options = {}
proxies_for_requests = {}

# --- НАСТРОЙКИ ПРОКСИ (если флаг --use-proxy передан) ---
if USE_PROXY_FLAG:
    PROXY_HOST = "brd.superproxy.io"
    PROXY_PORT = 33335
    PROXY_USER = "brd-customer-hl_335cad1c-zone-datacenter_proxy1"
    PROXY_PASS = "fcxp876yscbo"

    proxy_string_for_requests = f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
    proxies_for_requests = {
       'http': proxy_string_for_requests,
       'https': proxy_string_for_requests,
    }


# ######################################################################
# ### НАЧАЛО БЛОКА ПОДКЛЮЧЕНИЯ ###
# ######################################################################

retry_attempts = MAX_RETRIES if USE_PROXY_FLAG else 1

for attempt in range(retry_attempts):
    if USE_PROXY_FLAG:
        print(f"\nПопытка №{attempt + 1} из {retry_attempts} для подключения к прокси...")
        session_id = random.randint(10000, 999999)
        proxy_user_with_session = f'{PROXY_USER}-session-{session_id}'

        selenium_wire_options = {
            'proxy': {
                'http': f'http://{proxy_user_with_session}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
                'https': f'https://{proxy_user_with_session}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
                'no_proxy': 'localhost,127.0.0.1'
            }
        }

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-agent={session_user_agent}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--silent')
    chrome_options.add_argument('--disable-logging')

    if USE_PROXY_FLAG:
        print(f"Информация: Запускаем браузер с прокси, сессия: {session_id}")
    else:
        print("Информация: Запускаем браузер без прокси.")

    driver = webdriver.Chrome(
        options=chrome_options,
        seleniumwire_options=selenium_wire_options
    )

    try:
        driver.set_page_load_timeout(30)
        driver.get('https://httpbin.org/ip')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
        ip_info_element = driver.find_element(By.TAG_NAME, 'pre')
        ip_address_json = ip_info_element.text
        print(f"УСПЕХ! Браузер работает. IP АДРЕС: {ip_address_json.strip()}")
        break
    except Exception as e:
        print(f"ПРЕДУПРЕЖДЕНИЕ: Попытка №{attempt + 1} не удалась. Ошибка: {e.__class__.__name__}")
        if attempt < retry_attempts - 1:
            print("Закрываю браузер и пробую снова с новым IP...")
            driver.quit()
            driver = None
            time.sleep(5)
        else:
            print("!!! КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить рабочий прокси после нескольких попыток.")
            if driver: driver.quit()
            driver = None

if not driver:
    print("!!! Не удалось инициализировать браузер. Завершение работы.")
    sys.exit(1)

# ######################################################################
# ### КОНЕЦ БЛОКА ПОДКЛЮЧЕНИЯ ###
# ######################################################################


print("\n--- Основной парсинг ---")
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
driver.set_page_load_timeout(60)

# ######################################################################
# ### НАЧАЛО БЛОКА: ПОВТОРНЫЕ ПОПЫТКИ ЗАГРУЗКИ СТРАНИЦЫ ###
# ######################################################################
page_loaded_successfully = False
for page_load_attempt in range(MAX_RETRIES):
    try:
        print(f"Попытка загрузки основной страницы №{page_load_attempt + 1}...")
        driver.get(START_URL)

        # Ожидаем главный контейнер товаров, актуальный для bazarstore.az
        WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.grid__item"))
        )
        print("Основная страница успешно загружена, товары видны.")
        page_loaded_successfully = True
        break

    except (TimeoutException, WebDriverException) as e:
        print(f"ПРЕДУПРЕЖДЕНИЕ: Ошибка при загрузке страницы (попытка {page_load_attempt + 1}): {e.__class__.__name__}")
        if page_load_attempt < MAX_RETRIES - 1:
            print("Пауза 5 секунд и повторная попытка...")
            time.sleep(5)
        else:
            print("!!! КРИТИЧЕСКАЯ ОШИБКА: Не удалось загрузить основную страницу после нескольких попыток.")

if not page_loaded_successfully:
    driver.save_screenshot("bazarstore_page_load_error.png")
    with open("bazarstore_page_load_error.html", "w", encoding="utf-8") as f: f.write(driver.page_source)
    print("Сохранены файлы отладки. Завершение работы.")
    driver.quit()
    sys.exit(1)
# ######################################################################
# ### КОНЕЦ БЛОКА ###
# ######################################################################


print("Ожидаем и обрабатываем модальные окна (если они появятся)...")
time.sleep(random.uniform(3,6))

# Защитный блок для обработки модальных окон, если они появятся
try:
    lagv_et_button_xpath = '//button[normalize-space()="Ləğv et"]'
    WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.XPATH, lagv_et_button_xpath))).click()
    print('Кнопка "Ləğv et" нажата.')
    time.sleep(random.uniform(0.5, 1.5))
except: pass

try:
    city_modal_container_xpath = "//div[@data-v-73d529dc and contains(@class, 'fixed') and .//p[normalize-space()='Şəhərinizi seçin']]"
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, city_modal_container_xpath)))
    close_button_xpath_city = f"{city_modal_container_xpath}//i[contains(@class, 'i-close')]"
    city_modal_close_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, close_button_xpath_city)))
    driver.execute_script("arguments[0].click();", city_modal_close_button)
    time.sleep(random.uniform(1.5, 2.5))
    WebDriverWait(driver, 7).until_not(EC.visibility_of_element_located((By.XPATH, city_modal_container_xpath)))
except: pass

print("Обработка модальных окон завершена.")
random_wait()

# --- НАЧАЛО НОВОГО БЛОКА ПАГИНАЦИИ ---
print("Грузим страницы (жмём 'Daha Çox Yükləyin')...")
clicks_performed_show_more = 0
product_selector = "li.grid__item"

while True:
    # Запоминаем текущее количество товаров
    try:
        current_product_count = len(driver.find_elements(By.CSS_SELECTOR, product_selector))
    except Exception:
        current_product_count = 0

    human_scroll(driver)
    
    try:
        # Ищем кнопку "Загрузить еще"
        button_show_more_xpath = "//button[contains(., 'Daha Çox Yükləyin')]"
        button = WebDriverWait(driver, 25).until(
            EC.element_to_be_clickable((By.XPATH, button_show_more_xpath))
        )
        
        # Используем стандартный клик, он надежнее
        button.click()
        clicks_performed_show_more += 1
        print(f"Кликнули 'Daha Çox Yükləyin' ({clicks_performed_show_more}-й раз).")

        # Ждем, пока количество товаров на странице не увеличится
        print("Ожидаем загрузки новых товаров...")
        WebDriverWait(driver, 20).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, product_selector)) > current_product_count
        )
        new_product_count = len(driver.find_elements(By.CSS_SELECTOR, product_selector))
        print(f"Успех! Товары загружены. Было: {current_product_count}, стало: {new_product_count}.")

    except TimeoutException:
        print(f"Кнопка 'Daha Çox Yükləyin' не найдена или новые товары не загрузились. Завершаем загрузку.")
        break
    except Exception as e:
        print(f"Произошла непредвиденная ошибка при клике на кнопку (после {clicks_performed_show_more} кликов): {e}")
        break

print(f"Завершена загрузка дополнительных страниц. Всего кликов: {clicks_performed_show_more}.")
# --- КОНЕЦ НОВОГО БЛОКА ПАГИНАЦИИ ---

human_scroll(driver)
random_wait()

print("Сохраняем финальный скриншот и HTML перед парсингом...")
driver.save_screenshot("bazarstore_goods_final_before_parse.png")
with open("bazarstore_goods_final_before_parse.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
print("Финальный скриншот и HTML сохранены.")


# --- ИСПРАВЛЕННЫЙ БЛОК ПАРСИНГА ---

print("Парсинг финального HTML-кода...")
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Ищем контейнеры товаров по правильному классу 'grid__item'
cards = soup.select('li.grid__item')
print(f"Найдено карточек товаров (grid__item): {len(cards)}")

if not cards:
    print("КРИТИЧЕСКАЯ ОШИБКА: Не найдено ни одной карточки товара (grid__item)!")
    driver.quit()
    sys.exit(1)

with open(CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['name', 'price_new', 'price_old', 'photo_path', 'product_url']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    product_counter = 0

    print(f"Начинаем парсинг {len(cards)} найденных элементов...")

    for card in cards:
        if product_counter >= LIMIT:
            print(f"Достигнут лимит в {LIMIT} товаров. Останавливаем парсинг.")
            break

        # Пропускаем пустые или нерелевантные элементы, если они попались
        if not card.find('a', class_='full-unstyled-link'):
            continue

        # Извлекаем ссылку на товар и название из одного места
        link_tag = card.find('a', class_='full-unstyled-link')
        product_url_extracted = 'https://bazarstore.az' + link_tag['href']
        
        name_tag = card.find(class_='card-information__text')
        name = name_tag.get_text(strip=True) if name_tag else "N/A"

        # Извлекаем новую и старую цену по их реальным классам
        price_new_tag = card.select_one('.price-item--sale') or card.select_one('.price-item--regular')
        price_old_tag = card.select_one('s.price-item--regular')
        
        price_new = price_new_tag.get_text(strip=True) if price_new_tag else ""
        price_old = price_old_tag.get_text(strip=True) if price_old_tag else ""
        
        # Извлекаем фото
        img_tag = card.find('img')
        photo_url_full = ''
        if img_tag and img_tag.has_attr('src'):
            photo_url_full = 'https:' + img_tag['src']

        photo_path_local = ''
        if photo_url_full:
            try:
                photo_filename_base = photo_url_full.split('/')[-1].split('?')[0]
                valid_chars = "-_.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                photo_filename_base = ''.join(c for c in photo_filename_base if c in valid_chars)
                if not photo_filename_base or photo_filename_base == '.':
                     photo_filename_base = f"product_{product_counter + 1}_photo.jpg"
                if not os.path.splitext(photo_filename_base)[1]:
                    photo_filename_base += ".jpg"

                local_photo_filepath = os.path.join(PHOTO_DIR, photo_filename_base)
                headers_for_photo = {"User-Agent": session_user_agent, "Referer": START_URL}
                r_photo = requests.get(photo_url_full, headers=headers_for_photo, timeout=25, stream=True, proxies=proxies_for_requests)
                if r_photo.status_code == 200:
                    with open(local_photo_filepath, 'wb') as f_photo:
                        r_photo.raw.decode_content = True
                        shutil.copyfileobj(r_photo.raw, f_photo)
                    photo_path_local = local_photo_filepath
                else:
                    print(f"Не удалось скачать фото {photo_url_full} (Код {r_photo.status_code}) для товара {name}")
            except Exception as ex_photo:
                print(f"Ошибка скачивания фото {photo_url_full} для товара {name}: {ex_photo}")

        writer.writerow({
            'name': name,
            'price_new': price_new,
            'price_old': price_old,
            'photo_path': photo_path_local,
            'product_url': product_url_extracted
        })
        product_counter += 1
        print(f"[{product_counter}/{LIMIT if LIMIT else len(cards)}] {name} | Цена: {price_new} (старая: {price_old}) | Фото: {photo_path_local if photo_path_local else 'Нет фото'}")

        random_wait(action_counter=product_counter, type_of_action="item_process")

if product_counter > 0:
    print("Симуляция финальных действий перед закрытием...")
    human_scroll(driver)
    random_wait(base_min=10, base_max=25)

print(f"Готово! Данные {product_counter} товаров сохранены в {CSV_PATH}")
driver.quit()