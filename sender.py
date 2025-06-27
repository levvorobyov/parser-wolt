# sender.py

import pandas as pd
import requests
import os
import time
import sys
import re
import io
from PIL import Image

# --- НАСТРОЙКИ ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Пути к CSV-файлу и папке с фото
CSV_FILE = os.path.join(SCRIPT_DIR, 'bazarstore_products.csv')
PHOTOS_DIR = os.path.join(SCRIPT_DIR, 'photos')
FLASK_MARKET_API_URL = 'http://192.168.255.11:5500/api/competitor-parser/load-competitor-product'
# ID удален отсюда, теперь он передается как аргумент при запуске
API_KEY = '3e8d9b42c12a4e849b473fdc68c0cba70fe35338e4b01e6ed1fc2d3225cf07aa'

TEST_MODE_ROW_LIMIT = 1000000
# -------------------

def clean_price(price_str):
    """
    Очищает строку цены от символа валюты и пробелов,
    и преобразует в float.
    Возвращает float или None, если преобразование невозможно.
    """
    if price_str is None or not isinstance(price_str, str):
        return None
    cleaned_price = re.sub(r'[^\d.]', '', price_str.replace(',', '.'))
    try:
        return float(cleaned_price)
    except ValueError:
        print(f"Внимание: не удалось преобразовать цену '{price_str}' в число.")
        return None

def send_product_data(row, shebeke_id):
    photo_filename = row.get('photo_path')
    product_name = row.get('name')

    new_price_str = row.get('price_new')
    old_price_str = row.get('price_old')

    new_price_float = clean_price(new_price_str)
    old_price_float = clean_price(old_price_str)

    files = None
    photo_to_close = None

    if photo_filename and pd.notna(photo_filename):
        photo_filename_base = os.path.basename(str(photo_filename))
        photo_full_path = os.path.join(PHOTOS_DIR, photo_filename_base)

        if os.path.exists(photo_full_path):
            # --- НАЧАЛО ВСТАВЛЕННОЙ ЛОГИКИ КОНВЕРТАЦИИ ---
            if photo_filename_base.lower().endswith('.png'):
                print(f"Инфо: Конвертация '{photo_filename_base}' из PNG в JPG с белым фоном...")
                try:
                    # Открываем PNG изображение
                    img = Image.open(photo_full_path).convert("RGBA")

                    # Создаем новое изображение с белым фоном
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    
                    # Вставляем исходное изображение на белый фон, используя альфа-канал как маску
                    background.paste(img, mask=img)

                    # Создаем объект BytesIO для хранения JPG данных в памяти
                    photo_to_close = io.BytesIO()

                    # Сохраняем итоговое изображение как JPEG
                    background.save(photo_to_close, format='JPEG', quality=85)

                    # Перемещаем "курсор" в начало потока
                    photo_to_close.seek(0)
                    # Меняем расширение файла для API
                    jpg_filename = os.path.splitext(photo_filename_base)[0] + '.jpg'
                    files = {'photo': (jpg_filename, photo_to_close, 'image/jpeg')}
                except Exception as e:
                    print(f"Ошибка конвертации {photo_filename_base}: {e}")
                    files = None
                    photo_to_close = None 
            else:
                # Если это не PNG, используем старую логику
                photo_to_close = open(photo_full_path, 'rb')
                files = {'photo': (photo_filename_base, photo_to_close, 'image/jpeg')}
            # --- КОНЕЦ ВСТАВЛЕННОЙ ЛОГИКИ ---
        else:
            print(f"Внимание: Файл фото не найден: {photo_full_path}. Отправка без фото.")
    else:
        print(f"Инфо: Нет имени фото для {product_name}. Отправка без фото.")

    data = {
        'shebeke_id': shebeke_id,
        'product_name': product_name,
        'new_price': new_price_float,
        'old_price': old_price_float
    }
    data = {k: v for k, v in data.items() if v is not None}
    headers = { 'X-API-KEY': API_KEY }

    try:
        print(f"Отправка: {product_name} (Новая: {data.get('new_price')}, Старая: {data.get('old_price')}) {'с фото' if files else 'без фото'}...")
        response = requests.post(FLASK_MARKET_API_URL, files=files, data=data, headers=headers, timeout=60)
        response.raise_for_status()
        print(f"Успешно: {product_name}.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки {product_name}: {e}")
        if e.response is not None:
            print(f"   Ответ сервера ({e.response.status_code}): {e.response.text}")
        return False
    finally:
        if photo_to_close:
            photo_to_close.close()

def main():
    if not API_KEY or API_KEY == 'ВСТАВЬ_СЮДА_СВОЙ_КЛЮЧ':
        print("Ошибка: API_KEY не установлен или используется ключ-плейсхолдер в sender.py. Пожалуйста, установите его.")
        return

    # Получаем ID из аргументов командной строки
    try:
        if len(sys.argv) < 2:
            print("Ошибка: Необходим ID Shebeke в качестве аргумента командной строки.")
            print("Пример: python sender.py 123456789")
            return
        shebeke_id_to_use = int(sys.argv[1])
    except (ValueError, IndexError):
        print(f"Ошибка: ID Shebeke должен быть числом, получено: '{sys.argv[1:]}'")
        return

    try:
        df = pd.read_csv(CSV_FILE)
        print(f"Инфо: CSV прочитан ({len(df)}). Колонки: {df.columns.tolist()}")
    except Exception as e:
        print(f"Ошибка: Не удалось прочитать CSV '{CSV_FILE}': {e}")
        return

    required_cols = ['name', 'price_new', 'price_old', 'photo_path']
    if not all(col in df.columns for col in required_cols):
        print(f"Ошибка: В CSV файле '{CSV_FILE}' отсутствуют необходимые колонки. Ожидаются: {required_cols}, Найдены: {df.columns.tolist()}")
        return

    if TEST_MODE_ROW_LIMIT is not None:
        print(f"ИНФО: Тестовый режим! Будет отправлено не более {TEST_MODE_ROW_LIMIT} строк.")
        df_to_send = df.head(TEST_MODE_ROW_LIMIT)
    else:
        df_to_send = df

    # Используем переменную shebeke_id_to_use, полученную из аргументов
    print(f"Инфо: Начинаем отправку {len(df_to_send)} товаров (Shebeke ID: {shebeke_id_to_use})...")
    success_count = 0
    fail_count = 0

    for index, row in df_to_send.iterrows():
        # Передаем ID в функцию отправки
        if send_product_data(row, shebeke_id_to_use):
            success_count += 1
        else:
            fail_count += 1
        time.sleep(0.2)

    print(f"\n--- Отправка завершена ---")
    print(f"   Успешно: {success_count}")
    print(f"   Неудачно: {fail_count}")

if __name__ == "__main__":
    main()