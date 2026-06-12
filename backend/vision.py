import os
import json
import base64
import traceback

import numpy as np
import cv2
import google.generativeai as genai
from ultralytics import YOLO

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_dotenv():
    # harici paket kurmamak icin .env dosyasini elle okuyoruz
    env_path = os.path.join(ROOT_DIR, ".env")
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
    # analiz basarisiz oldugunda ekrana basilacak bos sablon
    return {"cal": "?", "p": "?", "k": "?", "y": "?", "tavsiye": advice}


def get_nutrition_from_gemini(food_name):
    # YOLO'nun buldugu yemek adi icin Gemini'den porsiyon bazli besin degerleri istiyoruz
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
model = YOLO(os.path.join(ROOT_DIR, "best.pt"))
print("[OK] YOLO modeli hazir.")


def decode_image_b64(b64):
    # base64 metnini opencv goruntusune cevirir, bozuksa None doner
    if not b64:
        return None
    # tarayicidan "data:image/jpeg;base64,..." formatinda gelirse basini at
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return None
    arr = np.frombuffer(raw, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def prepare_frame(img, target=480):
    # ortadan kare kirpip kucultuyoruz, model kare goruntuyle calisiyor
    h, w = img.shape[:2]
    mn = min(h, w)
    sx, sy = (w - mn) // 2, (h - mn) // 2
    cropped = img[sy:sy + mn, sx:sx + mn]
    return cv2.resize(cropped, (target, target))


def predict_food(frame):
    # once YOLO ile yemegi taniyoruz, sonra Gemini'den besin degerlerini aliyoruz
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
    # goruntuyu jpeg'e cevirip base64 string olarak doner
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return base64.b64encode(buf.tobytes()).decode("utf-8") if ok else None


def build_capture_payload(frame):
    # analiz sonucunu arayuzun bekledigi JSON formatina toplar
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
