# CENG FITNESS

Kalori ve antrenman takibi için geliştirdiğimiz web tabanlı bir fitness uygulaması.
Yemeğin fotoğrafını çekiyorsun, yapay zeka ne olduğunu tanıyıp kalorisini ve makro
değerlerini çıkarıyor; egzersizlerini kaydediyorsun, yaktığın kaloriyi ve kas
gelişimini takip ediyorsun.

Arayüz Python (Flet) ile yazıldı, tek bir FastAPI sunucusu üzerinden çalışıyor.
Telefondan, bilgisayardan, aynı linkten kullanılabiliyor.

## Özellikler

- **Yemek tarama** – Telefon ya da bilgisayar kamerasından fotoğraf çek veya
  galeriden seç. YOLO modeli yemeği tanıyor, Google Gemini bir porsiyon için
  kalori/protein/karbonhidrat/yağ değerlerini hesaplıyor.
- **Yemek günlüğü** – 128 yemeklik hazır listeden porsiyon seçerek ya da elle
  girerek kayıt tutma. Günlük ve haftalık toplamlar.
- **Egzersiz takibi** – 16 kategoride 173 hareket. Süreye göre (kardiyo) veya
  set/tekrar/ağırlığa göre (kuvvet) kayıt. Yakılan kalori MET değerinden otomatik
  hesaplanıyor.
- **Kas gelişimi** – Kas grubuna göre haftalık hacim, hareket bazlı ağırlık ve
  tahmini 1RM grafiği, kişisel rekor (PR) listesi.
- **Kalori takibi** – Bugün / son 24 saat / 7 gün / 30 gün ve özel tarih aralığı
  için alınan-yakılan-net kalori grafikleri.
- **Profil ve vücut ölçüleri** – Kilo, boy, yaş, BMI; ayrıca göğüs/bel/kol vb.
  ölçümlerini kaydedip zaman içindeki değişimini grafikte görme.
- **Mobil uyumlu** – Dar ekranda menü hamburger menüye dönüşüyor. Android, iOS ve
  masaüstü tarayıcılarda kamera erişimi ayrı ayrı ele alındı.

## Kullanılan teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| Arayüz | Flet 0.25.2 (Flutter tabanlı Python UI) |
| Sunucu | FastAPI + Uvicorn |
| Veritabanı | SQLite |
| Görüntü tanıma | YOLO (Ultralytics) – [Food-101](https://www.kaggle.com/datasets/dansbecker/food-101) üzerine eğitildi, 101 yemek sınıfı |
| Besin değeri | Google Gemini (`gemini-2.5-flash`) |
| Grafikler | Flet'in yerleşik LineChart / BarChart bileşenleri |

Flet, FastAPI'nin altına monte edildiği için arayüz ve API tek port (8000)
üzerinden sunuluyor. Bu sayede uygulama tek bir adresten dışarı açılabiliyor;
canlıda Nginx + Cloudflare ile https://cengfitness.com adresinde yayında.

### Kütüphaneler (requirements.txt)

| Paket | Ne işe yarıyor |
|-------|----------------|
| `flet` | Arayüzü oluşturan, Flutter tabanlı Python UI çatısı |
| `flet-web` | Flet'in web/FastAPI desteği; uygulamanın tarayıcıda çalışmasını sağlar |
| `fastapi` | API uç noktalarını (`/analyze`, `/save-food-log` vb.) sunan web çatısı |
| `uvicorn` | FastAPI uygulamasını çalıştıran ASGI sunucusu |
| `requests` | Sunucu içi HTTP istekleri (analiz çağrısı) için |
| `numpy` | Görüntüyü sayısal dizi olarak işlemek için |
| `opencv-python` | Fotoğrafı çözme, ortadan kare kırpma ve yeniden boyutlandırma |
| `ultralytics` | YOLO modelini yükleyip tahmin almak için (PyTorch'u da yanında getirir) |
| `google-generativeai` | Google Gemini'den besin değerlerini almak için |

## Proje yapısı

```
CENGFITNESS/
├── main.py                  Giriş noktası: rota yönetimi, sunucuyu başlatma
├── backend/
│   ├── api.py               FastAPI endpoint'leri (/analyze, /camera-page, ...)
│   ├── vision.py            YOLO + Gemini ile yemek analizi
│   ├── database.py          SQLite işlemleri ve sorgular
│   ├── auth.py              Kayıt / giriş, şifre hash'leme
│   └── camera_page.html     Tarayıcı kamerasıyla çalışan tarama sayfası
├── frontend/
│   └── ui_pages.py          Tüm ekranlar (giriş, panel, yemek, egzersiz, ...)
├── data/
│   ├── foods_data.py        Hazır yemek listesi (128 kayıt)
│   └── exercises_data.py    Egzersiz listesi ve MET değerleri (173 kayıt)
├── best.pt                  Eğitilmiş YOLO model dosyası
├── requirements.txt
└── .env.example
```

Veritabanı dosyası (`cengfitness.db`) ilk çalıştırmada otomatik oluşur,
`.gitignore` ile depodan dışarıda tutulur (kullanıcı verisi gizli kalsın).

## Canlı sürüm

Proje yayında: **https://cengfitness.com**

Sadece uygulamayı kullanmak istiyorsan kurulumla uğraşmana gerek yok; doğrudan
bu adresten hesap oluşturup başlayabilirsin. Uygulama bir Windows sunucuda
çalışıyor, önünde Nginx ters vekil olarak duruyor ve SSL/HTTPS Cloudflare
üzerinden sağlanıyor.

Aşağıdaki adımlar yalnızca projeyi kendi bilgisayarında çalıştırmak isteyenler
içindir.

## Donanım ve yazılım gereksinimleri

**Yazılım**

- İşletim sistemi: Windows, macOS veya Linux
- Python 3.10 veya üzeri
- İnternet bağlantısı – ilk kurulumda paketlerin inmesi ve besin analizi için
  yapılan Gemini API çağrıları gerektiriyor

**Donanım**

- En az 4 GB RAM (8 GB önerilir)
- Yaklaşık 2-3 GB boş disk alanı (PyTorch, Ultralytics ve model dosyaları için)
- GPU şart değil; model CPU üzerinde de çalışır (GPU varsa tahmin daha hızlı olur)

## Kurulum

Python 3.10 veya üzeri gerekiyor.

**1. Depoyu klonla ve sanal ortam kur**

```bash
git clone https://github.com/fatihsoyer9008/CENGFITNESS.git
cd CENGFITNESS
python -m venv venv
```

Sanal ortamı etkinleştir:

```bash
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

**2. Bağımlılıkları yükle (Bu işlem biraz zaman alabilir)**

```bash
pip install -r requirements.txt
```

İlk kurulumda ultralytics ve torch'un inmesi biraz zaman alabilir.

**3. Gemini API anahtarını tanımla**

`.env.example` dosyasını `.env` olarak yeniden adlandır ve kendi anahtarını gir:

```bash
mv .env.example .env
```
```
Proje klasörüne girip oradan .envyi açın içine anahtarı yapıştırın.Anahtarı https://aistudio.google.com/apikey adresinden ücretsiz alabilirsin.
```
```
GEMINI_API_KEY=buraya_kendi_anahtarin
```

`.env` dosyası git'e gönderilmez.

**4. Model dosyası**

`best.pt` (eğitilmiş YOLO modeli) proje kökünde bulunmalı. Depoda zaten mevcut.

## Çalıştırma

```bash
python main.py
```

Sunucu `http://localhost:8000` adresinde açılır. Tarayıcıdan bu adrese gir,
hesap oluştur ve kullanmaya başla.

İlk açılışta YOLO modeli belleğe yüklendiği için birkaç saniye bekleyebilirsin
(`[OK] YOLO modeli hazir.` yazısını görünce hazırdır).

## Telefondan kullanma

Uygulama yayında olduğu için telefondan kullanmak çok basit: tarayıcıdan
**https://cengfitness.com** adresine gir, hesabını oluştur. HTTPS hazır
olduğundan kamerayla tarama izni de doğrudan çalışır.

### Yerelde geliştirirken telefondan test (Cloudflare Tunnel)

Projeyi kendi bilgisayarında çalıştırıp telefondan denemek istersen, kamera
HTTPS gerektirdiği için yerel sunucuyu geçici bir adresle dışarı açabilirsin.
Geliştirme aşamasında kullandığımız yöntem buydu:

```bash
# uygulama çalışırken ayrı bir terminalde
cloudflared tunnel --url http://localhost:8000
```

Komut sana `https://...trycloudflare.com` şeklinde bir adres verir. Bu adresi
telefonun tarayıcısında açtığında uygulama doğrudan çalışır, kamera izni
sorulur. (Operatör DNS'i adresi geç çözebilir; açılmazsa telefonun DNS'ini
`dns.google` yapıp tekrar dene.)

`cloudflared` kurulu değilse: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

## Nasıl çalışıyor

**Yemek tanıma akışı**

1. Tarayıcı, kameradan ya da galeriden alınan fotoğrafı base64 olarak
   `/analyze` endpoint'ine gönderir.
2. Sunucu görüntüyü ortadan kare kırpıp 480×480'e küçültür ve YOLO modeline verir.
3. YOLO yemeği 101 sınıftan birine atar (Food-101 veri seti). Top-1 doğruluk ~%83.
4. Bulunan yemek adı Gemini'ye gönderilir, Gemini bir porsiyon için besin
   değerlerini JSON olarak döner.
5. Sonuç ekranda gösterilir, onaylanırsa yemek günlüğüne kaydedilir.

**Hesaplamalar**

- Yakılan kalori: `MET × kilo × süre(saat)` — MET değerleri egzersiz listesinde tanımlı.
- Tahmini 1RM (Epley formülü): `ağırlık × (1 + tekrar / 30)`
- Kas hacmi: `ağırlık × tekrar × set`
- BMI: `kilo / (boy_metre)²`

**Güvenlik**

Şifreler düz metin olarak tutulmaz; her kullanıcı için rastgele salt üretilip
PBKDF2-HMAC-SHA256 (200.000 tur) ile hash'lenir. Şifre karşılaştırması sabit
sürede yapılır.

## Veri seti

Görüntü tanıma modeli (`best.pt`) **Food-101** veri seti üzerinde eğitildi:

https://www.kaggle.com/datasets/dansbecker/food-101

Veri seti 101 yemek sınıfı ve sınıf başına 1.000 görüntü içeriyor. Eğitimden önce
veriler YOLO sınıflandırma formatına (her sınıf için ayrı klasör) dönüştürüldü;
20 epoch eğitim sonunda top-1 doğruluk ~%83, top-5 doğruluk ~%96 elde edildi.

## Veritabanı

İlk çalıştırmada `cengfitness.db` içinde dört tablo oluşur:

- `users` – kullanıcı bilgileri (e-posta, hash'li şifre, kilo, boy, yaş, cinsiyet)
- `food_log` – yemek kayıtları (ad, kalori, makrolar, kaynak)
- `exercise_log` – egzersiz kayıtları (süre, kalori, set, tekrar, ağırlık)
- `body_measurements` – vücut ölçümleri (kilo, çevre ölçüleri, yağ oranı)

## Notlar

- `best.pt` Food-101 veri setiyle eğitildiği için uluslararası yemeklerde
  daha isabetli. Listede karşılığı olmayan yerel yemekleri görsel olarak en yakın
  sınıfa atayabilir.
- Gemini cevabı bazen güvenlik filtresine takılabilir; bu durumda besin değerleri
  yerine bilgilendirme mesajı gösterilir.
