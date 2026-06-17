import uvicorn
import json
import requests
from fastapi import FastAPI, Depends, HTTPException, status, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from db import SessionLocal, User, LogEntry, DownloadedContent, init_db
from werkzeug.security import check_password_hash

init_db()
app = FastAPI(title="Apache Logs Aggregator API")

import os
if not os.path.exists("templates"):
    os.makedirs("templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/logs")
def get_logs(
    start_date: str = Query(None, description="YYYY-MM-DD HH:MM:SS"),
    end_date: str = Query(None, description="YYYY-MM-DD HH:MM:SS"),
    group_by_ip: bool = Query(False),
    filter_ip: str = Query(None),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(LogEntry)
        
        if filter_ip:
            query = query.filter(LogEntry.ip == filter_ip)
            
        if start_date:
            query = query.filter(LogEntry.timestamp >= datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S"))
        if end_date:
            query = query.filter(LogEntry.timestamp <= datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S"))
            
        if group_by_ip:

            results = db.query(LogEntry.ip, func.count(LogEntry.id).label("count")).group_by(LogEntry.ip)
            if filter_ip:
                results = results.filter(LogEntry.ip == filter_ip)
            return [{"ip": r[0], "count": r[1]} for r in results.all()]
            
        
        logs = query.all()
        return [
            {
                "id": l.id, "ip": l.ip, "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "method": l.method, "url": l.url, "status": l.status, "size": l.size
            } for l in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка запроса: {str(e)}")



@app.post("/api/auth")
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not check_password_hash(user.password_hash, password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    return {"status": "success", "message": "Авторизован"}

@app.get("/api/urls")
def get_urls_by_keyword(keyword: str = Query(""), db: Session = Depends(get_db)):
    
    query = db.query(LogEntry.url).distinct()
    if keyword:
        query = query.filter(LogEntry.url.like(f"%{keyword}%"))
    urls = [r[0] for r in query.limit(50).all()]
    return {"urls": urls}

@app.post("/api/download")
def download_content(url: str = Form(...), db: Session = Depends(get_db)):
    
    try:
        
        target_url = url if url.startswith("http") else f"https://httpbin.org/get?original_route={url}"
        
        response = requests.get(target_url, timeout=5)
        size = len(response.content)
        
        content_record = DownloadedContent(
            url=url,
            filename=url.split("/")[-1] or "index.html",
            size=size,
            content=response.text[:50000] 
        )
        db.add(content_record)
        db.commit()
        return {"status": "success", "size": size, "filename": content_record.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось загрузить контент: {str(e)}")

@app.get("/api/content/list")
def list_content(db: Session = Depends(get_db)):
    content_list = db.query(DownloadedContent).all()
    return [{"id": c.id, "url": c.url, "filename": c.filename, "size": c.size} for c in content_list]

@app.get("/api/content/{content_id}")
def get_content_detail(content_id: int, db: Session = Depends(get_db)):
    item = db.query(DownloadedContent).filter(DownloadedContent.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Контент не найден")
    return {"id": item.id, "url": item.url, "content": item.content, "size": item.size}

@app.get("/", response_class=HTMLResponse)
def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

uvicorn.run(app, host="127.0.0.1", port=8080)