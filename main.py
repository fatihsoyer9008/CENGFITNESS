import os
import json
import time
import threading
import base64
import logging
import traceback

import flet as ft
import requests
import cv2
from flask import Flask, jsonify
import google.generativeai as genai
from ultralytics import YOLO

import database
import auth
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
SERVER_URL = "http://127.0.0.1:5000"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY bulunamadı. Proje kökünde .env dosyası oluşturup "
        ".env.example'daki gibi anahtarınızı girin."
    )

genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 0.1,
    "response_mime_type": "application/json",
    "response_schema": {
        "type": "OBJECT",
        "properties": {
            "cal": {"type": "INTEGER"},
            "p":   {"type": "STRING"},
            "k":   {"type": "STRING"},
            "y":   {"type": "STRING"},
            "tavsiye": {"type": "STRING"},
        },
        "required": ["cal", "p", "k", "y", "tavsiye"],
    }
}

gemini_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
)


def get_nutrition_from_gemini(food_name):
    prompt = f"""
    Kullanici kameraya '{food_name}' gosterdi.
    Besin degerlerini Turkiye'deki doyurucu, standart 1 tam porsiyon icin hesapla.
    SADECE JSON formatinda yanit ver:
    {{
        "cal": 450,
        "p": "25g",
        "k": "40g",
        "y": "20g",
        "tavsiye": "1 standart porsiyon (yaklasik X gram) icin hesaplandi. Kisa tavsiye."
    }}
    """
    try:
        response = gemini_model.generate_content(prompt)
        try:
            text = response.text
        except ValueError:
            return {"cal": "?", "p": "?", "k": "?", "y": "?",
                    "tavsiye": "Yapay zeka guvenlik filtresine takildi."}
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            return {"cal": "?", "p": "?", "k": "?", "y": "?",
                    "tavsiye": f"JSON hatasi: {e}"}
    except Exception as e:
        print(f"Gemini API hatasi:\n{traceback.format_exc()}")
        return {"cal": "?", "p": "?", "k": "?", "y": "?",
                "tavsiye": f"Hata: {str(e)}"}


print("YOLO modeli yukleniyor...")
model = YOLO(os.path.join(BASE_DIR, "best.pt"))
print("[OK] YOLO modeli hazir.")


app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response


camera_lock = threading.Lock()
model_lock = threading.Lock()
latest_frame = None
cap = None
is_streaming = False
camera_error = None


def predict_food(cap_frame):
    with model_lock:
        results = model(cap_frame)

    try:
        if hasattr(results[0], "probs") and results[0].probs is not None:
            names = results[0].names
            idx = results[0].probs.top1
            predicted = names[idx]
            conf = float(results[0].probs.top1conf)
        elif hasattr(results[0], "boxes") and results[0].boxes is not None and len(results[0].boxes) > 0:
            names = results[0].names
            idx = int(results[0].boxes.cls[0].item())
            predicted = names[idx]
            conf = float(results[0].boxes.conf[0].item())
        else:
            predicted = "Bilinmiyor"
            conf = 0.0
    except Exception as e:
        print(f"Tahmin hatasi: {e}")
        predicted = "Bilinmiyor"
        conf = 0.0

    pct = round(conf * 100, 1)

    if predicted == "Bilinmiyor":
        stats = {"cal": "?", "p": "?", "k": "?", "y": "?",
                 "tavsiye": "Yiyecek tespit edilemedi."}
    else:
        stats = get_nutrition_from_gemini(predicted)

    return predicted, pct, stats


def encode_frame_b64(cap_frame, quality=95):
    ok, buf = cv2.imencode(".jpg", cap_frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return None
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def build_capture_payload(cap_frame):
    predicted, conf, stats = predict_food(cap_frame)
    b64 = encode_frame_b64(cap_frame, quality=95)
    if b64 is None:
        return {"status": "error", "message": "Fotograf islenemedi"}
    return {
        "status": "ok",
        "image": b64,
        "food_name": predicted.replace("_", " ").upper(),
        "confidence": conf,
        "calories": stats.get("cal", "?"),
        "macros": {
            "protein": stats.get("p", "?"),
            "karb":    stats.get("k", "?"),
            "yag":     stats.get("y", "?"),
        },
        "advice": stats.get("tavsiye", "Bilgi alinamadi."),
    }


def camera_thread():
    global latest_frame, cap, is_streaming, camera_error
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        camera_error = "Kamera acilamadi. Baska bir uygulama tarafindan kullaniliyor olabilir."
        is_streaming = False
        if cap:
            cap.release()
            cap = None
        return

    camera_error = None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while is_streaming:
        ret, frame = cap.read()
        if ret:
            h, w, _ = frame.shape
            mn = min(h, w)
            sx, sy = (w - mn) // 2, (h - mn) // 2
            cropped = frame[sy:sy + mn, sx:sx + mn]
            resized = cv2.resize(cropped, (340, 340))
            with camera_lock:
                latest_frame = resized
        else:
            camera_error = "Kameradan goruntu alinamadi."
        time.sleep(0.01)

    if cap:
        cap.release()
        cap = None


@app.route("/start")
def start_camera():
    global is_streaming, latest_frame, camera_error
    if not is_streaming:
        camera_error = None
        with camera_lock:
            latest_frame = None
        is_streaming = True
        threading.Thread(target=camera_thread, daemon=True).start()
    return jsonify({"status": "ok"})


@app.route("/stop")
def stop_camera():
    global is_streaming, latest_frame, camera_error
    is_streaming = False
    camera_error = None
    with camera_lock:
        latest_frame = None
    return jsonify({"status": "ok"})


@app.route("/frame")
def frame():
    if not is_streaming:
        return jsonify({"status": "error", "message": camera_error or "Kamera kapali"}), 503

    with camera_lock:
        current = latest_frame.copy() if latest_frame is not None else None

    if current is None:
        return jsonify({"status": "error", "message": camera_error or "Kamera hazirlaniyor"}), 503

    ok, buf = cv2.imencode(".jpg", current, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    if not ok:
        return jsonify({"status": "error", "message": "Goruntu islenemedi"}), 500
    b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
    return jsonify({"status": "ok", "image": b64})


@app.route("/capture")
def capture():
    with camera_lock:
        cap_frame = latest_frame.copy() if latest_frame is not None else None
    if cap_frame is None:
        return jsonify({"status": "error", "message": "Kamera hazir degil"})
    return jsonify(build_capture_payload(cap_frame))


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


def flet_main(page):
    page.title = "CENG FITNESS"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = ui_pages.BG_DARK
    page.padding = 0

    page.theme = ft.Theme(
        color_scheme_seed=ui_pages.PRIMARY,
        use_material3=True,
    )

    view_builders = {
        "/login":    lambda: ui_pages.build_login_view(page),
        "/register": lambda: ui_pages.build_register_view(page),
        "/":         lambda: ui_pages.build_dashboard_view(page),
        "/scan":     lambda: ui_pages.build_scan_view(page, SERVER_URL),
        "/food":     lambda: ui_pages.build_food_log_view(page),
        "/exercise": lambda: ui_pages.build_exercise_view(page),
        "/muscle":   lambda: ui_pages.build_muscle_view(page),
        "/stats":    lambda: ui_pages.build_stats_view(page),
        "/profile":  lambda: ui_pages.build_profile_view(page),
    }

    def route_change(e):
        try:
            dlg = getattr(page, "dialog", None)
            if dlg is not None and getattr(dlg, "open", False):
                dlg.open = False
            for ov in list(getattr(page, "overlay", []) or []):
                if getattr(ov, "open", False):
                    ov.open = False
        except Exception:
            pass

        page.views.clear()
        route = page.route or "/"

        user_id = page.session.get("user_id")
        public_routes = ("/login", "/register")

        if not user_id and route not in public_routes:
            route = "/login"
            page.route = "/login"
        elif user_id and route in public_routes:
            route = "/"
            page.route = "/"

        builder = view_builders.get(route, view_builders["/"])
        try:
            page.views.append(builder())
        except Exception as ex:
            traceback.print_exc()
            page.views.append(ft.View(
                route="/error",
                bgcolor=ui_pages.BG_DARK,
                controls=[
                    ft.Container(
                        padding=40,
                        content=ft.Column([
                            ft.Icon(ft.Icons.ERROR, color=ui_pages.DANGER, size=40),
                            ft.Text(f"Sayfa yuklenemedi: {ex}",
                                    color=ui_pages.TEXT_PRIMARY, size=14),
                            ft.FilledButton("Ana sayfa", on_click=lambda e: page.go("/")),
                        ], spacing=12, horizontal_alignment="center"),
                    )
                ],
            ))

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


def run_flask():
    app.run(host="127.0.0.1", port=5000, threaded=True, debug=False, use_reloader=False)


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    time.sleep(1.5)

    try:
        ft.app(target=flet_main, view=ft.AppView.WEB_BROWSER, port=8000)
    except Exception as e:
        print(f"Flet baslatma hatasi: {e}")
