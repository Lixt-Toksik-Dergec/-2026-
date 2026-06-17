import sys
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from db import SessionLocal, LogEntry

def get_filtered_data(ip_filter=None, start_str=None, end_str=None, group_by_ip=False):
    db = SessionLocal()
    try:
        query = db.query(LogEntry)
        if ip_filter:
            query = query.filter(LogEntry.ip == ip_filter)
        if start_str:
            sd = datetime.strptime(start_str, "%Y-%m-%d")
            query = query.filter(LogEntry.timestamp >= sd)
        if end_str:
            ed = datetime.strptime(end_str, "%Y-%m-%d")
            query = query.filter(LogEntry.timestamp <= ed)
            
        if group_by_ip:
            from sqlalchemy import func
            results = db.query(LogEntry.ip, func.count(LogEntry.id)).group_by(LogEntry.ip).all()
            return [{"ip": r[0], "count": r[1]} for r in results]
            
        return query.order_by(LogEntry.timestamp.desc()).all()
    except Exception as e:
        print(f"Ошибка получения данных: {e}")
        return []
    finally:
        db.close()

def run_cli():
    print("=== CLI АНАЛИЗАТОР ЛОГОВ APACHE ===")
    while True:
        print("\nВыберите действие:")
        print("1. Посмотреть все данные")
        print("2. Фильтр по IP")
        print("3. Группировка по IP")
        print("4. Выборка по временному промежутку дат (ГГГГ-ММ-ДД)")
        print("5. Запустить принудительный парсинг логов")
        print("6. Выход")
        
        choice = input("Введите номер действия: ").strip()
        
        if choice == "1":
            logs = get_filtered_data()
            for l in logs[:100]: print(f"[{l.timestamp}] {l.ip} -> {l.url} ({l.status})")
        elif choice == "2":
            ip = input("Введите IP: ").strip()
            logs = get_filtered_data(ip_filter=ip)
            for l in logs: print(f"[{l.timestamp}] {l.ip} -> {l.url} ({l.status})")
        elif choice == "3":
            groups = get_filtered_data(group_by_ip=True)
            for g in groups: print(f"IP: {g['ip']} | Количество запросов: {g['count']}")
        elif choice == "4":
            start = input("Дата начала (ГГГГ-ММ-ДД): ").strip()
            end = input("Дата окончания (ГГГГ-ММ-ДД): ").strip()
            try:
                logs = get_filtered_data(start_str=start, end_str=end)
                for l in logs: print(f"[{l.timestamp}] {l.ip} -> {l.url} ({l.status})")
            except Exception as e:
                print(f"Неверный формат дат: {e}")
        elif choice == "5":
            from parser import run_parser
            run_parser()
        elif choice == "6":
            break
        else:
            print("Неверный ввод. Попробуйте еще раз.")

class LogAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Apache Logs Aggregator Viewer")
        self.root.geometry("800x500")
        
        frame_filters = tk.Frame(root)
        frame_filters.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(frame_filters, text="IP фильтр:").grid(row=0, column=0, padx=5)
        self.entry_ip = tk.Entry(frame_filters, width=15)
        self.entry_ip.grid(row=0, column=1, padx=5)
        
        tk.Label(frame_filters, text="Старт (ГГГГ-ММ-ДД):").grid(row=0, column=2, padx=5)
        self.entry_start = tk.Entry(frame_filters, width=12)
        self.entry_start.grid(row=0, column=3, padx=5)
        
        tk.Label(frame_filters, text="Конец (ГГГГ-ММ-ДД):").grid(row=0, column=4, padx=5)
        self.entry_end = tk.Entry(frame_filters, width=12)
        self.entry_end.grid(row=0, column=5, padx=5)
        
        btn_filter = tk.Button(frame_filters, text="Применить", command=self.load_data, bg="#28a745", fg="white")
        btn_filter.grid(row=0, column=6, padx=10)

        btn_parse = tk.Button(frame_filters, text="Принудительный Парсинг", command=self.force_parse, bg="#007bff", fg="white")
        btn_parse.grid(row=0, column=7, padx=5)
        
        self.tree = ttk.Treeview(root, columns=("date", "ip", "url", "status", "size"), show="headings")
        self.tree.heading("date", text="Дата")
        self.tree.heading("ip", text="IP Адрес")
        self.tree.heading("url", text="URL")
        self.tree.heading("status", text="Статус")
        self.tree.heading("size", text="Размер")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.load_data()
        
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        ip = self.entry_ip.get().strip() or None
        start = self.entry_start.get().strip() or None
        end = self.entry_end.get().strip() or None
        
        try:
            logs = get_filtered_data(ip_filter=ip, start_str=start, end_str=end)
            for l in logs:
                self.tree.insert("", tk.END, values=(l.timestamp.strftime("%Y-%m-%d %H:%M:%S"), l.ip, l.url, l.status, l.size))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка обработки фильтров: {e}")

    def force_parse(self):
        from parser import run_parser
        count = run_parser()
        messagebox.showinfo("Парсинг логов", f"Успешно обработано и добавлено записей: {count}")
        self.load_data()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        root = tk.Tk()
        app = LogAppGUI(root)
        root.mainloop()
    else:
        print("Подсказка: Для запуска ОКОННОГО ИНТЕРФЕЙСА (GUI) передайте флаг --gui")
        run_cli()