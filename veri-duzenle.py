import os
import shutil

# Klasör yollarını kendi sistemine göre kontrol et
orijinal_images_yolu = "datasets/food-101/images"
meta_yolu = "datasets/food-101/meta"
hedef_yol = "datasets/yolo_food101" # YOLO'nun kullanacağı yeni klasör

def verileri_hazirla():
    print("Veri seti hazırlanıyor, bu işlem birkaç dakika sürebilir...")
    
    # train ve test (val) verileri için döngü
    for split, txt_ad in [('train', 'train.txt'), ('val', 'test.txt')]:
        txt_dosyasi = os.path.join(meta_yolu, txt_ad)
        
        with open(txt_dosyasi, 'r') as f:
            satirlar = f.readlines()
            
        for satir in satirlar:
            # Satırlar "elma_turtasi/1005649" formatındadır
            resim_yolu_kisa = satir.strip()
            
            # Sınıf adını (klasör adını) al
            sinif_adi = resim_yolu_kisa.split('/')[0]
            
            # Yeni konumdaki klasörleri oluştur (örn: datasets/yolo_food101/train/elma_turtasi)
            yeni_klasor_yolu = os.path.join(hedef_yol, split, sinif_adi)
            os.makedirs(yeni_klasor_yolu, exist_ok=True)
            
            # Kopyalanacak asıl resim ve yeni yeri
            kaynak_resim = os.path.join(orijinal_images_yolu, f"{resim_yolu_kisa}.jpg")
            hedef_resim = os.path.join(yeni_klasor_yolu, f"{resim_yolu_kisa.split('/')[1]}.jpg")
            
            # Resmi kopyala (eğer henüz kopyalanmadıysa)
            if not os.path.exists(hedef_resim):
                shutil.copy(kaynak_resim, hedef_resim)

    print("İşlem tamam! Veri seti YOLO sınıflandırma için hazır.")

if __name__ == "__main__":
    verileri_hazirla()