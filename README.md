# Агрегатор логов веб-сервера Apache

Приложение осуществляет сбор, агрегацию, парсинг файлов логов Apache по маске с сохранением структуры данных в СУБД. Предоставляет консольный (CLI) и оконный (GUI) интерфейсы для работы, а также Web-API (FastAPI) с AJAX-клиентом для работы с данными и фоновой скачки контента.

## Требования
* Python 3.10+
* Зависимости: `fastapi`, `uvicorn`, `sqlalchemy`, `requests`, `werkzeug`

## Установка зависимостей
```bash
pip install fastapi uvicorn sqlalchemy requests werkzeug

##Запуск: 
Ссылка: http://127.0.0.1:8080
Запуск: python server.py 
Стоп: ctrl + C
