# utils.py

import os
import shutil
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from config import DEBUG_DIR, PHOTO_DIR, CSV_PATH

def cleanup_previous_run():
    """Очищает файлы и папки от предыдущего запуска."""
    print("Очистка старых файлов...")
    if os.path.exists(CSV_PATH): os.remove(CSV_PATH)
    if os.path.exists(PHOTO_DIR): shutil.rmtree(PHOTO_DIR)
    if os.path.exists(DEBUG_DIR): shutil.rmtree(DEBUG_DIR)
    os.makedirs(PHOTO_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)
    print("Очистка завершена.")

def save_debug_info(driver, reason):
    """Сохраняет скриншот и HTML для отладки."""
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
        print(f"ОТЛАДКА: Не удалось сохранить файлы отладки: {e}")

def handle_all_popups(driver, timeout=3):
    """Универсальный обработчик для всех известных всплывающих окон."""
    selectors = {
        "Модальное окно товара": "button[data-test-id='modal-close-button']",
        "Окно уведомлений": "button[data-test-id='enable-notifications-button']",
        "Окно cookie": "button[data-test-id='allow-button']"
    }
    for name, selector in selectors.items():
        try:
            wait = WebDriverWait(driver, timeout)
            button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            print(f"! ОБНАРУЖЕНО: '{name}'. Закрываем...")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(random.uniform(1, 1.5))
        except TimeoutException:
            pass # Окно не найдено, это нормально

def human_mouse_move(driver):
    """Имитирует случайные движения мыши."""
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
    """Организует умные паузы."""
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