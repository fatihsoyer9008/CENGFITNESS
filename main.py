import os
import traceback

import flet as ft
import flet.fastapi as flet_fastapi
import uvicorn

from backend.api import api
from frontend import ui_pages


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# flet'in dosya yukleme linklerini imzalamasi icin gerekli
SECRET_KEY = os.environ.get("FLET_SECRET_KEY", "cengfitness-secret-2026")
os.environ.setdefault("FLET_SECRET_KEY", SECRET_KEY)


def flet_main(page):
    # her yeni kullanici baglantisinda calisir, sayfayi kurar
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
        # sayfa degisirken acik kalan dialog/picker varsa kapat
        dlg = getattr(page, "dialog", None)
        if dlg is not None and getattr(dlg, "open", False):
            dlg.open = False
        for ov in list(getattr(page, "overlay", []) or []):
            if getattr(ov, "open", False):
                ov.open = False

    def error_view(ex):
        # bir sayfa kurulurken hata olursa bos ekran yerine bunu gosteriyoruz
        return ft.View(
            route="/error", bgcolor=ui_pages.BG_DARK,
            controls=[ft.Container(padding=40, content=ft.Column([
                ft.Icon(ft.Icons.ERROR, color=ui_pages.DANGER, size=40),
                ft.Text(f"Sayfa yuklenemedi: {ex}", color=ui_pages.TEXT_PRIMARY, size=14),
                ft.FilledButton("Ana sayfa", on_click=lambda e: page.go("/")),
            ], spacing=12, horizontal_alignment="center"))],
        )

    def route_change(e):
        # rota her degistiginde eski view'i atip yenisini kurar
        try:
            close_open_overlays()
        except Exception:
            pass

        page.views.clear()
        route = page.route or "/"

        # giris yapmamis kullanici login'e, giris yapmis kullanici ana sayfaya
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
        # tarayicinin geri tusu
        if len(page.views) > 1:
            page.views.pop()
            page.go(page.views[-1].route)

    # pencere mobil esigini gecince sayfayi yeniden kur (sidebar <-> drawer gecisi)
    last_mobile = {"v": ui_pages.is_mobile(page)}

    def on_resized(e):
        # esik degisimi varsa mevcut sayfayi yeni yerlesimle kur
        now_mobile = ui_pages.is_mobile(page)
        if now_mobile != last_mobile["v"]:
            last_mobile["v"] = now_mobile
            route_change(None)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.on_resized = on_resized
    page.go(page.route or "/")


# Flet arayuzunu ayni FastAPI uygulamasinin altina koyuyoruz,
# boylece tek port uzerinden hem UI hem API sunuluyor (tunnel icin sart)
flet_sub_app = flet_fastapi.app(
    session_handler=flet_main,
    upload_dir=UPLOAD_DIR,
    secret_key=SECRET_KEY,
    web_renderer=ft.WebRenderer.CANVAS_KIT,
)

api.mount("/", flet_sub_app)


if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000, log_level="warning")
