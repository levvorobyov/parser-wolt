# webdriver_factory.py

import random
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from config import USER_AGENTS, PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS

def create_driver(use_proxy_flag=False):
    """Создает, настраивает и возвращает экземпляр WebDriver."""
    session_user_agent = random.choice(USER_AGENTS)
    selenium_wire_options = {}

    if use_proxy_flag:
        print("Информация: Настраиваем прокси для браузера.")
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
        print("Информация: Запуск браузера без прокси.")

    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-agent={session_user_agent}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    print("Запускаем браузер...")
    driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=selenium_wire_options)
    driver.set_page_load_timeout(60)

    # Добавляем user_agent в атрибуты драйвера для использования в других модулях
    driver.session_user_agent = session_user_agent
    return driver