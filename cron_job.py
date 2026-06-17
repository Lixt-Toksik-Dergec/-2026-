
import sys
from parser import run_parser

def main():
    try:
        print("--- Старт регламентного задания CRON ---")
        count = run_parser()
        print(f"--- Задание успешно выполнено. Обработано логов: {count} ---")
    except Exception as e:
        print(f"Критическая ошибка cron-скрипта: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()