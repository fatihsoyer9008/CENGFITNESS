import cv2
from ultralytics import YOLO

# Eğitilmiş KENDİ sınıflandırma modelimizi yüklüyoruz
model = YOLO('runs/classify/train/weights/best.pt')

cap = cv2.VideoCapture(1)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Görüntüyü modele ver
    results = model.predict(source=frame, show=False)
    
    # Sınıflandırma sonuçlarını al
    isimler = model.names
    en_iyi_tahmin_index = results[0].probs.top1      # En yüksek ihtimalli sonucun ID'si
    guven_skoru = float(results[0].probs.top1conf)   # Ne kadar emin olduğu (0 ile 1 arası)
    
    yemek_adi = isimler[en_iyi_tahmin_index]
    yazi = f"{yemek_adi} (%{guven_skoru * 100:.1f})"

    # Sadece belli bir güven skorunun üzerindeyse ekrana yazdır (Örn: %50'den eminse)
    if guven_skoru > 0.50:
        cv2.putText(frame, yazi, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow("Canli Yemek Siniflandirma", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()