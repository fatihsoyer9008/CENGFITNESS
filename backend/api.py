import os
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from backend import database, vision

# tarama sayfasinin HTML'i ayri dosyada duruyor, basta bir kez okuyoruz
_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "camera_page.html")
with open(_HTML_PATH, "r", encoding="utf-8") as f:
    CAMERA_HTML = f.read()


api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _err(msg, code=400):
    # standart hata cevabi
    return JSONResponse({"status": "error", "message": msg}, status_code=code)


@api.post("/analyze")
async def analyze(request: Request):
    # tarayicidan gelen base64 fotografi YOLO + Gemini ile analiz eder
    payload = await request.json() or {}
    img = vision.decode_image_b64(payload.get("image"))
    if img is None:
        return _err("Görsel okunamadı")

    try:
        frame = vision.prepare_frame(img)
        return JSONResponse(vision.build_capture_payload(frame))
    except Exception as e:
        print(f"Analiz hatasi:\n{traceback.format_exc()}")
        return _err(str(e), 500)


@api.post("/save-food-log")
async def save_food_log(request: Request):
    # kamera sayfasindan gelen sonucu yemek gunlugune kaydeder
    data = await request.json() or {}
    if not data.get("user_id"):
        return _err("user_id yok")
    try:
        database.add_food_log(
            user_id=int(data["user_id"]),
            food_name=str(data.get("food_name", "?")),
            calories=data.get("calories", 0),
            protein_g=str(data.get("protein", "0g")),
            carbs_g=str(data.get("karb", "0g")),
            fat_g=str(data.get("yag", "0g")),
            source="camera",
        )
        return JSONResponse({"status": "ok"})
    except Exception as e:
        print(f"Kayıt hatası:\n{traceback.format_exc()}")
        return _err(str(e), 500)


@api.get("/api/health")
async def health():
    # sunucu ayakta mi kontrolu
    return {"status": "ok"}


@api.get("/camera-page", response_class=HTMLResponse)
async def camera_page(user_id: str = ""):
    # getUserMedia tabanli tarama sayfasi; user_id'yi HTML icine gomuyoruz
    html = CAMERA_HTML.replace("__USER_ID__", user_id or "")
    return HTMLResponse(html)
