import os
import re
import glob
import json
from datetime import datetime
from db import SessionLocal, LogEntry

LOG_PATTERN = re.compile(
    r'(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<date>.*?)\]\s+"(?P<method>\S+)\s+(?P<url>\S+)\s+.*?#?"\s+(?P<status>\d+)\s+(?P<size>\S+)'
)

def parse_apache_date(date_str):

    clean_date = date_str.split(" ")[0]
    return datetime.strptime(clean_date, "%d/%b/%Y:%H:%M:%S")

def run_parser():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    log_dir = config["log_dir"]
    mask = config["log_file_mask"]
    search_path = os.path.join(log_dir, mask)
    files = glob.glob(search_path)
    
    if not files:
        print(f"Лог-файлы по пути {search_path} не найдены.")
        return 0

    db = SessionLocal()
    total_parsed = 0

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = LOG_PATTERN.match(line)
                    if match:
                        data = match.groupdict()
                        try:
                            size = int(data["size"])
                        except ValueError:
                            size = 0
                            
                        entry = LogEntry(
                            ip=data["ip"],
                            timestamp=parse_apache_date(data["date"]),
                            method=data["method"],
                            url=data["url"],
                            status=int(data["status"]),
                            size=size
                        )
                        db.add(entry)
                        total_parsed += 1
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Ошибка при обработке файла {file_path}: {e}")
    
    db.close()
    print(f"Парсинг завершен. Успешно сохранено записей: {total_parsed}")
    return total_parsed

if __name__ == "__main__":
    run_parser()