# parser.py (Новая версия-оркестратор)

import sys
import time
import random
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

# Импортируем наши собственные модули
import config
from utils import cleanup_previous_run, save_debug_info, handle_all_popups, human_mouse_move, random_wait
from webdriver_factory import create_driver
from data_processor import download_images, write_to_csv, get_proxies_for_requests

# !!! НОВОЕ: Настройки для повторной проверки IP
IP_CHECK_RETRIES = 6
IP_CHECK_DELAY_SECONDS = 20

def main():
    """Основная логика парсера."""
    
    # Получаем URL и флаг прокси из аргументов командной строки
    start_url = 'https://wolt.com/az/aze/baku/venue/araz-yasamal-3-superstore-f' # URL по умолчанию
    for arg in sys.argv[1:]:
        if not arg.startswith('--'):
            start_url = arg
            break
    use_proxy_flag = '--use-proxy' in sys.argv
    print(f"Информация: Используется ссылка для парсинга: {start_url}")

    # 1. Подготовка
    cleanup_previous_run()
    driver = None
    
    try:
        # 2. Создание браузера
        driver = create_driver(use_proxy_flag=use_proxy_flag)
        
        # !!! ИЗМЕНЕНИЕ: Добавлена логика повторных попыток для проверки IP
        ip_check_successful = False
        for attempt in range(1, IP_CHECK_RETRIES + 1):
            try:
                print(f"--- Попытка {attempt}/{IP_CHECK_RETRIES} проверки IP-адреса... ---")
                driver.get('https://httpbin.org/ip')
                # Ждем появления тега <pre>, в котором содержится IP
                wait = WebDriverWait(driver, 25)
                ip_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
                print(f"УСПЕХ! Браузер работает. IP АДРЕС: {ip_element.text.strip()}")
                ip_check_successful = True
                break # Если успешно, выходим из цикла
            except WebDriverException as e:
                print(f"ОШИБКА при проверке IP (попытка {attempt}): {str(e).splitlines()[0]}")
                save_debug_info(driver, f"ip_check_fail_attempt_{attempt}")
                if attempt < IP_CHECK_RETRIES:
                    print(f"Пауза {IP_CHECK_DELAY_SECONDS} секунд перед повторной попыткой...")
                    time.sleep(IP_CHECK_DELAY_SECONDS)
                else:
                    print("!!! КРИТИЧЕСКАЯ ОШИБКА: Не удалось проверить IP-адрес после всех попыток.")
        
        # Если после всех попыток IP так и не проверился, завершаем скрипт с ошибкой
        if not ip_check_successful:
            raise RuntimeError("Не удалось подтвердить рабочий IP-адрес.")


        # 3. Основной цикл парсинга
        print(f"\nЗагружаем страницу: {start_url}")
        driver.get(start_url)
        WebDriverWait(driver, 45).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='ItemCard']")))
        print("Страница загружена.")

        handle_all_popups(driver, timeout=5)

        print("\n--- Начинаем инкрементальный парсинг ---")
        processed_urls = set()
        products_data = []
        stale_scrolls = 0

        while stale_scrolls < config.STALE_SCROLL_LIMIT:
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

            print("...плавная прокрутка страницы...")
            current_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                human_mouse_move(driver)
                time.sleep(random.uniform(1.5, 2.5))
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == current_height:
                    break
                current_height = new_height
            
            random_wait(type_of_action="scroll")

            if len(processed_urls) == count_before_scroll:
                stale_scrolls += 1
                print(f"Новых товаров не найдено. Попытка {stale_scrolls}/{config.STALE_SCROLL_LIMIT}...")
                save_debug_info(driver, f"stale_scroll_{stale_scrolls}")
            else:
                stale_scrolls = 0

            if len(products_data) >= config.LIMIT:
                print(f"Достигнут лимит в {config.LIMIT} товаров.")
                break

        # 4. Обработка и сохранение данных
        print(f"\nВсего найдено уникальных товаров: {len(products_data)}")
        if products_data:
            proxies_req = get_proxies_for_requests(use_proxy_flag)
            download_images(products_data, proxies_req, driver.session_user_agent, start_url)
            write_to_csv(products_data)

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА в основном блоке: {e}")
        if driver:
            save_debug_info(driver, "critical_error")
        # !!! ИЗМЕНЕНИЕ: Явный выход с кодом ошибки, чтобы run_all.py мог это отследить
        sys.exit(1)
    finally:
        if driver:
            driver.quit()
            print("\nБраузер закрыт.")


if __name__ == "__main__":
    main()