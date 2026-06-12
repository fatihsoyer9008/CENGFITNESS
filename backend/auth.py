import hashlib
import os
import re
import sqlite3

from backend import database


PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
HASH_BYTES = 32

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _hash_password(password, salt_hex):
    # sifreyi duz metin saklamiyoruz, tuzlu pbkdf2 ile hashleyip oyle yaziyoruz
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=HASH_BYTES,
    )
    return dk.hex()


def _generate_salt():
    # her kullaniciya kayitta rastgele tuz uretilir
    return os.urandom(SALT_BYTES).hex()


def _constant_time_compare(a, b):
    # karsilastirma suresi icerige gore degismesin diye karakter karakter XOR
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def validate_email(email):
    # basit e-posta format kontrolu
    return bool(email and EMAIL_REGEX.match(email.strip()))


def validate_password(password):
    # minimum uzunluk kontrolu
    if not password or len(password) < 6:
        return False, "Şifre en az 6 karakter olmalı."
    return True, ""


def register(email, password, name, weight_kg, height_cm, age, gender):
    # yeni kullanici kaydi: alanlari dogrula, sifreyi hashle, veritabanina yaz
    if not validate_email(email):
        return False, "Geçerli bir e-posta adresi girin.", None

    ok, msg = validate_password(password)
    if not ok:
        return False, msg, None

    if not name or not name.strip():
        return False, "İsim boş olamaz.", None

    try:
        weight_kg = float(weight_kg)
        height_cm = float(height_cm)
        age = int(age)
        if not (20 <= weight_kg <= 300):
            return False, "Kilo 20-300 kg arasında olmalı.", None
        if not (100 <= height_cm <= 250):
            return False, "Boy 100-250 cm arasında olmalı.", None
        if not (10 <= age <= 120):
            return False, "Yaş 10-120 arasında olmalı.", None
    except (ValueError, TypeError):
        return False, "Kilo, boy ve yaş sayısal olmalı.", None

    if gender not in ("Erkek", "Kadın", "Diğer"):
        return False, "Cinsiyet seçimi geçersiz.", None

    salt = _generate_salt()
    pw_hash = _hash_password(password, salt)

    try:
        user_id = database.create_user(
            email=email,
            password_hash=pw_hash,
            salt=salt,
            name=name.strip(),
            weight_kg=weight_kg,
            height_cm=height_cm,
            age=age,
            gender=gender,
        )
        return True, "Kayıt başarılı!", user_id
    except sqlite3.IntegrityError:
        return False, "Bu e-posta zaten kayıtlı.", None
    except Exception as e:
        return False, f"Kayıt hatası: {e}", None


def login(email, password):
    # e-posta + sifre dogrulamasi, basariliysa kullanici bilgisini doner
    if not email or not password:
        return False, "E-posta ve şifre gerekli.", None

    user = database.get_user_by_email(email)
    if not user:
        # kullanici yok desek bilgi sizdirmis oluruz, ayni mesaji veriyoruz
        return False, "E-posta veya şifre hatalı.", None

    expected = _hash_password(password, user["salt"])
    if not _constant_time_compare(expected, user["password_hash"]):
        return False, "E-posta veya şifre hatalı.", None

    user.pop("password_hash", None)
    user.pop("salt", None)
    return True, "Giriş başarılı!", user
