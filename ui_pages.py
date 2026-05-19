import threading
import time
from datetime import datetime, timedelta

import flet as ft
import requests

import database
import auth
import exercises_data


PRIMARY        = "#14B8A6"
PRIMARY_DARK   = "#0F766E"
PRIMARY_LIGHT  = "#5EEAD4"
ACCENT         = "#22D3EE"

BG_DARK        = "#0B1014"
SURFACE_DARK   = "#151B22"
SURFACE_DARK_2 = "#1E262F"
BORDER_DARK    = "#2A3540"

TEXT_PRIMARY   = "#E6EDF3"
TEXT_SECONDARY = "#8B98A5"
TEXT_MUTED     = "#5A6A7A"

SUCCESS = "#22C55E"
DANGER  = "#EF4444"
WARNING = "#F59E0B"
INFO    = "#3B82F6"

PROTEIN_COLOR = "#F87171"
CARB_COLOR    = "#FBBF24"
FAT_COLOR     = "#A78BFA"


def card(content, padding=20, width=None, **kwargs):
    return ft.Container(
        content=content,
        bgcolor=SURFACE_DARK,
        border_radius=16,
        padding=padding,
        width=width,
        border=ft.border.all(1, BORDER_DARK),
        **kwargs,
    )


def primary_button(text, on_click, icon=None, width=None, expand=False):
    return ft.FilledButton(
        text=text, icon=icon, on_click=on_click, width=width, expand=expand,
        style=ft.ButtonStyle(
            bgcolor=PRIMARY, color="white",
            padding=ft.padding.symmetric(horizontal=24, vertical=18),
            shape=ft.RoundedRectangleBorder(radius=12),
            text_style=ft.TextStyle(weight="bold", size=15),
        ),
    )


def outlined_button(text, on_click, icon=None, width=None):
    return ft.OutlinedButton(
        text=text, icon=icon, on_click=on_click, width=width,
        style=ft.ButtonStyle(
            color=PRIMARY_LIGHT,
            side=ft.BorderSide(1, PRIMARY),
            padding=ft.padding.symmetric(horizontal=24, vertical=18),
            shape=ft.RoundedRectangleBorder(radius=12),
            text_style=ft.TextStyle(weight="bold", size=15),
        ),
    )


def text_field(label, password=False, value="", width=None, on_change=None,
               prefix_icon=None, hint=None, keyboard_type=None):
    return ft.TextField(
        label=label, password=password, can_reveal_password=password,
        value=value, width=width, on_change=on_change,
        prefix_icon=prefix_icon, hint_text=hint,
        border_color=BORDER_DARK, focused_border_color=PRIMARY, cursor_color=PRIMARY,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        text_style=ft.TextStyle(color=TEXT_PRIMARY),
        bgcolor=SURFACE_DARK_2,
        border_radius=12,
        content_padding=ft.padding.all(16),
        keyboard_type=keyboard_type,
    )


def show_snack(page, message, color=PRIMARY):
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color="white", weight="bold"),
        bgcolor=color,
    )
    page.snack_bar.open = True
    page.update()


def refresh_view(page, route=None):
    # page.go(same_route) Flet 0.25.2'de route_change'i async tetiklediği
    # için aynı sayfayı senkron yenilemek için handler'ı direkt çağırıyoruz
    target = route or page.route or "/"
    page.route = target
    handler = getattr(page, "on_route_change", None)
    if callable(handler):
        try:
            handler(None)
            return
        except Exception:
            pass
    page.go(target)


def stat_card(icon, label, value, unit, color):
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color=color, size=20),
                    bgcolor=f"{color}22",
                    padding=8,
                    border_radius=10,
                ),
                ft.Text(label, color=TEXT_SECONDARY, size=12, weight="w500"),
            ], spacing=10),
            ft.Container(height=10),
            ft.Row([
                ft.Text(str(value), size=28, weight="bold", color=TEXT_PRIMARY),
                ft.Text(unit, size=12, color=TEXT_MUTED, weight="w500"),
            ], spacing=6, vertical_alignment="end"),
        ], spacing=0),
        bgcolor=SURFACE_DARK,
        padding=18,
        border_radius=16,
        border=ft.border.all(1, BORDER_DARK),
        expand=True,
    )


def macro_chip(label, value, color):
    return ft.Container(
        content=ft.Column([
            ft.Text(label, size=10, color=color, weight="w500"),
            ft.Text(value, size=14, color=TEXT_PRIMARY, weight="bold"),
        ], horizontal_alignment="center", spacing=2),
        bgcolor=f"{color}22",
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        border_radius=10,
        expand=True,
    )


NAV_ITEMS = [
    ("/",         "DASHBOARD",       "Ana Sayfa"),
    ("/scan",     "CAMERA_ALT",      "Yemek Tara"),
    ("/food",     "RESTAURANT",      "Yemek Günlüğüm"),
    ("/exercise", "FITNESS_CENTER",  "Egzersizler"),
    ("/stats",    "INSIGHTS",        "İstatistikler"),
    ("/profile",  "PERSON",          "Profil"),
]


def build_sidebar(page, current_route):
    user_name = page.session.get("user_name") or "Misafir"

    def go_to(route):
        return lambda e: page.go(route)

    def logout(e):
        page.session.clear()
        page.go("/login")

    nav_buttons = []
    for route, icon_name, label in NAV_ITEMS:
        active = current_route == route
        nav_buttons.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(
                        getattr(ft.Icons, icon_name),
                        color=PRIMARY_LIGHT if active else TEXT_SECONDARY,
                        size=22,
                    ),
                    ft.Text(
                        label,
                        color=TEXT_PRIMARY if active else TEXT_SECONDARY,
                        weight="bold" if active else "w500",
                        size=14,
                    ),
                ], spacing=14),
                padding=ft.padding.symmetric(horizontal=18, vertical=12),
                bgcolor=f"{PRIMARY}22" if active else None,
                border=ft.border.only(
                    left=ft.BorderSide(3, PRIMARY if active else "transparent")
                ),
                border_radius=ft.border_radius.only(top_right=10, bottom_right=10),
                margin=ft.margin.only(right=12, top=2, bottom=2),
                on_click=go_to(route),
                ink=True,
            )
        )

    return ft.Container(
        width=240,
        bgcolor=SURFACE_DARK,
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.FITNESS_CENTER, color=PRIMARY_LIGHT, size=34),
                        ft.Column([
                            ft.Text("CENG", size=18, weight="bold", color=TEXT_PRIMARY),
                            ft.Text("F I T N E S S", size=10, weight="bold", color=TEXT_MUTED),
                        ], spacing=0),
                    ], spacing=10),
                    padding=ft.padding.symmetric(horizontal=20, vertical=20),
                ),
                ft.Divider(height=1, color=BORDER_DARK),
                ft.Container(height=10),

                ft.Column(nav_buttons, spacing=0, expand=True),

                ft.Divider(height=1, color=BORDER_DARK),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.PERSON, color=PRIMARY_LIGHT, size=18),
                            bgcolor=f"{PRIMARY}22",
                            padding=8, border_radius=20,
                        ),
                        ft.Column([
                            ft.Text(user_name, color=TEXT_PRIMARY, size=12, weight="bold"),
                            ft.Text("Hesabım", color=TEXT_MUTED, size=10),
                        ], spacing=0, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            icon_color=DANGER, icon_size=20,
                            on_click=logout, tooltip="Çıkış yap",
                        ),
                    ], spacing=10, vertical_alignment="center"),
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                ),
            ],
            spacing=0,
            expand=True,
        ),
    )


def shell(page, route, title, subtitle, body_controls, fab=None, header_actions=None):
    header_row = [
        ft.Column([
            ft.Text(title, size=22, weight="bold", color=TEXT_PRIMARY),
            ft.Text(subtitle, size=12, color=TEXT_MUTED) if subtitle else ft.Container(),
        ], spacing=2, expand=True),
    ]
    if header_actions:
        header_row.extend(header_actions)

    return ft.View(
        route=route,
        bgcolor=BG_DARK,
        padding=0,
        floating_action_button=fab,
        controls=[
            ft.Row([
                build_sidebar(page, route),
                ft.VerticalDivider(width=1, color=BORDER_DARK),
                ft.Container(
                    expand=True,
                    bgcolor=BG_DARK,
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row(header_row, vertical_alignment="center"),
                            padding=ft.padding.symmetric(horizontal=28, vertical=18),
                            bgcolor=SURFACE_DARK,
                            border=ft.border.only(bottom=ft.BorderSide(1, BORDER_DARK)),
                        ),
                        ft.Container(
                            content=ft.Column(
                                body_controls,
                                spacing=0,
                                scroll=ft.ScrollMode.AUTO,
                                expand=True,
                            ),
                            expand=True,
                            padding=ft.padding.symmetric(horizontal=28, vertical=20),
                        ),
                    ], spacing=0, expand=True),
                ),
            ], spacing=0, expand=True, vertical_alignment="start"),
        ],
    )


def build_login_view(page):
    email = text_field("E-posta", prefix_icon=ft.Icons.EMAIL, width=380)
    password = text_field("Şifre", password=True, prefix_icon=ft.Icons.LOCK, width=380)
    error_text = ft.Text("", color=DANGER, size=13, visible=False)

    def do_login(e):
        ok, msg, user = auth.login(email.value or "", password.value or "")
        if not ok:
            error_text.value = msg
            error_text.visible = True
            page.update()
            return
        page.session.set("user_id", user["id"])
        page.session.set("user_name", user["name"])
        show_snack(page, f"Hoş geldin, {user['name']}!", SUCCESS)
        page.go("/")

    return ft.View(
        route="/login",
        bgcolor=BG_DARK,
        padding=0,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FITNESS_CENTER, color=PRIMARY_LIGHT, size=48),
                        ft.Column([
                            ft.Text("CENG", size=32, weight="bold", color=PRIMARY_LIGHT),
                            ft.Text("F I T N E S S", size=14, weight="bold", color=TEXT_SECONDARY),
                        ], spacing=0),
                    ], alignment="center", spacing=12),
                    ft.Container(height=10),
                    ft.Text("Hesabına giriş yap", size=20, color=TEXT_PRIMARY, weight="w500"),
                    ft.Text("Sağlıklı yaşama devam et", size=13, color=TEXT_MUTED),
                    ft.Container(height=30),
                    card(
                        ft.Column([
                            email, password, error_text,
                            ft.Container(height=8),
                            primary_button("Giriş Yap", do_login, icon=ft.Icons.LOGIN, width=340),
                            ft.Container(
                                content=ft.Row([
                                    ft.Text("Hesabın yok mu?", color=TEXT_SECONDARY, size=13),
                                    ft.TextButton(
                                        "Hemen kayıt ol",
                                        on_click=lambda e: page.go("/register"),
                                        style=ft.ButtonStyle(color=PRIMARY_LIGHT),
                                    ),
                                ], alignment="center", spacing=4),
                                margin=ft.margin.only(top=4),
                            ),
                        ], horizontal_alignment="center", spacing=14),
                        width=400,
                    ),
                ], horizontal_alignment="center", alignment="center"),
            )
        ],
    )


def build_register_view(page):
    name = text_field("Ad Soyad", prefix_icon=ft.Icons.PERSON, width=380)
    email = text_field("E-posta", prefix_icon=ft.Icons.EMAIL, width=380)
    password = text_field("Şifre (en az 6 karakter)", password=True,
                          prefix_icon=ft.Icons.LOCK, width=380)
    weight = text_field("Kilo (kg)", prefix_icon=ft.Icons.MONITOR_WEIGHT, width=180,
                        keyboard_type=ft.KeyboardType.NUMBER)
    height = text_field("Boy (cm)", prefix_icon=ft.Icons.HEIGHT, width=180,
                        keyboard_type=ft.KeyboardType.NUMBER)
    age = text_field("Yaş", prefix_icon=ft.Icons.CAKE, width=180,
                     keyboard_type=ft.KeyboardType.NUMBER)

    gender = ft.Dropdown(
        label="Cinsiyet", width=180,
        border_color=BORDER_DARK, focused_border_color=PRIMARY,
        bgcolor=SURFACE_DARK_2, border_radius=12,
        content_padding=ft.padding.all(16),
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        text_style=ft.TextStyle(color=TEXT_PRIMARY),
        options=[
            ft.dropdown.Option("Erkek"),
            ft.dropdown.Option("Kadın"),
            ft.dropdown.Option("Diğer"),
        ],
    )

    error_text = ft.Text("", color=DANGER, size=13, visible=False)

    def do_register(e):
        ok, msg, uid = auth.register(
            email=email.value or "",
            password=password.value or "",
            name=name.value or "",
            weight_kg=weight.value or 0,
            height_cm=height.value or 0,
            age=age.value or 0,
            gender=gender.value or "",
        )
        if not ok:
            error_text.value = msg
            error_text.visible = True
            page.update()
            return
        page.session.set("user_id", uid)
        page.session.set("user_name", (name.value or "").strip())
        show_snack(page, "Kayıt başarılı! Hoş geldin!", SUCCESS)
        page.go("/")

    return ft.View(
        route="/register",
        bgcolor=BG_DARK,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(vertical=40),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FITNESS_CENTER, color=PRIMARY_LIGHT, size=40),
                        ft.Text("Yeni Hesap", size=28, weight="bold", color=TEXT_PRIMARY),
                    ], alignment="center", spacing=12),
                    ft.Text("Sağlıklı yaşama ilk adım", size=13, color=TEXT_MUTED),
                    ft.Container(height=20),
                    card(
                        ft.Column([
                            name, email, password,
                            ft.Container(height=6),
                            ft.Text("Fiziksel bilgiler", size=13,
                                    color=TEXT_SECONDARY, weight="w500"),
                            ft.Row([weight, height], spacing=10),
                            ft.Row([age, gender], spacing=10),
                            error_text,
                            ft.Container(height=8),
                            primary_button("Kayıt Ol", do_register,
                                           icon=ft.Icons.PERSON_ADD, width=340),
                            ft.Container(
                                content=ft.Row([
                                    ft.Text("Zaten hesabın var mı?", color=TEXT_SECONDARY, size=13),
                                    ft.TextButton(
                                        "Giriş yap",
                                        on_click=lambda e: page.go("/login"),
                                        style=ft.ButtonStyle(color=PRIMARY_LIGHT),
                                    ),
                                ], alignment="center", spacing=4),
                            ),
                        ], horizontal_alignment="center", spacing=12),
                        width=420,
                    ),
                ], horizontal_alignment="center", alignment="center"),
            )
        ],
    )


def quick_action(icon, label, route, page, color=PRIMARY):
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Icon(icon, color=color, size=28),
                bgcolor=f"{color}22", padding=14, border_radius=14,
            ),
            ft.Text(label, color=TEXT_PRIMARY, size=13, weight="w500", text_align="center"),
        ], horizontal_alignment="center", spacing=10),
        on_click=lambda e: page.go(route),
        ink=True,
        padding=16,
        border_radius=14,
        bgcolor=SURFACE_DARK,
        border=ft.border.all(1, BORDER_DARK),
        width=140,
        height=130,
    )


def build_dashboard_view(page):
    user_id = page.session.get("user_id")
    user = database.get_user_by_id(user_id)

    cal_in = database.get_today_calories_in(user_id)
    cal_out = database.get_today_calories_out(user_id)
    net = cal_in - cal_out

    recent_food = database.get_food_logs(user_id, days=1)[:3]
    recent_ex = database.get_exercise_logs(user_id, days=1)[:3]

    activity_items = []
    for f in recent_food:
        activity_items.append(
            ft.Row([
                ft.Icon(ft.Icons.RESTAURANT, color=WARNING, size=18),
                ft.Column([
                    ft.Text(f["food_name"], color=TEXT_PRIMARY, size=14, weight="w500"),
                    ft.Text(f["logged_at"][11:16], color=TEXT_MUTED, size=11),
                ], spacing=0, expand=True),
                ft.Text(f"+{f['calories']} kcal", color=WARNING, size=13, weight="bold"),
            ], spacing=12)
        )
    for ex in recent_ex:
        activity_items.append(
            ft.Row([
                ft.Icon(ft.Icons.FITNESS_CENTER, color=SUCCESS, size=18),
                ft.Column([
                    ft.Text(ex["exercise_name"], color=TEXT_PRIMARY, size=14, weight="w500"),
                    ft.Text(f"{ex['duration_min']} dk • {ex['logged_at'][11:16]}",
                            color=TEXT_MUTED, size=11),
                ], spacing=0, expand=True),
                ft.Text(f"-{ex['calories_burned']} kcal", color=SUCCESS, size=13, weight="bold"),
            ], spacing=12)
        )

    if not activity_items:
        activity_items = [
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.HOURGLASS_EMPTY, color=TEXT_MUTED, size=40),
                    ft.Text("Bugün henüz kayıt yok", color=TEXT_MUTED, size=14),
                    ft.Text("Yemek tara veya egzersiz ekle!", color=TEXT_MUTED, size=12),
                ], horizontal_alignment="center", spacing=6),
                padding=ft.padding.symmetric(vertical=30),
                alignment=ft.alignment.center,
            )
        ]

    body = [
        ft.Container(
            content=ft.Column([
                ft.Text(f"Merhaba, {user['name']} 👋", size=22, weight="bold", color=TEXT_PRIMARY),
                ft.Text(datetime.now().strftime("%d.%m.%Y"),
                        size=13, color=TEXT_SECONDARY),
            ], spacing=2),
        ),
        ft.Container(height=20),

        ft.Text("Bugünün özeti", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(height=8),
        ft.ResponsiveRow([
            ft.Container(stat_card(ft.Icons.RESTAURANT, "Alınan", cal_in, "kcal", WARNING),
                         col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(stat_card(ft.Icons.LOCAL_FIRE_DEPARTMENT, "Yakılan", cal_out, "kcal", SUCCESS),
                         col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(stat_card(ft.Icons.TRENDING_FLAT, "Net", net, "kcal",
                                   DANGER if net > 0 else SUCCESS),
                         col={"xs": 12, "sm": 12, "md": 4}),
        ], spacing=12, run_spacing=12),

        ft.Container(height=24),
        ft.Text("Hızlı erişim", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(height=8),
        ft.Row([
            quick_action(ft.Icons.CAMERA_ALT, "Yemek\nTara", "/scan", page, PRIMARY),
            quick_action(ft.Icons.ADD_CIRCLE, "Yemek\nEkle", "/food", page, WARNING),
            quick_action(ft.Icons.FITNESS_CENTER, "Egzersiz\nEkle", "/exercise", page, SUCCESS),
            quick_action(ft.Icons.INSIGHTS, "Grafik\nGör", "/stats", page, INFO),
        ], spacing=12, wrap=True),

        ft.Container(height=24),
        ft.Row([
            ft.Text("Son aktiviteler", size=14, weight="bold", color=TEXT_PRIMARY),
            ft.TextButton(
                "Tümünü gör",
                on_click=lambda e: page.go("/food"),
                style=ft.ButtonStyle(color=PRIMARY_LIGHT),
            ),
        ], alignment="spaceBetween"),
        card(ft.Column(activity_items, spacing=14)),
        ft.Container(height=40),
    ]

    return shell(page, "/", "Ana Sayfa", "Günlük özetin ve hızlı erişim", body)


def build_scan_view(page, server_url):
    user_id = page.session.get("user_id")

    TRANSPARENT_PIXEL = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    state = {"mode": "idle", "poller_id": 0}

    camera_stream = ft.Image(
        src=f"data:image/png;base64,{TRANSPARENT_PIXEL}",
        width=340, height=340, fit="cover", border_radius=20, visible=False,
        gapless_playback=True,
    )

    placeholder = ft.Container(
        width=340, height=340, bgcolor=SURFACE_DARK_2, border_radius=20,
        content=ft.Column([
            ft.Icon(ft.Icons.RESTAURANT, size=80, color=TEXT_MUTED),
            ft.Text("Kamerayı açmak için aşağıdaki butona bas",
                    color=TEXT_MUTED, size=12),
        ], alignment="center", horizontal_alignment="center", spacing=12),
        alignment=ft.alignment.center,
    )

    frozen_image = ft.Image(
        src=f"data:image/png;base64,{TRANSPARENT_PIXEL}",
        width=340, height=340, fit="cover", border_radius=20, visible=False,
        gapless_playback=True,
    )

    analyze_overlay = ft.Container(
        width=340, height=340, bgcolor="#CC000000",
        border_radius=20, alignment=ft.alignment.center, visible=False,
        content=ft.Column([
            ft.ProgressRing(color=PRIMARY_LIGHT, width=40, height=40),
            ft.Container(height=10),
            ft.Text("Yapay zeka analiz ediyor...", color="white", weight="bold"),
        ], alignment="center", horizontal_alignment="center"),
    )

    camera_stack = ft.Stack([placeholder, camera_stream, frozen_image, analyze_overlay],
                            width=340, height=340)

    info_text = ft.Text("Hazır! Kamerayı açabilirsin.", color=TEXT_SECONDARY, size=13)
    result_card_container = ft.Container(visible=False)

    action_btn = ft.FilledButton(
        text="Kamerayı Aç",
        icon=ft.Icons.VIDEOCAM,
        on_click=lambda e: handle_action(e),
        style=ft.ButtonStyle(
            bgcolor=PRIMARY, color="white",
            padding=ft.padding.symmetric(horizontal=30, vertical=20),
            shape=ft.RoundedRectangleBorder(radius=14),
            text_style=ft.TextStyle(weight="bold", size=15),
        ),
    )

    def show_idle_error(message):
        state["mode"] = "idle"
        placeholder.visible = True
        camera_stream.visible = False
        frozen_image.visible = False
        analyze_overlay.visible = False
        result_card_container.visible = False
        action_btn.disabled = False
        action_btn.icon = ft.Icons.VIDEOCAM
        action_btn.text = "Kamerayı Aç"
        action_btn.style.bgcolor = PRIMARY
        info_text.value = message
        info_text.color = DANGER
        page.update()

    def render_result_card(resp):
        food_name = resp.get("food_name", "BİLİNMİYOR")
        conf = resp.get("confidence", 0.0)
        cal = resp.get("calories", 0)
        macros = resp.get("macros", {"protein": "0g", "karb": "0g", "yag": "0g"})
        advice = resp.get("advice", "")

        def save_to_log(e):
            try:
                database.add_food_log(
                    user_id=user_id, food_name=food_name, calories=cal,
                    protein_g=macros.get("protein", "0g"),
                    carbs_g=macros.get("karb", "0g"),
                    fat_g=macros.get("yag", "0g"),
                    source="camera",
                )
                show_snack(page, f"'{food_name}' günlüğüne eklendi!", SUCCESS)
                result_card_container.visible = False
                show_idle_error("Yeni tarama için kamerayı aç.")
                info_text.color = TEXT_SECONDARY
            except Exception as ex:
                show_snack(page, f"Kayıt hatası: {ex}", DANGER)

        def discard(e):
            result_card_container.visible = False
            show_idle_error("Tarama iptal edildi.")
            info_text.color = TEXT_SECONDARY

        result_card_container.content = card(
            ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text(food_name, size=20, weight="bold", color=TEXT_PRIMARY),
                        ft.Text(f"Güven: %{conf}", size=12, color=TEXT_MUTED),
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(str(cal), size=24, weight="bold", color=PRIMARY_LIGHT),
                            ft.Text("kcal", size=10, color=TEXT_MUTED),
                        ], horizontal_alignment="center", spacing=0),
                        bgcolor=f"{PRIMARY}22",
                        padding=ft.padding.symmetric(horizontal=14, vertical=8),
                        border_radius=12,
                    ),
                ]),
                ft.Container(height=10),
                ft.Row([
                    macro_chip("Protein", macros.get('protein', '?'), PROTEIN_COLOR),
                    macro_chip("Karb", macros.get('karb', '?'), CARB_COLOR),
                    macro_chip("Yağ", macros.get('yag', '?'), FAT_COLOR),
                ], spacing=8),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.LIGHTBULB, color=INFO, size=18),
                        ft.Text(advice, color=TEXT_SECONDARY, size=12, italic=True, expand=True),
                    ], vertical_alignment="start", spacing=8),
                    bgcolor=f"{INFO}11",
                    padding=12, border_radius=10,
                ),
                ft.Container(height=10),
                ft.Row([
                    outlined_button("İptal", discard, icon=ft.Icons.CLOSE),
                    primary_button("Günlüğe Ekle", save_to_log, icon=ft.Icons.ADD),
                ], alignment="spaceBetween"),
            ], spacing=4),
            width=520,
        )
        result_card_container.visible = True

    def display_result(resp):
        state["mode"] = "result"
        state["poller_id"] += 1
        camera_stream.visible = False
        placeholder.visible = False
        frozen_image.src = f"data:image/jpeg;base64,{resp['image']}"
        frozen_image.visible = True
        analyze_overlay.visible = False
        render_result_card(resp)
        action_btn.disabled = False
        action_btn.icon = ft.Icons.REPLAY
        action_btn.text = "Yeni Tarama"
        action_btn.style.bgcolor = PRIMARY
        info_text.value = "Sonuç hazır. Günlüğüne eklemek için 'Günlüğe Ekle' butonuna bas."
        info_text.color = TEXT_SECONDARY
        page.update()

    def start_frame_poller():
        state["poller_id"] += 1
        poller_id = state["poller_id"]

        def poll():
            missed = 0
            while state["mode"] == "streaming" and state["poller_id"] == poller_id:
                if page.route != "/scan":
                    try:
                        requests.get(f"{server_url}/stop", timeout=1)
                    except Exception:
                        pass
                    return
                try:
                    resp = requests.get(f"{server_url}/frame", timeout=1)
                    data = resp.json()
                    if data.get("status") == "ok":
                        missed = 0
                        camera_stream.src = f"data:image/jpeg;base64,{data['image']}"
                        page.update()
                    else:
                        missed += 1
                        if missed >= 30:
                            try:
                                requests.get(f"{server_url}/stop", timeout=1)
                            except Exception:
                                pass
                            show_idle_error(data.get("message", "Kamera hazır değil."))
                            break
                except Exception:
                    missed += 1
                    if missed >= 30:
                        try:
                            requests.get(f"{server_url}/stop", timeout=1)
                        except Exception:
                            pass
                        show_idle_error("Kameradan görüntü alınamadı.")
                        break
                time.sleep(0.08)

        threading.Thread(target=poll, daemon=True).start()

    def handle_action(e):
        if state["mode"] == "idle":
            try:
                requests.get(f"{server_url}/start", timeout=2)
                state["mode"] = "streaming"
                placeholder.visible = False
                camera_stream.visible = True
                camera_stream.src = f"data:image/png;base64,{TRANSPARENT_PIXEL}"
                frozen_image.visible = False
                analyze_overlay.visible = False
                result_card_container.visible = False
                action_btn.icon = ft.Icons.CAMERA
                action_btn.text = "Fotoğraf Çek"
                action_btn.style.bgcolor = DANGER
                info_text.value = "Yemeği çerçeveye al ve fotoğraf çek."
                info_text.color = TEXT_SECONDARY
                page.update()
                start_frame_poller()
            except Exception as ex:
                show_idle_error(f"Kamera başlatılamadı: {ex}")

        elif state["mode"] == "streaming":
            state["mode"] = "analyzing"
            action_btn.disabled = True
            analyze_overlay.visible = True
            page.update()

            def process():
                try:
                    resp = requests.get(f"{server_url}/capture", timeout=20).json()
                    requests.get(f"{server_url}/stop", timeout=2)
                    camera_stream.visible = False
                    if resp.get("status") == "ok":
                        display_result(resp)
                    else:
                        show_idle_error(resp.get("message", "Yakalanamadı."))
                except Exception as ex:
                    try:
                        requests.get(f"{server_url}/stop", timeout=2)
                    except Exception:
                        pass
                    show_idle_error(f"Hata: {ex}")

            threading.Thread(target=process, daemon=True).start()

        elif state["mode"] == "result":
            state["mode"] = "idle"
            state["poller_id"] += 1
            frozen_image.visible = False
            camera_stream.visible = False
            analyze_overlay.visible = False
            placeholder.visible = True
            result_card_container.visible = False
            action_btn.icon = ft.Icons.VIDEOCAM
            action_btn.text = "Kamerayı Aç"
            action_btn.style.bgcolor = PRIMARY
            info_text.value = "Kamerayı açmak için butona bas."
            info_text.color = TEXT_SECONDARY
            page.update()

    camera_frame = ft.Container(
        content=camera_stack,
        border_radius=20,
        border=ft.border.all(2, PRIMARY_DARK),
    )

    body = [
        ft.Container(
            alignment=ft.alignment.top_center,
            content=ft.Column([
                camera_frame,
                ft.Container(height=14),
                info_text,
                ft.Container(height=14),
                action_btn,
                ft.Container(height=20),
                result_card_container,
                ft.Container(height=40),
            ], horizontal_alignment="center"),
        )
    ]

    return shell(page, "/scan", "Yemek Tara",
                 "Yemeği kameraya tut, kalori ve makro değerleri otomatik gelir",
                 body)


def build_food_log_view(page):
    user_id = page.session.get("user_id")

    food_name = text_field("Yemek adı", width=320, prefix_icon=ft.Icons.RESTAURANT)
    calories_input = text_field("Kalori (kcal)", width=320,
                                 prefix_icon=ft.Icons.LOCAL_FIRE_DEPARTMENT,
                                 keyboard_type=ft.KeyboardType.NUMBER)
    protein_input = text_field("Protein (g)", width=320, prefix_icon=ft.Icons.SCIENCE,
                                keyboard_type=ft.KeyboardType.NUMBER)
    carbs_input = text_field("Karbonhidrat (g)", width=320, prefix_icon=ft.Icons.GRAIN,
                              keyboard_type=ft.KeyboardType.NUMBER)
    fat_input = text_field("Yağ (g)", width=320, prefix_icon=ft.Icons.OPACITY,
                            keyboard_type=ft.KeyboardType.NUMBER)

    def close_dialog(e=None):
        dialog.open = False
        page.update()

    def save_manual(e):
        if not food_name.value or not calories_input.value:
            show_snack(page, "Yemek adı ve kalori zorunlu", DANGER)
            return
        try:
            database.add_food_log(
                user_id=user_id,
                food_name=food_name.value.strip(),
                calories=calories_input.value,
                protein_g=protein_input.value or 0,
                carbs_g=carbs_input.value or 0,
                fat_g=fat_input.value or 0,
                source="manual",
            )
            show_snack(page, "Eklendi!", SUCCESS)
            for f in [food_name, calories_input, protein_input, carbs_input, fat_input]:
                f.value = ""
            close_dialog()
            refresh_view(page, "/food")
        except Exception as ex:
            show_snack(page, f"Hata: {ex}", DANGER)

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=SURFACE_DARK,
        title=ft.Text("Yemek Ekle", color=TEXT_PRIMARY, weight="bold"),
        content=ft.Container(
            width=360,
            content=ft.Column([
                food_name, calories_input, protein_input, carbs_input, fat_input,
            ], spacing=10, tight=True),
        ),
        actions=[
            ft.TextButton("İptal", on_click=close_dialog,
                          style=ft.ButtonStyle(color=TEXT_SECONDARY)),
            ft.FilledButton("Ekle", on_click=save_manual,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color="white")),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_add_dialog(e):
        page.dialog = dialog
        dialog.open = True
        page.update()

    def delete_entry(log_id):
        def handler(e):
            database.delete_food_log(log_id, user_id)
            show_snack(page, "Silindi", WARNING)
            refresh_view(page, "/food")
        return handler

    logs_today = database.get_food_logs(user_id, days=1)
    logs_week = database.get_food_logs(user_id, days=7)
    today_total = sum(l["calories"] for l in logs_today)

    def render_log_row(log):
        is_camera = log["source"] == "camera"
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CAMERA_ALT if is_camera else ft.Icons.EDIT_NOTE,
                    color=PRIMARY_LIGHT if is_camera else WARNING,
                    size=22,
                ),
                ft.Column([
                    ft.Text(log["food_name"], size=14, weight="bold", color=TEXT_PRIMARY),
                    ft.Text(
                        f"{log['logged_at'][:16].replace('T', ' ')} • "
                        f"P:{log['protein_g']:.0f}g K:{log['carbs_g']:.0f}g Y:{log['fat_g']:.0f}g",
                        size=11, color=TEXT_MUTED,
                    ),
                ], spacing=2, expand=True),
                ft.Text(f"{log['calories']} kcal", size=14, weight="bold", color=PRIMARY_LIGHT),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE, icon_color=DANGER, icon_size=18,
                    on_click=delete_entry(log["id"]),
                ),
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            bgcolor=SURFACE_DARK_2, border_radius=10,
            margin=ft.margin.only(bottom=8),
        )

    today_rows = [render_log_row(l) for l in logs_today]
    if not today_rows:
        today_rows = [ft.Container(
            content=ft.Text("Bugün henüz yemek eklenmedi", color=TEXT_MUTED, size=13),
            padding=20, alignment=ft.alignment.center,
        )]

    earlier = [l for l in logs_week if l not in logs_today]
    earlier_rows = [render_log_row(l) for l in earlier]

    body = [
        card(
            ft.Row([
                ft.Icon(ft.Icons.RESTAURANT, color=PRIMARY_LIGHT, size=32),
                ft.Column([
                    ft.Text("Bugün toplam", size=12, color=TEXT_SECONDARY),
                    ft.Text(f"{today_total} kcal", size=24, weight="bold", color=PRIMARY_LIGHT),
                ], spacing=0, expand=True),
                outlined_button("Tara", lambda e: page.go("/scan"), icon=ft.Icons.CAMERA_ALT),
            ], spacing=14),
        ),
        ft.Container(height=20),
        ft.Text("Bugün", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(height=8),
        ft.Column(today_rows, spacing=0),
        ft.Container(height=20),
        ft.Text("Önceki günler (7 gün)", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(height=8),
        ft.Column(earlier_rows if earlier_rows else [
            ft.Container(
                content=ft.Text("Önceki kayıt yok", color=TEXT_MUTED, size=13),
                padding=20, alignment=ft.alignment.center,
            )
        ], spacing=0),
        ft.Container(height=80),
    ]

    fab = ft.FloatingActionButton(
        icon=ft.Icons.ADD, bgcolor=PRIMARY,
        on_click=open_add_dialog, tooltip="Manuel yemek ekle",
    )

    return shell(page, "/food", "Yemek Günlüğüm",
                 "Yediklerini kaydet ve takip et", body, fab=fab)


CATEGORY_ICONS = {
    "Kardiyo":             "DIRECTIONS_RUN",
    "Göğüs":               "FITNESS_CENTER",
    "Sırt":                "FITNESS_CENTER",
    "Omuz":                "FITNESS_CENTER",
    "Bacak & Kalça":       "FITNESS_CENTER",
    "Kol":                 "FITNESS_CENTER",
    "Karın & Core":        "SELF_IMPROVEMENT",
    "Fonksiyonel / HIIT":  "BOLT",
    "Yoga / Pilates":      "SELF_IMPROVEMENT",
    "Esneklik":            "ACCESSIBILITY_NEW",
    "Takım Sporları":      "SPORTS_SOCCER",
    "Raket Sporları":      "SPORTS_TENNIS",
    "Dövüş Sporları":      "SPORTS_MMA",
    "Dans":                "MUSIC_NOTE",
    "Su Sporları":         "POOL",
    "Doğa / Outdoor":      "HIKING",
}

STRENGTH_CATEGORIES = {"Göğüs", "Sırt", "Omuz", "Bacak & Kalça", "Kol", "Karın & Core"}

SECONDS_PER_SET = 90


def build_exercise_view(page):
    user_id = page.session.get("user_id")
    user = database.get_user_by_id(user_id)
    user_weight = user.get("weight_kg") or 70.0

    selected = {"exercise": None, "mode": "duration"}

    sets_field = text_field("Set sayısı", value="3", width=150,
                            prefix_icon=ft.Icons.FORMAT_LIST_NUMBERED,
                            keyboard_type=ft.KeyboardType.NUMBER)
    reps_field = text_field("Tekrar (rep)", value="10", width=150,
                            prefix_icon=ft.Icons.REPEAT,
                            keyboard_type=ft.KeyboardType.NUMBER)
    duration_input = text_field("Süre (dakika)", value="30", width=320,
                                prefix_icon=ft.Icons.TIMER,
                                keyboard_type=ft.KeyboardType.NUMBER)

    estimate_text = ft.Text("", size=14, color=PRIMARY_LIGHT, weight="bold")
    info_hint = ft.Text("", size=11, color=TEXT_MUTED, italic=True)

    sets_reps_row = ft.Row([sets_field, reps_field], spacing=10, visible=False)

    def update_estimate(e=None):
        ex = selected["exercise"]
        if not ex:
            estimate_text.value = ""
            return
        try:
            if selected["mode"] == "sets":
                try:
                    s = int(sets_field.value or 0)
                except ValueError:
                    s = 0
                if s > 0:
                    auto_dur = max(1, round(s * SECONDS_PER_SET / 60))
                    duration_input.value = str(auto_dur)
            dur = int(duration_input.value or 0)
            if dur <= 0:
                estimate_text.value = ""
                page.update()
                return
            cal = exercises_data.calculate_calories(ex["met"], user_weight, dur)
            estimate_text.value = f"≈ {cal} kcal yakılacak"
        except ValueError:
            estimate_text.value = ""
        page.update()

    duration_input.on_change = update_estimate
    sets_field.on_change = update_estimate
    reps_field.on_change = update_estimate

    def close_dialog(e=None):
        dialog.open = False
        page.update()

    def save_exercise(e):
        ex = selected["exercise"]
        if not ex:
            return
        try:
            dur = int(duration_input.value or 0)
            if dur <= 0:
                show_snack(page, "Süre pozitif olmalı", DANGER)
                return
        except ValueError:
            show_snack(page, "Süre sayısal olmalı", DANGER)
            return

        sets_val, reps_val = 0, 0
        if selected["mode"] == "sets":
            try:
                sets_val = int(sets_field.value or 0)
                reps_val = int(reps_field.value or 0)
                if sets_val <= 0 or reps_val <= 0:
                    show_snack(page, "Set ve tekrar pozitif olmalı", DANGER)
                    return
            except ValueError:
                show_snack(page, "Set ve tekrar sayısal olmalı", DANGER)
                return

        cal = exercises_data.calculate_calories(ex["met"], user_weight, dur)
        database.add_exercise_log(
            user_id=user_id, exercise_name=ex["name"],
            duration_min=dur, calories_burned=cal, met_value=ex["met"],
            sets=sets_val, reps=reps_val,
        )
        msg = f"{ex['name']} • {cal} kcal"
        if sets_val and reps_val:
            msg += f" ({sets_val}×{reps_val})"
        show_snack(page, f"{msg} eklendi!", SUCCESS)
        close_dialog()
        refresh_view(page, "/exercise")

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=SURFACE_DARK,
        title=ft.Text("Egzersiz Ekle", color=TEXT_PRIMARY, weight="bold"),
        content=ft.Container(
            width=360,
            content=ft.Column([
                ft.Text("", color=PRIMARY_LIGHT, size=16, weight="bold"),
                ft.Text("", color=TEXT_MUTED, size=12),
                ft.Container(height=10),
                sets_reps_row,
                info_hint,
                duration_input,
                estimate_text,
            ], spacing=8, tight=True),
        ),
        actions=[
            ft.TextButton("İptal", on_click=close_dialog,
                          style=ft.ButtonStyle(color=TEXT_SECONDARY)),
            ft.FilledButton("Ekle", on_click=save_exercise,
                            style=ft.ButtonStyle(bgcolor=PRIMARY, color="white")),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_exercise_dialog(ex):
        def handler(e):
            selected["exercise"] = ex
            is_strength = ex["category"] in STRENGTH_CATEGORIES
            selected["mode"] = "sets" if is_strength else "duration"

            dialog.content.content.controls[0].value = ex["name"]
            dialog.content.content.controls[1].value = f"Kategori: {ex['category']} • MET: {ex['met']}"

            if is_strength:
                sets_reps_row.visible = True
                sets_field.value = "3"
                reps_field.value = "10"
                duration_input.label = "Toplam süre (dk, otomatik)"
                duration_input.value = str(max(1, round(3 * SECONDS_PER_SET / 60)))
                info_hint.value = "Set sayısı değişince süre otomatik güncellenir, manuel düzenleyebilirsin."
                info_hint.visible = True
            else:
                sets_reps_row.visible = False
                duration_input.label = "Süre (dakika)"
                duration_input.value = "30"
                info_hint.value = ""
                info_hint.visible = False
            update_estimate()
            page.dialog = dialog
            dialog.open = True
            page.update()
        return handler

    def make_exercise_row(ex):
        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    getattr(ft.Icons, ex["icon"].upper(), ft.Icons.FITNESS_CENTER),
                    color=PRIMARY_LIGHT, size=18,
                ),
                ft.Column([
                    ft.Text(ex["name"], size=13, weight="w500", color=TEXT_PRIMARY),
                    ft.Text(
                        f"MET: {ex['met']} • "
                        f"{exercises_data.calculate_calories(ex['met'], user_weight, 30)} kcal/30dk",
                        size=10, color=TEXT_MUTED,
                    ),
                ], spacing=0, expand=True),
                ft.Icon(ft.Icons.ADD_CIRCLE, color=PRIMARY_LIGHT, size=22),
            ], spacing=10),
            bgcolor=SURFACE_DARK_2, border_radius=10,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            on_click=open_exercise_dialog(ex), ink=True,
            margin=ft.margin.only(left=12, right=12, bottom=6),
        )

    category_sections = []
    for cat in exercises_data.get_categories():
        exs = exercises_data.get_by_category(cat)
        cat_icon_name = CATEGORY_ICONS.get(cat, "FITNESS_CENTER")

        category_sections.append(
            ft.Container(
                content=ft.ExpansionTile(
                    title=ft.Text(cat, size=14, weight="bold", color=TEXT_PRIMARY),
                    subtitle=ft.Text(f"{len(exs)} hareket", size=11, color=TEXT_MUTED),
                    leading=ft.Container(
                        content=ft.Icon(
                            getattr(ft.Icons, cat_icon_name, ft.Icons.FITNESS_CENTER),
                            color=PRIMARY_LIGHT, size=22,
                        ),
                        bgcolor=f"{PRIMARY}22",
                        padding=10, border_radius=10,
                    ),
                    bgcolor=SURFACE_DARK,
                    collapsed_bgcolor=SURFACE_DARK,
                    text_color=TEXT_PRIMARY,
                    collapsed_text_color=TEXT_PRIMARY,
                    icon_color=PRIMARY_LIGHT,
                    collapsed_icon_color=TEXT_SECONDARY,
                    initially_expanded=False,
                    maintain_state=True,
                    controls=[
                        ft.Container(height=4),
                        *(make_exercise_row(ex) for ex in exs),
                        ft.Container(height=6),
                    ],
                ),
                bgcolor=SURFACE_DARK,
                border_radius=12,
                border=ft.border.all(1, BORDER_DARK),
                margin=ft.margin.only(bottom=10),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )
        )

    recent = database.get_exercise_logs(user_id, days=1)

    def render_ex_row(log):
        sets = log.get("sets") or 0
        reps = log.get("reps") or 0
        detail_parts = []
        if sets and reps:
            detail_parts.append(f"{sets} set × {reps} tekrar")
        detail_parts.append(f"{log['duration_min']} dk")
        detail_parts.append(log['logged_at'][11:16])
        detail = " • ".join(detail_parts)

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FITNESS_CENTER, color=SUCCESS, size=20),
                ft.Column([
                    ft.Text(log["exercise_name"], size=13, weight="bold", color=TEXT_PRIMARY),
                    ft.Text(detail, size=11, color=TEXT_MUTED),
                ], spacing=2, expand=True),
                ft.Text(f"-{log['calories_burned']} kcal", color=SUCCESS, weight="bold", size=14),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE, icon_color=DANGER, icon_size=18,
                    on_click=lambda e, lid=log["id"]: (
                        database.delete_exercise_log(lid, user_id),
                        show_snack(page, "Silindi", WARNING),
                        refresh_view(page, "/exercise"),
                    ),
                ),
            ], spacing=10),
            bgcolor=SURFACE_DARK_2, border_radius=10,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            margin=ft.margin.only(bottom=6),
        )

    today_total_ex = sum(l["calories_burned"] for l in recent)

    body = [
        card(
            ft.Row([
                ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=SUCCESS, size=32),
                ft.Column([
                    ft.Text("Bugün yakılan", size=12, color=TEXT_SECONDARY),
                    ft.Text(f"{today_total_ex} kcal", size=24, weight="bold", color=SUCCESS),
                ], spacing=0, expand=True),
                ft.Container(
                    content=ft.Text(f"Kilon: {user_weight:.0f} kg",
                                    size=11, color=TEXT_MUTED),
                    bgcolor=SURFACE_DARK_2,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=8,
                ),
            ], spacing=14),
        ),
        ft.Container(height=20),
        ft.Text("Bugünün egzersizleri", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(height=8),
        *(
            [render_ex_row(l) for l in recent] if recent
            else [ft.Container(
                content=ft.Text("Bugün henüz egzersiz eklenmedi",
                                color=TEXT_MUTED, size=13),
                padding=16, alignment=ft.alignment.center,
            )]
        ),
        ft.Container(height=20),
        ft.Text("Yeni egzersiz ekle", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Text("Bir kategoriyi aç, hareketi seç ve süreyi gir — kalori otomatik hesaplanır",
                size=12, color=TEXT_MUTED),
        ft.Container(height=12),
        *category_sections,
        ft.Container(height=40),
    ]

    return shell(page, "/exercise", "Egzersizler",
                 "Egzersizini seç, kalori yakımını otomatik hesaplayalım", body)


def build_stats_view(page):
    user_id = page.session.get("user_id")
    period = page.session.get("stats_period") or "7g"
    today = datetime.now().date()

    custom_start = page.session.get("stats_custom_start") or (today - timedelta(days=6)).isoformat()
    custom_end = page.session.get("stats_custom_end") or today.isoformat()

    daily = None
    hourly = None
    totals = {"cal_in": 0, "cal_out": 0, "net": 0}
    period_label = ""

    if period == "bugun":
        totals = database.get_totals_today(user_id)
        hourly = database.get_hourly_summary_today(user_id)
        period_label = "Bugün"
    elif period == "24s":
        totals = database.get_totals_last_24h(user_id)
        hourly = database.get_hourly_summary_last_24h(user_id)
        period_label = "Son 24 saat"
    elif period == "7g":
        totals = database.get_totals(user_id, days=7)
        daily = database.get_daily_summary(user_id, days=7)
        period_label = "Son 7 gün"
    elif period == "30g":
        totals = database.get_totals(user_id, days=30)
        daily = database.get_daily_summary(user_id, days=30)
        period_label = "Son 30 gün"
    elif period == "ozel":
        totals = database.get_totals_range(user_id, custom_start, custom_end)
        daily = database.get_daily_summary_range(user_id, custom_start, custom_end)
        period_label = f"{custom_start} → {custom_end}"

    def on_start_change(e):
        if e.control.value:
            page.session.set("stats_custom_start", e.control.value.date().isoformat())
            page.session.set("stats_period", "ozel")
            refresh_view(page, "/stats")

    def on_end_change(e):
        if e.control.value:
            page.session.set("stats_custom_end", e.control.value.date().isoformat())
            page.session.set("stats_period", "ozel")
            refresh_view(page, "/stats")

    start_picker = ft.DatePicker(
        first_date=datetime(2024, 1, 1),
        last_date=datetime.now(),
        on_change=on_start_change,
    )
    end_picker = ft.DatePicker(
        first_date=datetime(2024, 1, 1),
        last_date=datetime.now(),
        on_change=on_end_change,
    )

    # Picker'ları view inşası sırasında overlay'a eklemiyoruz; aksi halde
    # eski view'ın mount durumuyla çakışıp Flet stale ID hatası atıyor
    def _ensure_in_overlay(ctrl):
        if ctrl not in page.overlay:
            page.overlay.append(ctrl)

    def open_start(e):
        _ensure_in_overlay(start_picker)
        try:
            page.open(start_picker)
        except Exception:
            start_picker.open = True
            page.update()

    def open_end(e):
        _ensure_in_overlay(end_picker)
        try:
            page.open(end_picker)
        except Exception:
            end_picker.open = True
            page.update()

    def build_bar_chart(daily):
        max_val = max(
            [d["cal_in"] for d in daily] + [d["cal_out"] for d in daily] + [100]
        )
        max_y = ((max_val // 200) + 1) * 200
        groups = []
        for i, d in enumerate(daily):
            groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0, to_y=d["cal_in"],
                            width=12, color=WARNING,
                            border_radius=ft.border_radius.only(top_left=4, top_right=4),
                            tooltip=f"Alınan: {d['cal_in']} kcal",
                        ),
                        ft.BarChartRod(
                            from_y=0, to_y=d["cal_out"],
                            width=12, color=SUCCESS,
                            border_radius=ft.border_radius.only(top_left=4, top_right=4),
                            tooltip=f"Yakılan: {d['cal_out']} kcal",
                        ),
                    ],
                )
            )
        x_labels = []
        for i, d in enumerate(daily):
            try:
                dt = datetime.fromisoformat(d["date"])
                label = dt.strftime("%d/%m")
            except Exception:
                label = d["date"][-5:]
            x_labels.append(ft.ChartAxisLabel(value=i, label=ft.Text(label, size=10, color=TEXT_MUTED)))

        return ft.BarChart(
            bar_groups=groups,
            border=ft.border.all(0, "transparent"),
            left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("kcal", size=11, color=TEXT_MUTED)),
            bottom_axis=ft.ChartAxis(labels=x_labels, labels_size=30),
            horizontal_grid_lines=ft.ChartGridLines(color=BORDER_DARK, width=0.5, dash_pattern=[3, 3]),
            tooltip_bgcolor=SURFACE_DARK_2,
            max_y=max_y, min_y=0,
            interactive=True, expand=True, height=280,
        )

    def build_line_chart(daily):
        max_abs = max([abs(d["net"]) for d in daily] + [100])
        max_y = ((max_abs // 200) + 1) * 200
        points = [ft.LineChartDataPoint(x=i, y=d["net"]) for i, d in enumerate(daily)]
        x_labels = []
        for i, d in enumerate(daily):
            try:
                dt = datetime.fromisoformat(d["date"])
                label = dt.strftime("%d/%m")
            except Exception:
                label = d["date"][-5:]
            x_labels.append(ft.ChartAxisLabel(value=i, label=ft.Text(label, size=10, color=TEXT_MUTED)))

        series = ft.LineChartData(
            data_points=points,
            color=PRIMARY_LIGHT, stroke_width=3, curved=True,
            stroke_cap_round=True,
            below_line_bgcolor=f"{PRIMARY}33",
            below_line_cutoff_y=0,
            point=True,
        )
        return ft.LineChart(
            data_series=[series],
            border=ft.border.all(0, "transparent"),
            horizontal_grid_lines=ft.ChartGridLines(color=BORDER_DARK, width=0.5, dash_pattern=[3, 3]),
            left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("net kcal", size=11, color=TEXT_MUTED)),
            bottom_axis=ft.ChartAxis(labels=x_labels, labels_size=30),
            min_y=-max_y, max_y=max_y,
            min_x=0, max_x=len(daily) - 1,
            tooltip_bgcolor=SURFACE_DARK_2,
            interactive=True, expand=True, height=240,
        )

    def build_hourly_chart(hourly):
        max_val = max(
            [h["cal_in"] for h in hourly] + [h["cal_out"] for h in hourly] + [100]
        )
        max_y = ((max_val // 100) + 1) * 100
        groups = []
        for i, h in enumerate(hourly):
            groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0, to_y=h["cal_in"],
                            width=6, color=WARNING,
                            border_radius=ft.border_radius.only(top_left=2, top_right=2),
                            tooltip=f"{h['hour']:02d}:00 • Alınan: {h['cal_in']} kcal",
                        ),
                        ft.BarChartRod(
                            from_y=0, to_y=h["cal_out"],
                            width=6, color=SUCCESS,
                            border_radius=ft.border_radius.only(top_left=2, top_right=2),
                            tooltip=f"{h['hour']:02d}:00 • Yakılan: {h['cal_out']} kcal",
                        ),
                    ],
                )
            )
        x_labels = [
            ft.ChartAxisLabel(
                value=i,
                label=ft.Text(f"{hourly[i]['hour']:02d}", size=9, color=TEXT_MUTED),
            )
            for i in range(0, len(hourly), 3)
        ]
        return ft.BarChart(
            bar_groups=groups,
            border=ft.border.all(0, "transparent"),
            left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("kcal", size=11, color=TEXT_MUTED)),
            bottom_axis=ft.ChartAxis(labels=x_labels, labels_size=30,
                                     title=ft.Text("Saat", size=11, color=TEXT_MUTED)),
            horizontal_grid_lines=ft.ChartGridLines(color=BORDER_DARK, width=0.5, dash_pattern=[3, 3]),
            tooltip_bgcolor=SURFACE_DARK_2,
            max_y=max_y, min_y=0,
            interactive=True, expand=True, height=240,
        )

    def set_period(p):
        def handler(e):
            page.session.set("stats_period", p)
            refresh_view(page, "/stats")
        return handler

    def period_btn(label, key):
        is_active = period == key
        return ft.FilledButton(
            label, on_click=set_period(key),
            style=ft.ButtonStyle(
                bgcolor=PRIMARY if is_active else SURFACE_DARK_2,
                color="white" if is_active else TEXT_SECONDARY,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(horizontal=18, vertical=14),
                text_style=ft.TextStyle(weight="bold", size=13),
            ),
        )

    period_buttons = ft.Row([
        period_btn("Bugün", "bugun"),
        period_btn("Son 24 saat", "24s"),
        period_btn("7 Gün", "7g"),
        period_btn("30 Gün", "30g"),
        period_btn("Özel aralık", "ozel"),
    ], spacing=8, wrap=True)

    def date_field(label, value, on_click):
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CALENDAR_TODAY, color=PRIMARY_LIGHT, size=18),
                ft.Column([
                    ft.Text(label, size=10, color=TEXT_MUTED),
                    ft.Text(value, size=13, weight="bold", color=TEXT_PRIMARY),
                ], spacing=0),
            ], spacing=10),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            bgcolor=SURFACE_DARK_2,
            border=ft.border.all(1, BORDER_DARK),
            border_radius=10,
            on_click=on_click,
            ink=True,
        )

    custom_range_row = ft.Container(
        content=ft.Row([
            date_field("Başlangıç", custom_start, open_start),
            ft.Icon(ft.Icons.ARROW_FORWARD, color=TEXT_MUTED, size=18),
            date_field("Bitiş", custom_end, open_end),
        ], spacing=10, vertical_alignment="center"),
        margin=ft.margin.only(top=10),
        visible=(period == "ozel"),
    )

    chart_section = []
    if period in ("bugun", "24s") and hourly is not None:
        title = "Bugünün saat-saat dağılımı" if period == "bugun" else "Son 24 saatin saat-saat dağılımı"
        chart_section = [
            ft.Text(title, size=14, weight="bold", color=TEXT_PRIMARY),
            ft.Container(height=4),
            ft.Row([
                ft.Container(width=12, height=12, bgcolor=WARNING, border_radius=2),
                ft.Text("Alınan", size=11, color=TEXT_SECONDARY),
                ft.Container(width=14),
                ft.Container(width=12, height=12, bgcolor=SUCCESS, border_radius=2),
                ft.Text("Yakılan", size=11, color=TEXT_SECONDARY),
            ], spacing=6),
            ft.Container(height=10),
            card(build_hourly_chart(hourly), padding=14),
            ft.Container(height=20),
        ]
    elif daily is not None and len(daily) > 0:
        chart_section = [
            ft.Text("Günlük kalori alımı / yakımı", size=14, weight="bold", color=TEXT_PRIMARY),
            ft.Container(height=4),
            ft.Row([
                ft.Container(width=12, height=12, bgcolor=WARNING, border_radius=2),
                ft.Text("Alınan", size=11, color=TEXT_SECONDARY),
                ft.Container(width=14),
                ft.Container(width=12, height=12, bgcolor=SUCCESS, border_radius=2),
                ft.Text("Yakılan", size=11, color=TEXT_SECONDARY),
            ], spacing=6),
            ft.Container(height=10),
            card(build_bar_chart(daily), padding=14),
            ft.Container(height=20),
            ft.Text("Net kalori trendi", size=14, weight="bold", color=TEXT_PRIMARY),
            ft.Text(
                "Pozitif: alınan > yakılan (kilo alımı)  •  Negatif: yakılan > alınan (kilo verme)",
                size=11, color=TEXT_MUTED,
            ),
            ft.Container(height=10),
            card(build_line_chart(daily), padding=14),
            ft.Container(height=20),
        ]

    body = [
        period_buttons,
        custom_range_row,
        ft.Container(height=16),
        ft.ResponsiveRow([
            ft.Container(stat_card(ft.Icons.RESTAURANT, "Toplam alınan",
                                   totals["cal_in"], "kcal", WARNING),
                         col={"xs": 12, "sm": 4}),
            ft.Container(stat_card(ft.Icons.LOCAL_FIRE_DEPARTMENT, "Toplam yakılan",
                                   totals["cal_out"], "kcal", SUCCESS),
                         col={"xs": 12, "sm": 4}),
            ft.Container(stat_card(ft.Icons.TRENDING_FLAT, "Net kalori",
                                   totals["net"], "kcal",
                                   DANGER if totals["net"] > 0 else SUCCESS),
                         col={"xs": 12, "sm": 4}),
        ], spacing=12, run_spacing=12),
        ft.Container(height=20),
        *chart_section,
        ft.Container(height=40),
    ]

    return shell(page, "/stats", "İstatistikler",
                 f"{period_label} özeti ve grafikleri", body)


def build_profile_view(page):
    user_id = page.session.get("user_id")
    user = database.get_user_by_id(user_id)

    name = text_field("Ad Soyad", value=user.get("name", ""),
                      prefix_icon=ft.Icons.PERSON, width=340)
    weight = text_field("Kilo (kg)", value=str(user.get("weight_kg", "")),
                        prefix_icon=ft.Icons.MONITOR_WEIGHT, width=160,
                        keyboard_type=ft.KeyboardType.NUMBER)
    height = text_field("Boy (cm)", value=str(user.get("height_cm", "")),
                        prefix_icon=ft.Icons.HEIGHT, width=160,
                        keyboard_type=ft.KeyboardType.NUMBER)
    age = text_field("Yaş", value=str(user.get("age", "")),
                     prefix_icon=ft.Icons.CAKE, width=160,
                     keyboard_type=ft.KeyboardType.NUMBER)

    gender = ft.Dropdown(
        label="Cinsiyet", value=user.get("gender", ""), width=160,
        border_color=BORDER_DARK, focused_border_color=PRIMARY,
        bgcolor=SURFACE_DARK_2, border_radius=12,
        content_padding=ft.padding.all(16),
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        text_style=ft.TextStyle(color=TEXT_PRIMARY),
        options=[
            ft.dropdown.Option("Erkek"),
            ft.dropdown.Option("Kadın"),
            ft.dropdown.Option("Diğer"),
        ],
    )

    def save(e):
        try:
            database.update_user_profile(
                user_id,
                name=name.value.strip() if name.value else None,
                weight_kg=float(weight.value) if weight.value else None,
                height_cm=float(height.value) if height.value else None,
                age=int(age.value) if age.value else None,
                gender=gender.value if gender.value else None,
            )
            page.session.set("user_name", name.value.strip())
            show_snack(page, "Profil güncellendi!", SUCCESS)
            refresh_view(page, "/profile")
        except ValueError:
            show_snack(page, "Sayısal alanları kontrol et", DANGER)
        except Exception as ex:
            show_snack(page, f"Hata: {ex}", DANGER)

    bmi_text, bmi_color = "", TEXT_SECONDARY
    try:
        w = float(user.get("weight_kg") or 0)
        h = float(user.get("height_cm") or 0)
        if w > 0 and h > 0:
            bmi = w / ((h / 100) ** 2)
            bmi_text = f"BMI: {bmi:.1f}"
            if bmi < 18.5:
                bmi_text += " (Zayıf)"; bmi_color = INFO
            elif bmi < 25:
                bmi_text += " (Normal)"; bmi_color = SUCCESS
            elif bmi < 30:
                bmi_text += " (Fazla kilolu)"; bmi_color = WARNING
            else:
                bmi_text += " (Obez)"; bmi_color = DANGER
    except Exception:
        pass

    totals_all = database.get_totals(user_id, days=None)

    body = [
        card(
            ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.PERSON, color=PRIMARY_LIGHT, size=40),
                    bgcolor=f"{PRIMARY}22",
                    width=80, height=80, border_radius=40,
                    alignment=ft.alignment.center,
                ),
                ft.Column([
                    ft.Text(user["name"], size=20, weight="bold", color=TEXT_PRIMARY),
                    ft.Text(user["email"], size=12, color=TEXT_SECONDARY),
                    ft.Text(bmi_text, size=12, color=bmi_color, weight="bold"),
                ], spacing=2, expand=True),
            ], spacing=16),
        ),
        ft.Container(height=20),
        ft.Text("Genel toplam", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(height=8),
        ft.ResponsiveRow([
            ft.Container(stat_card(ft.Icons.RESTAURANT, "Toplam alınan",
                                   totals_all["cal_in"], "kcal", WARNING),
                         col={"xs": 12, "sm": 4}),
            ft.Container(stat_card(ft.Icons.LOCAL_FIRE_DEPARTMENT, "Toplam yakılan",
                                   totals_all["cal_out"], "kcal", SUCCESS),
                         col={"xs": 12, "sm": 4}),
            ft.Container(stat_card(ft.Icons.TRENDING_FLAT, "Net kalori",
                                   totals_all["net"], "kcal",
                                   DANGER if totals_all["net"] > 0 else SUCCESS),
                         col={"xs": 12, "sm": 4}),
        ], spacing=12, run_spacing=12),
        ft.Container(height=20),
        ft.Text("Bilgilerini düzenle", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(height=8),
        card(
            ft.Column([
                name,
                ft.Row([weight, height], spacing=10),
                ft.Row([age, gender], spacing=10),
                ft.Container(height=10),
                primary_button("Kaydet", save, icon=ft.Icons.SAVE, width=200),
            ], spacing=12),
        ),
        ft.Container(height=40),
    ]

    return shell(page, "/profile", "Profil",
                 "Bilgilerini görüntüle ve düzenle", body)
