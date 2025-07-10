# config.py

# --- ПУТИ И ИМЕНА ФАЙЛОВ ---
DEBUG_DIR = 'debug_files'
PHOTO_DIR = 'photos'
CSV_PATH = 'bazarstore_products.csv'

# --- НАСТРОЙКИ ПАРСЕРА ---
LIMIT = 100000 # Лимит товаров для парсинга
STALE_SCROLL_LIMIT = 8 # Сколько раз прокручивать впустую, прежде чем остановиться

# --- НАСТРОЙКИ БРАУЗЕРА И ПРОКСИ ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15"
]

# Данные прокси (если используются)
PROXY_HOST = "brd.superproxy.io"
PROXY_PORT = 33335
PROXY_USER = "brd-customer-hl_335cad1c-zone-datacenter_proxy_araz"
PROXY_PASS = "9xabfgb7aidn"