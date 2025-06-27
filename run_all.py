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
LOCK_FILE = "run_all_araz.lock"
LOG_FILE = "run_interactive_araz.log"
# !!! ИЗМЕНЕНИЕ: ID магазина перенесен сюда для централизованного управления
SHEBEKE_ID_UMICO = 198006659

# --- ПЕРЕКЛЮЧАТЕЛИ ---
USE_VPN = False    # Измените на False, чтобы отключить VPN
USE_PROXY = True  # Измените на True, чтобы включить Прокси

# --- СПИСОК ССЫЛОК ДЛЯ ПАРСИНГА ---
LINKS_TO_PARSE = {
    '1':  ("Meyvə & Tərəvəz",                "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/meyv-trvz-17"),
    '2':  ("Xonça Un Məmulatları",           "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/xonca-un-mmulatlar-32"),
    '3':  ("Təzə ət məhsulları",             "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/tz-t-mhsullar-38"),
    '4':  ("Toyuq məhsulları",               "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/toyuq-mhsullar-37"),
    '5':  ("Dəniz məhsulları",               "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/dniz-mhsullar-47"),
    '6':  ("Hazır qida",                     "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/hazr-qida-63"),
    '7':  ("Süd məhsulları",                 "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/sud-mhsullar-40"),
    '8':  ("Yağlar",                         "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/yaglar-42"),
    '9':  ("Yumurta",                        "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/yumurta-39"),
    '10': ("Qastronom",                      "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/qastronom-20"),
    '11': ("Spirtsiz Içkilər",               "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/spirtsiz-ickilr-1"),
    '12': ("Şirələr paketləşdirilmiş",       "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/sirlr-paketlsdirilmis-2"),
    '13': ("Sadə və mineral sular",          "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/sad-v-mineral-sular-3"),
    '14': ("Enerji Içkiləri",                "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/enerji-ickilri-4"),
    '15': ("Şirniyyat ədədli",               "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/sirniyyat-ddli-36"),
    '16': ("Çəki şirniyyatları",             "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/cki-sirniyyatlar-51"),
    '17': ("Saqqız",                         "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/saqqz-95"),
    '18': ("Tumlar və çipslər",              "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/tumlar-v-cipslr-11"),
    '19': ("Quru meyvə",                     "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/quru-meyv-66"),
    '20': ("Diabetik və dietik qidalar",     "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/diabetik-v-dietik-qidalar-49"),
    '21': ("Dondurulmuş qida",               "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/dondurulmus-qida-50"),
    '22': ("Dondurma",                       "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/dondurma-41"),
    '23': ("Makaron və düyü",                "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/makaron-v-duyu-45"),
    '24': ("Hazır səhər yeməkləri",          "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/hazr-shr-yemklri-62"),
    '25': ("Mürəbbə və cemlər",              "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/murbb-v-cemlr-52"),
    '26': ("Konservləşdirilmiş məhsullar",    "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/konservlsdirilmis-mhsullar-53"),
    '27': ("Sous və sirkələr",               "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/sous-v-sirklr-65"),
    '28': ("Ədviyyat və bişirmə məhsulları", "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/dviyyat-v-bisirm-mhsullar-61"),
    '29': ("Sushi məhsulları",                "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/sushi-mhsullar-48"),
    '30': ("Çay və kofe",                    "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/cay-v-kofe-35"),
    '31': ("Un",                             "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/un-46"),
    '32': ("Şəkər tozu və qənd",             "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/skr-tozu-v-qnd-67"),
    '33': ("Uşaq qidası və baxımı",         "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/usaq-qidas-v-baxm-56"),
    '34': ("Xanımlar üçün şəxsi baxım",      "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/xanmlar-ucun-sxsi-baxm-54"),
    '35': ("Bəylər üçün şəxsi baxim",        "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/bylr-ucun-sxsi-baxim-55"),
    '36': ("Kosmetika ve qulluq vasitələri", "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/kosmetika-ve-qulluq-vasitlri-76"),
    '37': ("Diş pastaları və fırçaları",     "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/dis-pastalar-v-frcalar-57"),
    '38': ("Ümumi hamam məhsulları",         "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/umumi-hamam-mhsullar-58"),
    '39': ("Təmizlik",                       "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/tmizlik-59"),
    '40': ("Tekstil və geyim",              "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/tekstil-v-geyim-69"),
    '41': ("Ev əşyaları",                    "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/ev-syalar-87"),
    '42': ("Xırdavat ləvazimatları",         "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/xrdavat-lvazimatlar-82"),
    '43': ("Ev heyvanları üçün yem",         "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/ev-heyvanlar-ucun-yem-60"),
    '44': ("Tütün məhsulları",               "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/tutun-mhsullar-16"),
    '45': ("Elektron siqaret",               "https://wolt.com/az/aze/baku/venue/araz-supermarket-nefilr/items/elektron-siqaret-81"),
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

# !!! ИЗМЕНЕНИЕ: Добавлен новый аргумент `shebeke_id` для передачи в sender.py
def run_script(script_name, url=None, use_proxy_flag=False, shebeke_id=None):
    """Запускает скрипт в реальном времени, без буферизации."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    command = [sys.executable, "-u", script_path]
    if url:
        command.append(url)
    if use_proxy_flag:
        command.append("--use-proxy")
    # !!! ИЗМЕНЕНИЕ: Если shebeke_id предоставлен, добавляем его в команду
    if shebeke_id:
        command.append(str(shebeke_id))

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
            # !!! ИЗМЕНЕНИЕ: Передаем SHEBEKE_ID_UMICO в скрипт sender.py
            run_script('sender.py', shebeke_id=SHEBEKE_ID_UMICO)
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