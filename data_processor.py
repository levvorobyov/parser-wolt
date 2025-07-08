# data_processor.py

import os
import shutil
import time
import random
import requests
import csv
from config import PHOTO_DIR, CSV_PATH, PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS

def get_proxies_for_requests(use_proxy_flag):
    """Возвращает словарь с прокси для библиотеки requests."""
    if not use_proxy_flag:
        return {}
    proxy_string = f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
    return {'http': proxy_string, 'https': proxy_string}

def download_images(products_data, proxies, user_agent, start_url):
    """Скачивает изображения для списка товаров."""
    print(f"\nНачинаем скачивание {len(products_data)} изображений...")
    headers = {"User-Agent": user_agent, "Referer": start_url}
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

def write_to_csv(products_data):
    """Записывает собранные данные в CSV файл."""
    if not products_data:
        print("Нет данных для записи в CSV.")
        return
        
    print(f"\nЗапись {len(products_data)} товаров в {CSV_PATH}...")
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'price_new', 'price_old', 'photo_path', 'product_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for product in products_data:
            # Удаляем временные ключи перед записью
            product.pop('photo_url_full', None)
            writer.writerow(product)
    print("Данные успешно сохранены.")