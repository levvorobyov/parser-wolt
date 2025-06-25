# run_all.py

import subprocess
import sys
import os
import time
import random
import atexit
import logging
 
 
try:
    import psutil 
except ImportError:
    print("Ошибка: для работы скрипта требуется библиотека 'psutil'.")
    print("Пожалуйста, установите ее командой: pip install psutil")
    sys.exit(1)


# --- КОНФИГУРАЦИЯ ---
LOCK_FILE = "run_all.lock"
LOG_FILE = "run_interactive.log"
# --- ПЕРЕКЛЮЧАТЕЛИ ---
USE_VPN = True    # Измените на False, чтобы отключить VPN
USE_PROXY = False  # Измените на True, чтобы включить Прокси

# --- СПИСОК ССЫЛОК ДЛЯ ПАРСИНГА ---
LINKS_TO_PARSE = {
    '1': ("Saqqız (Жвачка)", "https://wolt.com/az/aze/baku/venue/araz-yasamal-3-superstore-f/items/saqqz-95"),
    '2': ("Meyve", "https://wolt.com/az/aze/baku/venue/araz-yasamal-3-superstore-f/items/meyv-18"),
}

def setup_logging():
    """Настраивает логирование в файл и на консоль."""
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    formatter = logging.Formatter('%(message)s')

    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def create_lock_file():
    """Создает lock-файл, если скрипт еще не запущен."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                try:
                    p = psutil.Process(pid)
                    if os.path.basename(__file__) in ' '.join(p.cmdline()):
                         print(f"Ошибка: Скрипт уже запущен с PID: {pid}. Повторный запуск невозможен.")
                         sys.exit(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied): pass
        except (IOError, ValueError): pass
        
        print("Обнаружен устаревший lock-файл. Удаляем его.")
        os.remove(LOCK_FILE)

    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    atexit.register(remove_lock_file)
    print(f"Lock-файл создан. PID процесса: {os.getpid()}")

def remove_lock_file():
    """Удаляет lock-файл, если он существует."""
    print("Lock-файл удален. Работа завершена.")
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def display_menu(menu_title, options):
    """Отображает универсальное меню."""
    print("\n" + "="*60)
    print(menu_title)
    # ДОБАВЛЕНО: Опция "Парсить всё"
    print("  0: Парсить все категории (Parse All Categories)")
    for key, text in options.items():
        print(f"  {key}: {text}")
    print("\nВведите номер (например: 1), номера через запятую (1,3), 0 для всех, или 'exit' для выхода.")
    print("="*60)

def get_link_selection():
    """Получает и проверяет выбор ссылок для парсинга."""
    while True:
        user_input = input("> ").strip()
        if user_input.lower() == 'exit':
            return []
        
        # ДОБАВЛЕНО: Проверка на ввод "0"
        if user_input == '0':
            print("Выбраны все категории для парсинга.")
            return list(LINKS_TO_PARSE.values())

        if not user_input:
            print("Ошибка: Пустой ввод. Пожалуйста, введите номер.")
            continue
            
        choices = [c.strip() for c in user_input.split(',')]
        selected_links = []
        valid_selection = True
        for choice in choices:
            if choice in LINKS_TO_PARSE:
                selected_links.append(LINKS_TO_PARSE[choice])
            else:
                print(f"Ошибка: Неверный выбор '{choice}'. Доступные варианты: {', '.join(LINKS_TO_PARSE.keys())} или 0.")
                valid_selection = False
                break
        if valid_selection:
            return selected_links

def run_script(script_name, url=None, use_proxy_flag=False):
    """Запускает скрипт в реальном времени, без буферизации."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    command = [sys.executable, "-u", script_path]
    if url:
        command.append(url)
    if use_proxy_flag:
        command.append("--use-proxy")
        
    if not os.path.exists(script_path):
        logging.error(f"!!! Ошибка: Скрипт '{script_name}' не найден по пути '{script_path}'")
        return False
    
    logging.info(f"\n{'='*25} ЗАПУСК СКРИПТА: {script_name} {'='*25}\n")
    try:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1) as p:
            for line in p.stdout:
                logging.info(line.strip())
        
        if p.returncode != 0:
             raise subprocess.CalledProcessError(p.returncode, p.args)

        logging.info(f"\n{'='*25} СКРИПТ '{script_name}' УСПЕШНО ЗАВЕРШЕН {'='*25}\n")
        return True
    except subprocess.CalledProcessError:
        logging.error(f"\n!!! КРИТИЧЕСКАЯ ОШИБКА: Скрипт '{script_name}' завершился с ошибкой.")
        return False
    except Exception as e:
        logging.error(f"!!! Непредвиденная ошибка при запуске '{script_name}': {e}")
        return False

def main():
    """Основная функция: меню и последовательный запуск парсера и сендера."""
    
    display_menu("Выберите категории для парсинга:", {k: v[0] for k, v in LINKS_TO_PARSE.items()})
    selected_links = get_link_selection()
    
    if not selected_links:
        print("Выход из программы.")
        return

    setup_logging()
    
    sudo_password = '31337' 
    vpn_config_file = 'xachchch.ovpn'
    
    logging.info("="*60)
    logging.info("Выбор сделан.")
    logging.info(f"  - VPN: {'ВКЛЮЧЕН' if USE_VPN else 'ОТКЛЮЧЕН'}")
    logging.info(f"  - Прокси: {'ВКЛЮЧЕН' if USE_PROXY else 'ОТКЛЮЧЕН'}")
    logging.info(f"Весь дальнейший вывод дублируется в файл: {LOG_FILE}")
    logging.info("="*60)
    
    total_selected = len(selected_links)
    for i, (link_name, link_url) in enumerate(selected_links, 1):
        logging.info("\n" + "#"*70)
        logging.info(f"### ЗАПУСК {i}/{total_selected}: '{link_name}'")
        logging.info("#"*70)
        
        parser_successful = False
        
        if USE_VPN:
            vpn_process = None
            start_cmd_string = f'echo {sudo_password} | sudo -S openvpn --config {vpn_config_file}'
            stop_cmd_string = f'echo {sudo_password} | sudo -S pkill openvpn'
            try:
                logging.info(f"Запускаем VPN...")
                vpn_process = subprocess.Popen(start_cmd_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(10)
                if vpn_process.poll() is not None:
                    raise RuntimeError("Не удалось запустить VPN.")
                logging.info("VPN соединение активно. Начинаем парсинг...")
                
                parser_successful = run_script('parser.py', url=link_url, use_proxy_flag=USE_PROXY)
            except Exception as e:
                logging.error(f"\n!!! Произошла ошибка во время сессии VPN: {e}")
            finally:
                if vpn_process:
                    logging.info("\nОтключаем VPN...")
                    subprocess.run(stop_cmd_string, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logging.info("VPN процесс был остановлен.")
        else: # Запуск без VPN
            parser_successful = run_script('parser.py', url=link_url, use_proxy_flag=USE_PROXY)

        if parser_successful:
            logging.info("\nЗапускаем отправку данных...")
            run_script('sender.py')
        else:
            logging.warning("\nПарсинг не был успешным. Отправка данных отменена.")

        if i < total_selected:
            delay_seconds = random.randint(60, 300) 
            minutes = delay_seconds // 60
            seconds = delay_seconds % 60
            logging.info(f"\n{'='*25} ПАУЗА {'='*25}")
            logging.info(f"Следующий запуск начнется через {minutes} мин. {seconds} сек...")
            time.sleep(delay_seconds)

    logging.info("\n\n" + "*"*60)
    logging.info("ВСЕ ВЫБРАННЫЕ ЗАДАЧИ ЗАВЕРШЕНЫ.")
    logging.info("*"*60)

if __name__ == "__main__":
    create_lock_file()
    main()