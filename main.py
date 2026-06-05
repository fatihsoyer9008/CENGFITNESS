import os
import json
import base64
import logging
import traceback

import flet as ft
import flet.fastapi as flet_fastapi
import numpy as np
import cv2
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import google.generativeai as genai
from ultralytics import YOLO

import database
import ui_pages


def load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


load_dotenv()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

SECRET_KEY = os.environ.get("FLET_SECRET_KEY", "cengfitness-secret-2026")
os.environ.setdefault("FLET_SECRET_KEY", SECRET_KEY)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY bulunamadı. Proje kökünde .env dosyası oluşturup "
        ".env.example'daki gibi anahtarınızı girin."
    )

genai.configure(api_key=GEMINI_API_KEY)

gemini_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={
        "temperature": 0.1,
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "cal": {"type": "INTEGER"},
                "p": {"type": "STRING"},
                "k": {"type": "STRING"},
                "y": {"type": "STRING"},
                "tavsiye": {"type": "STRING"},
            },
            "required": ["cal", "p", "k", "y", "tavsiye"],
        },
    },
)


def _empty_nutrition(advice):
    return {"cal": "?", "p": "?", "k": "?", "y": "?", "tavsiye": advice}


def get_nutrition_from_gemini(food_name):
    prompt = (
        f"Kullanici kameraya '{food_name}' gosterdi. "
        "Turkiye'deki doyurucu standart 1 porsiyon icin besin degerlerini "
        "SADECE bu JSON formatinda yanitla: "
        '{"cal": 450, "p": "25g", "k": "40g", "y": "20g", '
        '"tavsiye": "1 standart porsiyon (yaklasik X gram) icin hesaplandi. Kisa tavsiye."}'
    )
    try:
        response = gemini_model.generate_content(prompt)
        try:
            return json.loads(response.text)
        except ValueError:
            return _empty_nutrition("Yapay zeka guvenlik filtresine takildi.")
        except json.JSONDecodeError as e:
            return _empty_nutrition(f"JSON hatasi: {e}")
    except Exception as e:
        print(f"Gemini API hatasi:\n{traceback.format_exc()}")
        return _empty_nutrition(f"Hata: {e}")


print("YOLO modeli yukleniyor...")
model = YOLO(os.path.join(BASE_DIR, "best.pt"))
print("[OK] YOLO modeli hazir.")

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def decode_image_b64(b64):
    if not b64:
        return None
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return None
    arr = np.frombuffer(raw, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def prepare_frame(img, target=480):
    h, w = img.shape[:2]
    mn = min(h, w)
    sx, sy = (w - mn) // 2, (h - mn) // 2
    cropped = img[sy:sy + mn, sx:sx + mn]
    return cv2.resize(cropped, (target, target))


def predict_food(frame):
    try:
        res = model(frame)[0]
        if getattr(res, "probs", None) is not None:
            idx = res.probs.top1
            name = res.names[idx]
            conf = float(res.probs.top1conf)
        elif getattr(res, "boxes", None) is not None and len(res.boxes) > 0:
            idx = int(res.boxes.cls[0].item())
            name = res.names[idx]
            conf = float(res.boxes.conf[0].item())
        else:
            name, conf = "Bilinmiyor", 0.0
    except Exception as e:
        print(f"Tahmin hatasi: {e}")
        name, conf = "Bilinmiyor", 0.0

    pct = round(conf * 100, 1)
    if name == "Bilinmiyor":
        stats = _empty_nutrition("Yiyecek tespit edilemedi.")
    else:
        stats = get_nutrition_from_gemini(name)
    return name, pct, stats


def encode_frame_b64(frame, quality=85):
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return base64.b64encode(buf.tobytes()).decode("utf-8") if ok else None


def build_capture_payload(frame):
    name, conf, stats = predict_food(frame)
    b64 = encode_frame_b64(frame)
    if b64 is None:
        return {"status": "error", "message": "Fotograf islenemedi"}
    return {
        "status": "ok",
        "image": b64,
        "food_name": name.replace("_", " ").upper(),
        "confidence": conf,
        "calories": stats.get("cal", "?"),
        "macros": {
            "protein": stats.get("p", "?"),
            "karb": stats.get("k", "?"),
            "yag": stats.get("y", "?"),
        },
        "advice": stats.get("tavsiye", "Bilgi alinamadi."),
    }


def flet_main(page):
    page.title = "CENG FITNESS"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ui_pages.BG_DARK
    page.padding = 0

    page.theme = ft.Theme(
        color_scheme_seed=ui_pages.PRIMARY,
        use_material3=True,
    )

    views = {
        "/login":    lambda: ui_pages.build_login_view(page),
        "/register": lambda: ui_pages.build_register_view(page),
        "/":         lambda: ui_pages.build_dashboard_view(page),
        "/scan":     lambda: ui_pages.build_scan_view(page, "http://127.0.0.1:8000", UPLOAD_DIR),
        "/food":     lambda: ui_pages.build_food_log_view(page),
        "/exercise": lambda: ui_pages.build_exercise_view(page),
        "/muscle":   lambda: ui_pages.build_muscle_view(page),
        "/stats":    lambda: ui_pages.build_stats_view(page),
        "/profile":  lambda: ui_pages.build_profile_view(page),
    }
    PUBLIC = ("/login", "/register")

    def close_open_overlays():
        dlg = getattr(page, "dialog", None)
        if dlg is not None and getattr(dlg, "open", False):
            dlg.open = False
        for ov in list(getattr(page, "overlay", []) or []):
            if getattr(ov, "open", False):
                ov.open = False

    def error_view(ex):
        return ft.View(
            route="/error", bgcolor=ui_pages.BG_DARK,
            controls=[ft.Container(padding=40, content=ft.Column([
                ft.Icon(ft.Icons.ERROR, color=ui_pages.DANGER, size=40),
                ft.Text(f"Sayfa yuklenemedi: {ex}", color=ui_pages.TEXT_PRIMARY, size=14),
                ft.FilledButton("Ana sayfa", on_click=lambda e: page.go("/")),
            ], spacing=12, horizontal_alignment="center"))],
        )

    def route_change(e):
        try:
            close_open_overlays()
        except Exception:
            pass

        page.views.clear()
        route = page.route or "/"

        if not page.session.get("user_id") and route not in PUBLIC:
            route = "/login"
            page.route = route
        elif page.session.get("user_id") and route in PUBLIC:
            route = "/"
            page.route = route

        try:
            page.views.append(views.get(route, views["/"])())
        except Exception as ex:
            traceback.print_exc()
            page.views.append(error_view(ex))

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)

    last_mobile = {"v": ui_pages.is_mobile(page)}

    def on_resized(e):
        now_mobile = ui_pages.is_mobile(page)
        if now_mobile != last_mobile["v"]:
            last_mobile["v"] = now_mobile
            route_change(None)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.on_resized = on_resized
    page.go(page.route or "/")


api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _err(msg, code=400):
    return JSONResponse({"status": "error", "message": msg}, status_code=code)


@api.post("/analyze")
async def analyze(request: Request):
    payload = await request.json() or {}
    img = decode_image_b64(payload.get("image"))
    if img is None:
        return _err("Görsel okunamadı")

    try:
        frame = prepare_frame(img)
        return JSONResponse(build_capture_payload(frame))
    except Exception as e:
        print(f"Analiz hatasi:\n{traceback.format_exc()}")
        return _err(str(e), 500)


@api.post("/save-food-log")
async def save_food_log(request: Request):
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
    return {"status": "ok"}


CAMERA_HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Yemek Tara — CENG FITNESS</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
  body {
    background: #0B1014; color: #E6EDF3;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center;
    padding: 16px; padding-bottom: 40px;
  }
  h1 { font-size: 18px; font-weight: 600; margin-bottom: 14px; color: #5EEAD4; }
  .frame {
    position: relative; width: 100%; max-width: 380px; aspect-ratio: 1;
    background: #1E262F; border-radius: 20px; border: 2px solid #0F766E;
    overflow: hidden; margin-bottom: 14px;
  }
  video, img.preview {
    width: 100%; height: 100%; object-fit: cover; display: block;
  }
  video { background: #000; }
  img.preview { display: none; }
  canvas { display: none; }
  .placeholder {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 12px; color: #5A6A7A;
    padding: 20px; text-align: center;
  }
  .placeholder svg { width: 64px; height: 64px; }
  .placeholder.hidden { display: none; }
  button {
    background: #14B8A6; color: white; border: none; border-radius: 14px;
    padding: 14px 22px; font-size: 14px; font-weight: 600; cursor: pointer;
    font-family: inherit; min-height: 48px;
  }
  button.secondary { background: #2A3540; }
  button.danger { background: #EF4444; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-row {
    display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;
    width: 100%; max-width: 380px;
  }
  .btn-row button { flex: 1; min-width: 130px; }
  .info { font-size: 13px; color: #8B98A5; text-align: center; margin: 8px 0 14px; padding: 0 8px; }
  .info.error { color: #EF4444; }
  .result-card {
    background: #151B22; border: 1px solid #2A3540; border-radius: 16px;
    padding: 18px; margin-top: 14px; width: 100%; max-width: 380px;
  }
  .result-head {
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 12px; margin-bottom: 12px;
  }
  .food-name { font-size: 19px; font-weight: 700; }
  .confidence { font-size: 11px; color: #5A6A7A; margin-top: 3px; }
  .cal-badge {
    background: rgba(20, 184, 166, 0.13); padding: 10px 14px;
    border-radius: 12px; text-align: center; min-width: 76px;
  }
  .cal-num { font-size: 22px; font-weight: 700; color: #5EEAD4; }
  .cal-label { font-size: 10px; color: #5A6A7A; }
  .macros { display: flex; gap: 8px; margin-bottom: 10px; }
  .macro {
    flex: 1; padding: 10px 6px; border-radius: 10px; text-align: center;
    background: #1E262F;
  }
  .macro-label { font-size: 10px; color: #8B98A5; }
  .macro-val { font-size: 13px; font-weight: 600; margin-top: 2px; }
  .advice {
    background: rgba(59, 130, 246, 0.07); padding: 12px;
    border-radius: 10px; font-size: 12px; color: #8B98A5;
    font-style: italic; margin-bottom: 12px; line-height: 1.4;
  }
  .loading {
    position: absolute; inset: 0; background: rgba(0,0,0,0.72);
    display: none; flex-direction: column; align-items: center;
    justify-content: center; gap: 12px; color: white; font-weight: 600;
  }
  .loading.show { display: flex; }
  .spinner {
    width: 38px; height: 38px;
    border: 3px solid rgba(94, 234, 212, 0.25);
    border-top-color: #5EEAD4; border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .hidden { display: none !important; }
  .success-box { text-align: center; padding: 8px; }
  .success-box .emoji { font-size: 44px; margin-bottom: 8px; }
  .success-box .title { font-weight: 600; margin-bottom: 6px; }
  .success-box .sub { color: #8B98A5; font-size: 13px; margin-bottom: 16px; }
</style>
</head>
<body>
  <h1>Yemek Tara</h1>

  <div class="frame">
    <div class="placeholder" id="placeholder">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 15.5A3.5 3.5 0 1 0 12 8.5a3.5 3.5 0 0 0 0 7zm0-9c3.04 0 5.5 2.46 5.5 5.5S15.04 17.5 12 17.5 6.5 15.04 6.5 12 8.96 6.5 12 6.5zm-3-4l-1.83 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6.5c0-1.1-.9-2-2-2h-3.17L15 2.5H9z"/></svg>
      <div>Kamerayı başlatmak için aşağıdaki butona bas</div>
    </div>
    <video id="video" autoplay playsinline muted></video>
    <img class="preview" id="preview" />
    <canvas id="canvas"></canvas>
    <div class="loading" id="loading">
      <div class="spinner"></div>
      <div id="loadingText">Yapay zeka analiz ediyor...</div>
    </div>
  </div>

  <div class="info" id="info">Aşağıdan kamerayı başlat, yemeği çerçeveye al ve fotoğraf çek.</div>

  <div class="btn-row" id="btnRow">
    <button id="startBtn" onclick="startCamera()">Kamerayı Aç</button>
    <button id="captureBtn" class="hidden" onclick="captureAndAnalyze()">Fotoğraf Çek</button>
    <button id="switchBtn" class="secondary hidden" onclick="switchCamera()">Çevir</button>
    <button id="retryBtn" class="secondary hidden" onclick="reset()">Tekrar Dene</button>
  </div>

  <div id="result"></div>

<script>
const USER_ID = "__USER_ID__";
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const preview = document.getElementById('preview');
const placeholder = document.getElementById('placeholder');
const loading = document.getElementById('loading');
const loadingText = document.getElementById('loadingText');
const info = document.getElementById('info');
const startBtn = document.getElementById('startBtn');
const captureBtn = document.getElementById('captureBtn');
const switchBtn = document.getElementById('switchBtn');
const retryBtn = document.getElementById('retryBtn');
const result = document.getElementById('result');

let stream = null;
let facingMode = 'environment';
let lastResult = null;

function setInfo(msg, isError) {
  info.textContent = msg;
  info.className = 'info' + (isError ? ' error' : '');
}

async function startCamera() {
  try {
    if (stream) stream.getTracks().forEach(t => t.stop());
    const constraints = {
      video: {
        facingMode: { ideal: facingMode },
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    };
    stream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = stream;
    placeholder.classList.add('hidden');
    startBtn.classList.add('hidden');
    retryBtn.classList.add('hidden');
    captureBtn.classList.remove('hidden');
    switchBtn.classList.remove('hidden');
    video.style.display = 'block';
    preview.style.display = 'none';
    setInfo('Yemeği çerçeveye al ve "Fotoğraf Çek"e bas.');
  } catch (err) {
    let msg = err.message || String(err);
    if (err.name === 'NotAllowedError') msg = 'Kamera izni reddedildi. Tarayıcı ayarlarından izin ver.';
    else if (err.name === 'NotFoundError') msg = 'Bu cihazda kamera bulunamadı.';
    else if (err.name === 'NotReadableError') msg = 'Kamera başka bir uygulama tarafından kullanılıyor.';
    setInfo('Kamera açılamadı: ' + msg, true);
    startBtn.classList.remove('hidden');
    captureBtn.classList.add('hidden');
    switchBtn.classList.add('hidden');
  }
}

async function switchCamera() {
  facingMode = (facingMode === 'environment') ? 'user' : 'environment';
  await startCamera();
}

async function captureAndAnalyze() {
  if (!stream) return;
  const w = video.videoWidth || 640;
  const h = video.videoHeight || 480;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, w, h);
  const b64 = canvas.toDataURL('image/jpeg', 0.88);

  stream.getTracks().forEach(t => t.stop());
  stream = null;
  video.srcObject = null;
  preview.src = b64;
  preview.style.display = 'block';
  video.style.display = 'none';

  captureBtn.classList.add('hidden');
  switchBtn.classList.add('hidden');
  loading.classList.add('show');
  loadingText.textContent = 'Yapay zeka analiz ediyor...';
  setInfo('Analiz ediliyor, birkaç saniye sürebilir...');

  try {
    const resp = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: b64 }),
    });
    const data = await resp.json();
    loading.classList.remove('show');
    if (data.status === 'ok') {
      lastResult = data;
      renderResult(data);
    } else {
      setInfo('Hata: ' + (data.message || 'Bilinmeyen'), true);
      retryBtn.classList.remove('hidden');
    }
  } catch (err) {
    loading.classList.remove('show');
    setInfo('Bağlantı hatası: ' + err.message, true);
    retryBtn.classList.remove('hidden');
  }
}

function renderResult(d) {
  const m = d.macros || {};
  result.innerHTML = `
    <div class="result-card">
      <div class="result-head">
        <div>
          <div class="food-name">${escapeHtml(d.food_name)}</div>
          <div class="confidence">Güven: %${d.confidence}</div>
        </div>
        <div class="cal-badge">
          <div class="cal-num">${escapeHtml(String(d.calories))}</div>
          <div class="cal-label">kcal</div>
        </div>
      </div>
      <div class="macros">
        <div class="macro" style="color:#F87171"><div class="macro-label">Protein</div><div class="macro-val">${escapeHtml(m.protein || '?')}</div></div>
        <div class="macro" style="color:#FBBF24"><div class="macro-label">Karb</div><div class="macro-val">${escapeHtml(m.karb || '?')}</div></div>
        <div class="macro" style="color:#A78BFA"><div class="macro-label">Yağ</div><div class="macro-val">${escapeHtml(m.yag || '?')}</div></div>
      </div>
      <div class="advice">${escapeHtml(d.advice || '')}</div>
      <div class="btn-row">
        <button class="secondary" onclick="reset()">İptal</button>
        <button onclick="saveLog()">Günlüğe Ekle</button>
      </div>
    </div>
  `;
  setInfo('Sonuç hazır. Günlüğüne kaydetmek için "Günlüğe Ekle"ye bas.');
}

async function saveLog() {
  if (!lastResult) return;
  if (!USER_ID) { setInfo('Kullanıcı kimliği bulunamadı, ana sayfaya dönüp tekrar dene.', true); return; }
  try {
    const resp = await fetch('/save-food-log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: USER_ID,
        food_name: lastResult.food_name,
        calories: lastResult.calories,
        protein: (lastResult.macros || {}).protein,
        karb: (lastResult.macros || {}).karb,
        yag: (lastResult.macros || {}).yag,
      }),
    });
    const data = await resp.json();
    if (data.status === 'ok') {
      result.innerHTML = `
        <div class="result-card">
          <div class="success-box">
            <div class="emoji">✅</div>
            <div class="title">Günlüğüne eklendi!</div>
            <div class="sub">${escapeHtml(lastResult.food_name)} • ${escapeHtml(String(lastResult.calories))} kcal</div>
            <div class="btn-row">
              <button class="secondary" onclick="window.close()">Pencereyi Kapat</button>
              <button onclick="reset()">Yeni Tarama</button>
            </div>
          </div>
        </div>
      `;
      setInfo('Kayıt başarılı.');
    } else {
      setInfo('Kayıt hatası: ' + (data.message || ''), true);
    }
  } catch (err) {
    setInfo('Kayıt hatası: ' + err.message, true);
  }
}

function reset() {
  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
  video.srcObject = null;
  video.style.display = 'block';
  preview.style.display = 'none';
  preview.src = '';
  result.innerHTML = '';
  loading.classList.remove('show');
  placeholder.classList.remove('hidden');
  startBtn.classList.remove('hidden');
  captureBtn.classList.add('hidden');
  switchBtn.classList.add('hidden');
  retryBtn.classList.add('hidden');
  lastResult = null;
  setInfo('Aşağıdan kamerayı başlat, yemeği çerçeveye al ve fotoğraf çek.');
}

function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
}
</script>
</body>
</html>
"""


@api.get("/camera-page", response_class=HTMLResponse)
async def camera_page(user_id: str = ""):
    html = CAMERA_HTML.replace("__USER_ID__", user_id or "")
    return HTMLResponse(html)


flet_sub_app = flet_fastapi.app(
    session_handler=flet_main,
    upload_dir=UPLOAD_DIR,
    secret_key=SECRET_KEY,
    web_renderer=ft.WebRenderer.CANVAS_KIT,
)

api.mount("/", flet_sub_app)


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000, log_level="warning")
