import os
import yt_dlp
import requests
from fastapi import FastAPI, BackgroundTasks, Header, HTTPException

app = FastAPI()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
AUTH_SECRET = os.environ.get("AUTH_SECRET", "kofuku_secret_key_12345")

def download_and_send(chat_id: int, query: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'quiet': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            entry = info['entries'][0] if 'entries' in info and info.get('entries') else info
            
            file_id = entry.get('id')
            file_path = f"/tmp/{file_id}.mp3"
            title = entry.get('title', 'Unknown Track')
            uploader = entry.get('uploader', 'Unknown Artist')

        if os.path.exists(file_path):
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
            with open(file_path, 'rb') as audio:
                requests.post(url, data={
                    'chat_id': chat_id,
                    'title': title[:60],
                    'performer': uploader[:60],
                    'caption': f"🎵 **{title}**\n👤 {uploader}\n\n🤖 ارسال شده توسط Kofuku"
                }, files={'audio': audio})
            
            os.remove(file_path)

    except Exception as e:
        print(f"Error processing '{query}': {e}")
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
                'chat_id': chat_id,
                'text': f"❌ متأسفانه در دانلود آهنگ «{query}» مشکلی پیش آمد."
            })
        except Exception:
            pass

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Kofuku Music Downloader"}

@app.post("/download")
async def handle_download(chat_id: int, query: str, background_tasks: BackgroundTasks, x_auth_token: str = Header(None)):
    if x_auth_token != AUTH_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    background_tasks.add_task(download_and_send, chat_id, query)
    return {"status": "queued"}
