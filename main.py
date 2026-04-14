import flet as ft
import requests
import threading
import time
import base64
import cv2
from flask import Flask, Response, jsonify
import logging

# =====================================================================
# 1. BÖLÜM: FLASK SUNUCUSU & YAPAY ZEKA (ARKA PLAN)
# =====================================================================

app = Flask(__name__)
SERVER_URL = "http://127.0.0.1:5000"

# --- WEB TARAYICISI GÜVENLİK İZNİ (CORS FIX) ---
# Tarayıcının kamerayı engellememesi için gereken geçiş izni
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
# -----------------------------------------------

camera_lock = threading.Lock()
model_lock = threading.Lock()
latest_frame = None
cap = None
is_streaming = False
camera_error = None
AUTO_CAPTURE_THRESHOLD = 70.0
AUTO_DETECT_INTERVAL = 0.8

from ultralytics import YOLO
logging.getLogger("ultralytics").setLevel(logging.ERROR)

print("🧠 Yapay Zeka Modeli Yükleniyor...")
model = YOLO("best.pt")
print("✅ Model Hazır!")

BESIN_DEGERLERI = {
    "kofte": {"cal": 250, "p": "18g", "k": "10g", "y": "15g", "tavsiye": "Protein deposu, harika tercih!"},
    "salata": {"cal": 50, "p": "1g", "k": "5g", "y": "2g", "tavsiye": "Diyet dostu, lifli ve sağlıklı."},
    "pilav": {"cal": 300, "p": "5g", "k": "45g", "y": "10g", "tavsiye": "Yüksek karbonhidrat, enerji verir."},
    "tavuk_durum": {"cal": 400, "p": "25g", "k": "35g", "y": "15g", "tavsiye": "Pratik ve doyurucu."}
}

def predict_food(cap_frame):
    with model_lock:
        results = model(cap_frame)

    try:
        isimler = results[0].names
        en_iyi_tahmin_index = results[0].probs.top1
        predicted_class = isimler[en_iyi_tahmin_index]

        guven_skoru = float(results[0].probs.top1conf)
        yuzde_skor = round(guven_skoru * 100, 1)
    except Exception:
        predicted_class = "Bilinmiyor"
        yuzde_skor = 0.0

    stats = BESIN_DEGERLERI.get(
        predicted_class,
        {"cal": "?", "p": "?", "k": "?", "y": "?", "tavsiye": "Sistemde kayıtlı değil."}
    )

    return predicted_class, yuzde_skor, stats

def encode_frame_base64(cap_frame, quality=95):
    ok, buf = cv2.imencode('.jpg', cap_frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        return None
    return base64.b64encode(buf.tobytes()).decode('utf-8')

def build_capture_payload(cap_frame, status="ok"):
    predicted_class, yuzde_skor, stats = predict_food(cap_frame)
    b64 = encode_frame_base64(cap_frame, quality=95)

    if b64 is None:
        return {"status": "error", "message": "Fotoğraf işlenemedi"}

    return {
        "status": status,
        "image": b64,
        "food_name": predicted_class.replace("_", " ").upper(),
        "confidence": yuzde_skor,
        "calories": stats["cal"],
        "macros": {"protein": stats["p"], "karb": stats["k"], "yag": stats["y"]},
        "advice": stats["tavsiye"]
    }

def camera_thread():
    global latest_frame, cap, is_streaming, camera_error
    # Windows'ta kameranın anında açılması için CAP_DSHOW eklendi
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        camera_error = "Kamera açılamadı. Kamera başka bir uygulama tarafından kullanılıyor olabilir."
        is_streaming = False
        cap.release()
        cap = None
        return

    camera_error = None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while is_streaming:
        ret, cap_frame = cap.read()
        if ret:
            h, w, _ = cap_frame.shape
            min_dim = min(h, w)
            sx, sy = (w - min_dim) // 2, (h - min_dim) // 2
            cropped = cap_frame[sy:sy+min_dim, sx:sx+min_dim]
            resized = cv2.resize(cropped, (320, 320))
            with camera_lock:
                latest_frame = resized
        else:
            camera_error = "Kameradan görüntü alınamadı."
        time.sleep(0.01)

    if cap:
        cap.release()
        cap = None

def generate_mjpeg():
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 65]
    while True:
        if not is_streaming: break
        with camera_lock:
            current_frame = latest_frame
        if current_frame is None:
            time.sleep(0.1)
            continue
        _, buf = cv2.imencode('.jpg', current_frame, encode_param)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')
        time.sleep(0.04)

@app.route('/video_feed')
def video_feed():
    if not is_streaming:
        return "Kamera kapalı", 404
    return Response(generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start')
def start_camera():
    global is_streaming, latest_frame, camera_error
    if not is_streaming:
        camera_error = None
        with camera_lock:
            latest_frame = None
        is_streaming = True
        threading.Thread(target=camera_thread, daemon=True).start()
    return jsonify({"status": "ok"})

@app.route('/stop')
def stop_camera():
    global is_streaming, latest_frame, camera_error
    is_streaming = False
    camera_error = None
    with camera_lock:
        latest_frame = None
    return jsonify({"status": "ok"})

@app.route('/frame')
def frame():
    if not is_streaming:
        return jsonify({"status": "error", "message": camera_error or "Kamera kapalı"}), 503

    with camera_lock:
        current_frame = latest_frame.copy() if latest_frame is not None else None

    if current_frame is None:
        return jsonify({"status": "error", "message": camera_error or "Kamera hazırlanıyor"}), 503

    ok, buf = cv2.imencode('.jpg', current_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
    if not ok:
        return jsonify({"status": "error", "message": "Görüntü işlenemedi"}), 500

    b64 = base64.b64encode(buf.tobytes()).decode('utf-8')
    return jsonify({"status": "ok", "image": b64})

@app.route('/capture')
def capture():
    with camera_lock:
        cap_frame = latest_frame.copy() if latest_frame is not None else None

    if cap_frame is None:
        return jsonify({"status": "error", "message": "Kamera hazır değil"})

    return jsonify(build_capture_payload(cap_frame))

@app.route('/auto_capture')
def auto_capture():
    with camera_lock:
        cap_frame = latest_frame.copy() if latest_frame is not None else None

    if cap_frame is None:
        return jsonify({"status": "waiting", "message": "Kamera hazırlanıyor"})

    predicted_class, yuzde_skor, stats = predict_food(cap_frame)

    if yuzde_skor <= AUTO_CAPTURE_THRESHOLD:
        return jsonify({
            "status": "waiting",
            "food_name": predicted_class.replace("_", " ").upper(),
            "confidence": yuzde_skor,
            "threshold": AUTO_CAPTURE_THRESHOLD
        })

    b64 = encode_frame_base64(cap_frame, quality=95)
    if b64 is None:
        return jsonify({"status": "error", "message": "Fotoğraf işlenemedi"})

    return jsonify({
        "status": "detected",
        "image": b64,
        "food_name": predicted_class.replace("_", " ").upper(),
        "confidence": yuzde_skor,
        "threshold": AUTO_CAPTURE_THRESHOLD,
        "calories": stats["cal"],
        "macros": {"protein": stats["p"], "karb": stats["k"], "yag": stats["y"]},
        "advice": stats["tavsiye"]
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})


# =====================================================================
# 2. BÖLÜM: FLET ARAYÜZÜ (ÖN YÜZ)
# =====================================================================

def main(page: ft.Page):
    page.title = "CENG FİTNESS"
    page.theme_mode = "light"
    page.horizontal_alignment = "center"
    page.scroll = "auto"
    page.padding = 30

    TRANSPARENT_PIXEL = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    page.appbar = ft.AppBar(
        title=ft.Text("CENG FİTNESS", weight="bold", color="white"),
        center_title=True,
        bgcolor="teal700",
    )

    camera_stream = ft.Image(
        src=f"data:image/png;base64,{TRANSPARENT_PIXEL}",
        width=300, height=300, fit="cover", border_radius=20, visible=False,
        gapless_playback=True
    )

    placeholder = ft.Container(
        width=300, height=300, bgcolor="grey200", border_radius=20,
        content=ft.Icon(ft.Icons.RESTAURANT, size=72, color="grey400"),
        alignment="center"
    )

    frozen_image = ft.Image(
        src=f"data:image/png;base64,{TRANSPARENT_PIXEL}",
        width=300, height=300, fit="cover", border_radius=20, visible=False,
        gapless_playback=True
    )

    analyze_overlay = ft.Container(
        width=300, height=300, bgcolor="#AA000000",
        border_radius=20, alignment="center", visible=False,
        content=ft.Column([
            ft.ProgressRing(color="teal200"),
            ft.Text("Yapay Zeka Analiz Ediyor...", color="white", weight="bold")
        ], alignment="center", horizontal_alignment="center")
    )

    camera_stack = ft.Stack([placeholder, camera_stream, frozen_image, analyze_overlay], width=300, height=300)

    result_card = ft.Card(
        visible=False,
        content=ft.Container(
            padding=20, width=320,
            content=ft.Column([], horizontal_alignment="center")
        )
    )

    info_text = ft.Text("Sistem hazır! Kamerayı açabilirsiniz.", color="teal")
    state = {"mode": "idle", "poller_id": 0}

    action_btn = ft.IconButton(
        icon=ft.Icons.VIDEOCAM,
        icon_color="white",
        icon_size=34,
        bgcolor="teal",
        width=64,
        height=64,
        padding=0,
        tooltip="Kamerayı Aç",
        on_click=lambda e: handle_action(e),
    )

    def show_idle_error(message):
        state["mode"] = "idle"
        placeholder.visible = True
        camera_stream.visible = False
        frozen_image.visible = False
        analyze_overlay.visible = False
        result_card.visible = False
        action_btn.disabled = False
        action_btn.icon = ft.Icons.VIDEOCAM
        action_btn.tooltip = "Kamerayı Aç"
        action_btn.bgcolor = "teal"
        info_text.visible = True
        info_text.value = message
        page.update()

    def display_result(resp, automatic=False):
        state["mode"] = "result"
        state["poller_id"] += 1
        camera_stream.visible = False
        placeholder.visible = False
        frozen_image.src = f"data:image/jpeg;base64,{resp['image']}"
        frozen_image.visible = True

        food_name = resp.get("food_name", "BİLİNMİYOR")
        conf = resp.get("confidence", 0.0)
        cal = resp.get("calories", 0)
        macros = resp.get("macros", {"protein": "0g", "karb": "0g", "yag": "0g"})
        advice = resp.get("advice", "")

        result_card.content.content.controls = [
            ft.Text(f"{food_name} (%{conf})", size=22, weight="bold"),
            ft.Divider(height=10),
            ft.Text(f"{cal} kcal", size=28, color="teal700", weight="bold"),
            ft.Row([
                ft.Text(f"P: {macros['protein']}", color="red", weight="bold"),
                ft.Text(f"K: {macros['karb']}", color="orange", weight="bold"),
                ft.Text(f"Y: {macros['yag']}", color="amber", weight="bold")
            ], alignment="spaceAround"),
            ft.Container(
                margin=ft.margin.only(top=10), padding=10, bgcolor="blue50", border_radius=10,
                content=ft.Text(f"💡 {advice}", color="blue800", italic=True, text_align="center")
            )
        ]

        analyze_overlay.visible = False
        result_card.visible = True
        action_btn.disabled = False
        action_btn.icon = ft.Icons.REPLAY
        action_btn.tooltip = "Yeni Tarama"
        action_btn.bgcolor = "teal"
        info_text.visible = True
        info_text.value = (
            f"%{conf} güvenle otomatik yakalandı. Yeni tarama için tıklayın."
            if automatic else
            "Yeni tarama için tıklayın."
        )
        page.update()

    def start_frame_poller():
        state["poller_id"] += 1
        poller_id = state["poller_id"]

        def poll():
            missed_frames = 0
            next_detect_at = time.monotonic() + 0.8
            while state["mode"] == "streaming" and state["poller_id"] == poller_id:
                try:
                    resp = requests.get(f"{SERVER_URL}/frame", timeout=1)
                    data = resp.json()

                    if data.get("status") == "ok":
                        missed_frames = 0
                        camera_stream.src = f"data:image/jpeg;base64,{data['image']}"

                        if time.monotonic() >= next_detect_at:
                            next_detect_at = time.monotonic() + AUTO_DETECT_INTERVAL
                            auto_resp = requests.get(f"{SERVER_URL}/auto_capture", timeout=8)
                            auto_data = auto_resp.json()

                            if auto_data.get("status") == "detected":
                                if state["mode"] == "streaming" and state["poller_id"] == poller_id:
                                    requests.get(f"{SERVER_URL}/stop", timeout=1)
                                    display_result(auto_data, automatic=True)
                                break

                            if auto_data.get("status") == "waiting":
                                food_name = auto_data.get("food_name", "BİLİNMİYOR")
                                conf = auto_data.get("confidence", 0.0)
                                if conf > 0:
                                    info_text.value = f"Algılanıyor: {food_name} (%{conf}). %70 üstünde otomatik çeker."

                        page.update()
                    else:
                        missed_frames += 1
                        if missed_frames >= 30:
                            requests.get(f"{SERVER_URL}/stop", timeout=1)
                            show_idle_error(data.get("message", "Kamera hazır değil."))
                            break
                except Exception as ex:
                    missed_frames += 1
                    if missed_frames >= 30:
                        print("Frame hatası:", ex)
                        try:
                            requests.get(f"{SERVER_URL}/stop", timeout=1)
                        except Exception:
                            pass
                        show_idle_error("Kameradan görüntü alınamadı.")
                        break

                time.sleep(0.08)

        threading.Thread(target=poll, daemon=True).start()

    def handle_action(e):
        if state["mode"] == "idle":
            try:
                requests.get(f"{SERVER_URL}/start", timeout=2)
                state["mode"] = "streaming"
                placeholder.visible = False
                camera_stream.visible = True
                camera_stream.src = f"data:image/png;base64,{TRANSPARENT_PIXEL}"

                frozen_image.visible = False
                analyze_overlay.visible = False
                result_card.visible = False

                action_btn.icon = ft.Icons.CAMERA
                action_btn.tooltip = "Fotoğraf Çek"
                action_btn.bgcolor = "red400"

                info_text.value = "Yemeği çerçeveye alın ve butona basın."
                page.update()
                start_frame_poller()
            except Exception as ex:
                print("Kamera başlatma hatası:", ex)
                show_idle_error("Kamera başlatılamadı.")

        elif state["mode"] == "streaming":
            state["mode"] = "analyzing"
            action_btn.disabled = True
            analyze_overlay.visible = True
            info_text.visible = False
            page.update()

            def process():
                try:
                    resp = requests.get(f"{SERVER_URL}/capture", timeout=15).json()
                    requests.get(f"{SERVER_URL}/stop", timeout=2)
                    camera_stream.visible = False

                    if resp.get("status") == "ok":
                        display_result(resp)
                        return
                    else:
                        show_idle_error(resp.get("message", "Kamera hazır değil."))
                        return
                except Exception as ex:
                    print("Hata:", ex)
                    try:
                        requests.get(f"{SERVER_URL}/stop", timeout=2)
                    except Exception:
                        pass
                    show_idle_error("Fotoğraf alınırken hata oluştu.")
                    return
                page.update()

            threading.Thread(target=process, daemon=True).start()

        elif state["mode"] == "result":
            state["mode"] = "idle"
            state["poller_id"] += 1
            frozen_image.visible = False
            camera_stream.visible = False
            camera_stream.src = f"data:image/png;base64,{TRANSPARENT_PIXEL}"
            analyze_overlay.visible = False
            placeholder.visible = True
            result_card.visible = False
            action_btn.disabled = False

            action_btn.icon = ft.Icons.VIDEOCAM
            action_btn.tooltip = "Kamerayı Aç"
            action_btn.bgcolor = "teal"
            info_text.value = "Kamerayı açmak için butona basın."
            page.update()

    page.add(ft.Column([
        ft.Container(content=camera_stack, border_radius=20, border=ft.border.all(2, "teal300")),
        ft.Container(height=10),
        info_text,
        result_card,
        ft.Container(height=10),
        ft.Row([action_btn], alignment="center"),
        ft.Container(height=40)
    ], horizontal_alignment="center"))


# =====================================================================
# 3. BÖLÜM: SİSTEMİ BAŞLATMA
# =====================================================================

def run_flask_app():
    app.run(host='127.0.0.1', port=5000, threaded=True, debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    time.sleep(1.5)

    try:
        ft.run(main, view="web_browser", port=8000)
    except:
        ft.app(target=main, view="web_browser", port=8000)
