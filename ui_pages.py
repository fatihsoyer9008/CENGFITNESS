import base64
import os
import threading
from datetime import datetime, timedelta

import flet as ft
import requests

import database
import auth
import exercises_data
import foods_data


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
                ft.Text(label, color=TEXT_SECONDARY, size=13, weight="w500"),
            ], spacing=10),
            ft.Container(height=10),
            ft.Row([
                ft.Text(str(value), size=28, weight="bold", color=TEXT_PRIMARY),
                ft.Text(unit, size=13, color=TEXT_MUTED, weight="w500"),
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
            ft.Text(label, size=11, color=color, weight="w500"),
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
    ("/muscle",   "BOLT",            "Kas Gelişimi"),
    ("/stats",    "INSIGHTS",        "Kalori Takibi"),
    ("/profile",  "PERSON",          "Profil"),
]

MOBILE_BREAKPOINT = 760


def is_mobile(page):
    w = getattr(page, "width", None) or 1200
    return w < MOBILE_BREAKPOINT


def _nav_content(page, current_route, on_select=None):
    user_name = page.session.get("user_name") or "Misafir"

    def go_to(route):
        def handler(e):
            if on_select:
                on_select()
            page.go(route)
        return handler

    def logout(e):
        if on_select:
            on_select()
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

    return [
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
    ]


def build_sidebar(page, current_route):
    return ft.Container(
        width=240,
        bgcolor=SURFACE_DARK,
        content=ft.Column(
            _nav_content(page, current_route),
            spacing=0,
            expand=True,
        ),
    )


def build_drawer(page, current_route):
    drawer = ft.NavigationDrawer(bgcolor=SURFACE_DARK)

    def close_drawer():
        try:
            page.close(drawer)
        except Exception:
            drawer.open = False
            page.update()

    drawer.controls = _nav_content(page, current_route, on_select=close_drawer)
    return drawer


def shell(page, route, title, subtitle, body_controls, fab=None, header_actions=None):
    mobile = is_mobile(page)
    extras = list(header_actions) if header_actions else []

    title_col = ft.Column([
        ft.Text(title, size=20 if mobile else 22, weight="bold", color=TEXT_PRIMARY),
        ft.Text(subtitle, size=11 if mobile else 12, color=TEXT_MUTED) if subtitle else ft.Container(),
    ], spacing=2, expand=True)

    if mobile:
        drawer = build_drawer(page, route)

        def open_drawer(e):
            try:
                page.open(drawer)
            except Exception:
                drawer.open = True
                page.update()

        header_row = [
            ft.IconButton(icon=ft.Icons.MENU, icon_color=PRIMARY_LIGHT, on_click=open_drawer),
            title_col,
            *extras,
        ]

        return ft.View(
            route=route,
            bgcolor=BG_DARK,
            padding=0,
            drawer=drawer,
            floating_action_button=fab,
            controls=[
                ft.Container(
                    expand=True,
                    bgcolor=BG_DARK,
                    content=ft.Column([
                        ft.Container(
                            content=ft.Row(header_row, vertical_alignment="center", spacing=4),
                            padding=ft.padding.symmetric(horizontal=8, vertical=8),
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
                            padding=ft.padding.symmetric(horizontal=14, vertical=14),
                        ),
                    ], spacing=0, expand=True),
                ),
            ],
        )

    header_row = [title_col, *extras]
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
    mobile = is_mobile(page)
    page_w = getattr(page, "width", None) or 1200
    card_w = min(400, page_w - 24) if mobile else 400
    field_w = card_w - 60
    button_w = card_w - 60

    email = text_field("E-posta", prefix_icon=ft.Icons.EMAIL, width=field_w)
    password = text_field("Şifre", password=True, prefix_icon=ft.Icons.LOCK, width=field_w)
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

    email.on_submit = do_login
    password.on_submit = do_login

    return ft.View(
        route="/login",
        bgcolor=BG_DARK,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(vertical=20, horizontal=12),
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
                            primary_button("Giriş Yap", do_login, icon=ft.Icons.LOGIN, width=button_w),
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
                        width=card_w,
                    ),
                ], horizontal_alignment="center", alignment="center"),
            )
        ],
    )


def build_register_view(page):
    mobile = is_mobile(page)
    page_w = getattr(page, "width", None) or 1200
    card_w = min(420, page_w - 24) if mobile else 420
    field_w = card_w - 60
    half_w = (field_w - 10) // 2
    button_w = card_w - 60

    name = text_field("Ad Soyad", prefix_icon=ft.Icons.PERSON, width=field_w)
    email = text_field("E-posta", prefix_icon=ft.Icons.EMAIL, width=field_w)
    password = text_field("Şifre (en az 6 karakter)", password=True,
                          prefix_icon=ft.Icons.LOCK, width=field_w)
    weight = text_field("Kilo (kg)", prefix_icon=ft.Icons.MONITOR_WEIGHT, width=half_w,
                        keyboard_type=ft.KeyboardType.NUMBER)
    height = text_field("Boy (cm)", prefix_icon=ft.Icons.HEIGHT, width=half_w,
                        keyboard_type=ft.KeyboardType.NUMBER)
    age = text_field("Yaş", prefix_icon=ft.Icons.CAKE, width=half_w,
                     keyboard_type=ft.KeyboardType.NUMBER)

    gender = ft.Dropdown(
        label="Cinsiyet", width=half_w,
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

    for f in (name, email, password, weight, height, age):
        f.on_submit = do_register

    return ft.View(
        route="/register",
        bgcolor=BG_DARK,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(vertical=40, horizontal=12),
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
                                           icon=ft.Icons.PERSON_ADD, width=button_w),
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
                        width=card_w,
                    ),
                ], horizontal_alignment="center", alignment="center"),
            )
        ],
    )


def quick_action(icon, label, route, page, color=PRIMARY, col=None):
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Icon(icon, color=color, size=28),
                bgcolor=f"{color}22", padding=14, border_radius=14,
            ),
            ft.Text(label, color=TEXT_PRIMARY, size=13, weight="w500", text_align="center"),
        ], horizontal_alignment="center", alignment="center", spacing=10),
        on_click=lambda e: page.go(route),
        ink=True,
        padding=16,
        border_radius=14,
        bgcolor=SURFACE_DARK,
        border=ft.border.all(1, BORDER_DARK),
        height=130,
        col=col,
    )


def build_dashboard_view(page):
    user_id = page.session.get("user_id")
    user = database.get_user_by_id(user_id)

    cal_in = database.get_today_calories_in(user_id)
    cal_out = database.get_today_calories_out(user_id)
    net = cal_in - cal_out

    strength_week = database.get_strength_summary(user_id, days=7)

    recent_food = database.get_food_logs(user_id, days=1)[:3]
    recent_ex = database.get_exercise_logs(user_id, days=1)[:3]

    activity_items = []
    for f in recent_food:
        activity_items.append(
            ft.Row([
                ft.Icon(ft.Icons.RESTAURANT, color=WARNING, size=18),
                ft.Column([
                    ft.Text(f["food_name"], color=TEXT_PRIMARY, size=14, weight="w500"),
                    ft.Text(f["logged_at"][11:16], color=TEXT_MUTED, size=12),
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
                            color=TEXT_MUTED, size=12),
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

        ft.Row([
            ft.Text("Bugünün kalori özeti", size=14, weight="bold", color=TEXT_PRIMARY),
            ft.TextButton(
                "Detay",
                on_click=lambda e: page.go("/stats"),
                style=ft.ButtonStyle(color=PRIMARY_LIGHT),
            ),
        ], alignment="spaceBetween"),
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
        ft.Row([
            ft.Text("Bu haftaki kas gelişimi", size=14, weight="bold", color=TEXT_PRIMARY),
            ft.TextButton(
                "Detay",
                on_click=lambda e: page.go("/muscle"),
                style=ft.ButtonStyle(color=PRIMARY_LIGHT),
            ),
        ], alignment="spaceBetween"),
        ft.Container(height=8),
        ft.ResponsiveRow([
            ft.Container(stat_card(ft.Icons.SCALE, "Volüm",
                                   f"{strength_week['volume']:,.0f}".replace(",", "."),
                                   "kg", PRIMARY_LIGHT),
                         col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(stat_card(ft.Icons.FORMAT_LIST_NUMBERED, "Set",
                                   strength_week["sets"], "set", SUCCESS),
                         col={"xs": 12, "sm": 6, "md": 4}),
            ft.Container(stat_card(ft.Icons.EMOJI_EVENTS, "Yeni rekor",
                                   strength_week["new_prs"], "adet", WARNING),
                         col={"xs": 12, "sm": 12, "md": 4}),
        ], spacing=12, run_spacing=12),
        *(
            [
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.TRENDING_UP, color=SUCCESS, size=18),
                        ft.Text(
                            f"En çok büyüyen hareket: {strength_week['top_growth'][0]} "
                            f"({strength_week['top_growth'][2]:g} → {strength_week['top_growth'][3]:g} kg, "
                            f"+{strength_week['top_growth'][1]:g} kg)",
                            color=TEXT_SECONDARY, size=12, expand=True,
                        ),
                    ], spacing=8),
                    bgcolor=f"{SUCCESS}11",
                    padding=10, border_radius=8,
                    margin=ft.margin.only(top=8),
                ),
            ] if strength_week.get("top_growth") else []
        ),

        ft.Container(height=24),
        ft.Text("Hızlı erişim", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(height=8),
        ft.ResponsiveRow([
            quick_action(ft.Icons.CAMERA_ALT, "Yemek\nTara", "/scan", page, PRIMARY,
                         col={"xs": 6, "sm": 4, "md": 3, "lg": 2}),
            quick_action(ft.Icons.ADD_CIRCLE, "Yemek\nEkle", "/food", page, WARNING,
                         col={"xs": 6, "sm": 4, "md": 3, "lg": 2}),
            quick_action(ft.Icons.FITNESS_CENTER, "Egzersiz\nEkle", "/exercise", page, SUCCESS,
                         col={"xs": 6, "sm": 4, "md": 3, "lg": 2}),
            quick_action(ft.Icons.BOLT, "Kas\nGelişimi", "/muscle", page, PROTEIN_COLOR,
                         col={"xs": 6, "sm": 4, "md": 3, "lg": 2}),
            quick_action(ft.Icons.INSIGHTS, "Kalori\nTakibi", "/stats", page, INFO,
                         col={"xs": 12, "sm": 4, "md": 3, "lg": 2}),
        ], spacing=12, run_spacing=12),

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


def build_scan_view(page, server_url, upload_dir):
    user_id = page.session.get("user_id")
    is_phone = is_mobile(page)
    is_android = "android" in (page.client_user_agent or "").lower()

    PICK_LABEL = "Fotoğraf Çek" if is_phone else "Dosya / Galeri"
    PICK_ICON = ft.Icons.PHOTO_CAMERA if is_phone else ft.Icons.PHOTO_LIBRARY

    state = {"image_b64": None, "pending_file": None}

    placeholder = ft.Container(
        width=340, height=340, bgcolor=SURFACE_DARK_2, border_radius=20,
        alignment=ft.alignment.center,
        content=ft.Column([
            ft.Icon(ft.Icons.PHOTO_CAMERA, size=80, color=TEXT_MUTED),
            ft.Text("Fotoğraf çek veya galeriden seç", color=TEXT_MUTED, size=12),
        ], alignment="center", horizontal_alignment="center", spacing=12),
    )

    preview_image = ft.Image(
        width=340, height=340, fit="cover", border_radius=20,
        visible=False, gapless_playback=True,
    )

    overlay_label = ft.Text("Yapay zeka analiz ediyor...", color="white", weight="bold")
    busy_overlay = ft.Container(
        width=340, height=340, bgcolor="#CC000000",
        border_radius=20, alignment=ft.alignment.center, visible=False,
        content=ft.Column([
            ft.ProgressRing(color=PRIMARY_LIGHT, width=40, height=40),
            ft.Container(height=10),
            overlay_label,
        ], alignment="center", horizontal_alignment="center"),
    )

    info_text = ft.Text("", color=TEXT_SECONDARY, size=13, text_align="center")
    result_card_container = ft.Container(visible=False)

    def set_info(msg, color=TEXT_SECONDARY):
        info_text.value = msg
        info_text.color = color

    def show_busy(label):
        overlay_label.value = label
        busy_overlay.visible = True

    def hide_busy():
        busy_overlay.visible = False

    def reset_to_idle(msg=None):
        state["image_b64"] = None
        state["pending_file"] = None
        placeholder.visible = True
        preview_image.visible = False
        hide_busy()
        result_card_container.visible = False
        pick_btn.disabled = False
        pick_btn.text = PICK_LABEL
        pick_btn.icon = PICK_ICON
        analyze_btn.visible = False
        analyze_btn.disabled = False
        if msg:
            set_info(msg)
        page.update()

    def show_error(msg):
        hide_busy()
        pick_btn.disabled = False
        analyze_btn.disabled = False
        set_info(msg, DANGER)
        page.update()

    def render_result_card(resp):
        food_name = resp.get("food_name", "BİLİNMİYOR")
        cal = resp.get("calories", 0)
        macros = resp.get("macros", {})
        advice = resp.get("advice", "")

        def save(e):
            try:
                database.add_food_log(
                    user_id=user_id, food_name=food_name, calories=cal,
                    protein_g=macros.get("protein", "0g"),
                    carbs_g=macros.get("karb", "0g"),
                    fat_g=macros.get("yag", "0g"),
                    source="camera",
                )
                show_snack(page, f"'{food_name}' günlüğüne eklendi!", SUCCESS)
                reset_to_idle("Yeni tarama için butona bas.")
            except Exception as ex:
                show_snack(page, f"Kayıt hatası: {ex}", DANGER)

        result_card_container.content = card(ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(food_name, size=20, weight="bold", color=TEXT_PRIMARY),
                    ft.Text(f"Güven: %{resp.get('confidence', 0)}",
                            size=12, color=TEXT_MUTED),
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Column([
                        ft.Text(str(cal), size=24, weight="bold", color=PRIMARY_LIGHT),
                        ft.Text("kcal", size=10, color=TEXT_MUTED),
                    ], horizontal_alignment="center", spacing=0),
                    bgcolor=f"{PRIMARY}22", border_radius=12,
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                ),
            ]),
            ft.Container(height=10),
            ft.Row([
                macro_chip("Protein", macros.get("protein", "?"), PROTEIN_COLOR),
                macro_chip("Karb", macros.get("karb", "?"), CARB_COLOR),
                macro_chip("Yağ", macros.get("yag", "?"), FAT_COLOR),
            ], spacing=8),
            ft.Container(height=8),
            ft.Container(
                bgcolor=f"{INFO}11", padding=12, border_radius=10,
                content=ft.Row([
                    ft.Icon(ft.Icons.LIGHTBULB, color=INFO, size=18),
                    ft.Text(advice, color=TEXT_SECONDARY, size=12, italic=True, expand=True),
                ], vertical_alignment="start", spacing=8),
            ),
            ft.Container(height=10),
            ft.Row([
                outlined_button("İptal", lambda e: reset_to_idle("Tarama iptal edildi."),
                                icon=ft.Icons.CLOSE),
                primary_button("Günlüğe Ekle", save, icon=ft.Icons.ADD),
            ], alignment="spaceBetween"),
        ], spacing=4), width=520)
        result_card_container.visible = True

    def display_result(resp):
        hide_busy()
        render_result_card(resp)
        pick_btn.disabled = False
        pick_btn.text = "Yeni Tarama"
        pick_btn.icon = ft.Icons.REPLAY
        analyze_btn.visible = False
        set_info("Sonuç hazır. 'Günlüğe Ekle' ile kaydet.")
        page.update()

    def send_for_analysis():
        if not state["image_b64"]:
            show_error("Önce bir fotoğraf seç.")
            return

        pick_btn.disabled = True
        analyze_btn.disabled = True
        show_busy("Yapay zeka analiz ediyor...")
        set_info("Analiz birkaç saniye sürebilir...")
        page.update()

        def worker():
            try:
                resp = requests.post(
                    f"{server_url}/analyze",
                    json={"image": state["image_b64"]},
                    timeout=45,
                ).json()
                if resp.get("status") == "ok":
                    if resp.get("image"):
                        preview_image.src = f"data:image/jpeg;base64,{resp['image']}"
                    display_result(resp)
                else:
                    show_error(resp.get("message", "Analiz başarısız."))
            except requests.Timeout:
                show_error("Sunucu yanıt vermedi (zaman aşımı).")
            except Exception as ex:
                show_error(f"Hata: {ex}")

        threading.Thread(target=worker, daemon=True).start()

    def load_file_bytes(path):
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except Exception as ex:
            show_error(f"Dosya okunamadı: {ex}")
            return
        try:
            os.remove(path)
        except Exception:
            pass

        b64 = base64.b64encode(raw).decode("utf-8")
        state["image_b64"] = b64
        placeholder.visible = False
        preview_image.src = f"data:image/jpeg;base64,{b64}"
        preview_image.visible = True
        hide_busy()
        result_card_container.visible = False
        analyze_btn.visible = True
        analyze_btn.disabled = False
        pick_btn.text = "Başka Fotoğraf"
        pick_btn.icon = ft.Icons.REFRESH
        set_info("Fotoğraf hazır. 'Analiz Et' butonuna basabilirsin.")
        page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        f = e.files[0]

        if f.path and os.path.exists(f.path):
            load_file_bytes(f.path)
            return

        safe_name = f.name.replace("\\", "_").replace("/", "_")
        state["pending_file"] = safe_name
        try:
            upload_url = page.get_upload_url(safe_name, 120)
        except Exception as ex:
            show_error(f"Yükleme adresi alınamadı: {ex}")
            return

        placeholder.visible = False
        pick_btn.disabled = True
        show_busy("Fotoğraf yükleniyor...")
        set_info("Fotoğraf sunucuya yükleniyor...")
        page.update()

        file_picker.upload([ft.FilePickerUploadFile(name=f.name, upload_url=upload_url)])

    def on_upload(e: ft.FilePickerUploadEvent):
        if e.error:
            show_error(f"Yükleme hatası: {e.error}")
            state["pending_file"] = None
            return
        if e.progress is None or e.progress < 1:
            return

        name = state.pop("pending_file", None) or e.file_name
        path = os.path.join(upload_dir, name)
        if not os.path.exists(path):
            path = os.path.join(upload_dir, e.file_name)
        if not os.path.exists(path):
            show_error("Yüklenen dosya bulunamadı.")
            return
        load_file_bytes(path)

    file_picker = ft.FilePicker(on_result=on_file_picked, on_upload=on_upload)
    page.overlay[:] = [ov for ov in page.overlay if not isinstance(ov, ft.FilePicker)]
    page.overlay.append(file_picker)

    def open_picker(e):
        if result_card_container.visible:
            reset_to_idle()
        file_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
        )

    def open_camera_popup(e):
        if not user_id:
            show_snack(page, "Önce giriş yap", DANGER)
            return
        page.launch_url(
            f"/camera-page?user_id={user_id}",
            web_window_name="cengfit_camera",
            web_popup_window=True,
            window_width=440, window_height=760,
        )

    def open_camera_tab(e):
        if not user_id:
            show_snack(page, "Önce giriş yap", DANGER)
            return
        page.launch_url(f"/camera-page?user_id={user_id}", web_window_name="_blank")

    def scan_btn(text, icon, on_click, bg, visible=True):
        return ft.FilledButton(
            text=text, icon=icon, on_click=on_click, visible=visible,
            style=ft.ButtonStyle(
                bgcolor=bg, color="white",
                padding=ft.padding.symmetric(horizontal=24, vertical=18),
                shape=ft.RoundedRectangleBorder(radius=14),
                text_style=ft.TextStyle(weight="bold", size=14),
            ),
        )

    pick_btn = scan_btn(
        PICK_LABEL, PICK_ICON,
        open_camera_tab if is_android else open_picker,
        PRIMARY,
    )
    live_btn = scan_btn("Kamerayı Aç", ft.Icons.VIDEOCAM, open_camera_popup,
                        ACCENT, visible=not is_phone)
    analyze_btn = scan_btn("Analiz Et", ft.Icons.AUTO_AWESOME,
                           lambda e: send_for_analysis(), ACCENT, visible=False)

    preview_frame = ft.Container(
        content=ft.Stack([placeholder, preview_image, busy_overlay],
                         width=340, height=340),
        border_radius=20, border=ft.border.all(2, PRIMARY_DARK),
    )

    if is_android:
        set_info("Butona basınca kamera ve galeri seçenekleri açılır.")
    elif is_phone:
        set_info("Butona basınca telefonun 'kamera' veya 'galeri' seçeneği çıkar.")
    else:
        set_info("Kameradan çek ya da galerideki fotoğrafı seç.")

    button_row = (
        ft.Row([pick_btn], alignment="center")
        if is_phone else
        ft.Row([live_btn, pick_btn], alignment="center", spacing=10, wrap=True)
    )

    body = [
        ft.Container(
            alignment=ft.alignment.top_center,
            content=ft.Column([
                preview_frame,
                ft.Container(height=14),
                info_text,
                ft.Container(height=14),
                button_row,
                ft.Container(height=8),
                ft.Row([analyze_btn], alignment="center"),
                ft.Container(height=20),
                result_card_container,
                ft.Container(height=40),
            ], horizontal_alignment="center"),
        )
    ]

    return shell(page, "/scan", "Yemek Tara",
                 "Fotoğraf çek ya da galeriden seç, kalori ve makroyu otomatik hesaplayalım",
                 body)


def build_food_log_view(page):
    user_id = page.session.get("user_id")

    selected = {"food": None}

    food_name = text_field("Yemek adı", width=320, prefix_icon=ft.Icons.RESTAURANT)
    calories_input = text_field("Kalori (kcal)", width=320,
                                 prefix_icon=ft.Icons.LOCAL_FIRE_DEPARTMENT,
                                 keyboard_type=ft.KeyboardType.NUMBER)
    protein_input = text_field("Protein (g)", width=150, prefix_icon=ft.Icons.SCIENCE,
                                keyboard_type=ft.KeyboardType.NUMBER)
    carbs_input = text_field("Karb (g)", width=150, prefix_icon=ft.Icons.GRAIN,
                              keyboard_type=ft.KeyboardType.NUMBER)
    fat_input = text_field("Yağ (g)", width=150, prefix_icon=ft.Icons.OPACITY,
                            keyboard_type=ft.KeyboardType.NUMBER)
    portion_input = text_field("Adet", value="1", width=150,
                               prefix_icon=ft.Icons.FORMAT_LIST_NUMBERED,
                               keyboard_type=ft.KeyboardType.NUMBER)

    portion_label = ft.Text("", size=11, color=TEXT_MUTED, italic=True)

    def apply_portion():
        food = selected["food"]
        if not food:
            return
        try:
            n = float((portion_input.value or "1").replace(",", "."))
        except ValueError:
            n = 1.0
        if n <= 0:
            n = 1.0
        food_name.value = food["name"]
        calories_input.value = str(round(food["kcal"] * n))
        protein_input.value = f"{food['protein_g'] * n:.1f}"
        carbs_input.value = f"{food['carbs_g'] * n:.1f}"
        fat_input.value = f"{food['fat_g'] * n:.1f}"
        portion_label.value = (
            f"{n:g} {food['portion_name']} • ≈{food['portion_g'] * n:.0f} g"
        )
        page.update()

    def clear_selection():
        selected["food"] = None
        portion_label.value = ""
        portion_input.value = "1"
        food_name.value = ""
        calories_input.value = ""
        protein_input.value = ""
        carbs_input.value = ""
        fat_input.value = ""

    def on_category_change(e):
        cat = e.control.value
        if not cat:
            return
        food_picker.options = [
            ft.dropdown.Option(f["name"]) for f in foods_data.get_by_category(cat)
        ]
        food_picker.value = None
        selected["food"] = None
        portion_label.value = ""
        page.update()

    def on_food_pick(e):
        name = e.control.value
        if not name:
            return
        food = foods_data.find_by_name(name)
        if not food:
            return
        selected["food"] = food
        portion_input.value = "1"
        apply_portion()

    def on_portion_change(e):
        if selected["food"]:
            apply_portion()

    portion_input.on_change = on_portion_change

    category_picker = ft.Dropdown(
        label="Kategori",
        on_change=on_category_change,
        border_color=BORDER_DARK, focused_border_color=PRIMARY,
        bgcolor=SURFACE_DARK_2, border_radius=12,
        content_padding=ft.padding.all(14),
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        text_style=ft.TextStyle(color=TEXT_PRIMARY),
        width=320,
        options=[ft.dropdown.Option(c) for c in foods_data.get_categories()],
    )

    food_picker = ft.Dropdown(
        label="Yemek seç",
        on_change=on_food_pick,
        border_color=BORDER_DARK, focused_border_color=PRIMARY,
        bgcolor=SURFACE_DARK_2, border_radius=12,
        content_padding=ft.padding.all(14),
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        text_style=ft.TextStyle(color=TEXT_PRIMARY),
        width=320,
        options=[],
    )

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
                source="library" if selected["food"] else "manual",
            )
            show_snack(page, "Eklendi!", SUCCESS)
            clear_selection()
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
                ft.Text("Hazır listeden seç", size=12, color=TEXT_SECONDARY, weight="w500"),
                category_picker,
                food_picker,
                ft.Row([portion_input], spacing=10),
                portion_label,
                ft.Divider(height=20, color=BORDER_DARK),
                ft.Text("veya manuel düzenle", size=12, color=TEXT_SECONDARY, weight="w500"),
                food_name,
                calories_input,
                ft.Row([protein_input, carbs_input, fat_input], spacing=10, wrap=True),
            ], spacing=10, tight=True, scroll=ft.ScrollMode.AUTO, height=480),
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
        clear_selection()
        category_picker.value = None
        food_picker.value = None
        food_picker.options = []
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
        src = log.get("source") or "manual"
        if src == "camera":
            icon, icon_color = ft.Icons.CAMERA_ALT, PRIMARY_LIGHT
        elif src == "library":
            icon, icon_color = ft.Icons.MENU_BOOK, SUCCESS
        else:
            icon, icon_color = ft.Icons.EDIT_NOTE, WARNING
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=icon_color, size=22),
                ft.Column([
                    ft.Text(log["food_name"], size=14, weight="bold", color=TEXT_PRIMARY),
                    ft.Text(
                        f"{log['logged_at'][:16].replace('T', ' ')} • "
                        f"P:{log['protein_g']:.0f}g K:{log['carbs_g']:.0f}g Y:{log['fat_g']:.0f}g",
                        size=12, color=TEXT_MUTED,
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
    weight_field = text_field("Ağırlık (kg)", value="", width=320,
                              prefix_icon=ft.Icons.SCALE,
                              keyboard_type=ft.KeyboardType.NUMBER)
    duration_input = text_field("Süre (dakika)", value="30", width=320,
                                prefix_icon=ft.Icons.TIMER,
                                keyboard_type=ft.KeyboardType.NUMBER)

    estimate_text = ft.Text("", size=14, color=PRIMARY_LIGHT, weight="bold")
    one_rm_text = ft.Text("", size=11, color=TEXT_SECONDARY, italic=True)
    info_hint = ft.Text("", size=11, color=TEXT_MUTED, italic=True)

    sets_reps_row = ft.Row([sets_field, reps_field], spacing=10, visible=False)

    def update_estimate(e=None):
        ex = selected["exercise"]
        if not ex:
            estimate_text.value = ""
            one_rm_text.value = ""
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
            else:
                cal = exercises_data.calculate_calories(ex["met"], user_weight, dur)
                estimate_text.value = f"≈ {cal} kcal yakılacak"

            if selected["mode"] == "sets":
                try:
                    w = float(weight_field.value or 0)
                    r = int(reps_field.value or 0)
                    if w > 0 and r > 0:
                        one_rm = database.estimate_1rm(w, r)
                        one_rm_text.value = f"Tahmini 1RM: {one_rm:.1f} kg"
                    else:
                        one_rm_text.value = ""
                except ValueError:
                    one_rm_text.value = ""
            else:
                one_rm_text.value = ""
        except ValueError:
            estimate_text.value = ""
        page.update()

    duration_input.on_change = update_estimate
    sets_field.on_change = update_estimate
    reps_field.on_change = update_estimate
    weight_field.on_change = update_estimate

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

        sets_val, reps_val, weight_val = 0, 0, 0.0
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
            try:
                weight_val = float(weight_field.value or 0)
                if weight_val < 0:
                    weight_val = 0
            except ValueError:
                weight_val = 0

        cal = exercises_data.calculate_calories(ex["met"], user_weight, dur)
        database.add_exercise_log(
            user_id=user_id, exercise_name=ex["name"],
            duration_min=dur, calories_burned=cal, met_value=ex["met"],
            sets=sets_val, reps=reps_val, weight_kg=weight_val,
        )
        msg = f"{ex['name']} • {cal} kcal"
        if sets_val and reps_val:
            msg += f" ({sets_val}×{reps_val}"
            if weight_val > 0:
                msg += f" @ {weight_val:g} kg"
            msg += ")"
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
                weight_field,
                one_rm_text,
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
                weight_field.visible = True
                weight_field.value = ""
                sets_field.value = "3"
                reps_field.value = "10"
                duration_input.label = "Toplam süre (dk, otomatik)"
                duration_input.value = str(max(1, round(3 * SECONDS_PER_SET / 60)))
                info_hint.value = "Ağırlık girersen 1RM tahmini ve kişisel rekorlar takip edilir."
                info_hint.visible = True
            else:
                sets_reps_row.visible = False
                weight_field.visible = False
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
        weight = log.get("weight_kg") or 0
        detail_parts = []
        if sets and reps:
            sr = f"{sets} set × {reps} tekrar"
            if weight > 0:
                sr += f" @ {weight:g} kg"
            detail_parts.append(sr)
        detail_parts.append(f"{log['duration_min']} dk")
        detail_parts.append(log['logged_at'][11:16])
        detail = " • ".join(detail_parts)

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FITNESS_CENTER, color=SUCCESS, size=20),
                ft.Column([
                    ft.Text(log["exercise_name"], size=14, weight="bold", color=TEXT_PRIMARY),
                    ft.Text(detail, size=12, color=TEXT_MUTED),
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

    return shell(page, "/stats", "Kalori Takibi",
                 f"{period_label} kalori özeti ve grafikleri", body)


MUSCLE_PERIOD_DAYS = {"7g": 7, "30g": 30, "90g": 90}
MUSCLE_PERIOD_LABELS = {"7g": "Son 7 gün", "30g": "Son 30 gün", "90g": "Son 90 gün"}


def build_muscle_view(page):
    user_id = page.session.get("user_id")
    today = datetime.now().date()

    period_key = page.session.get("muscle_period") or "7g"
    if period_key not in MUSCLE_PERIOD_DAYS and period_key != "custom":
        period_key = "7g"

    custom_start = page.session.get("muscle_custom_start") or (today - timedelta(days=29)).isoformat()
    custom_end = page.session.get("muscle_custom_end") or today.isoformat()

    if period_key == "custom":
        period_label = f"{custom_start} → {custom_end}"
    else:
        period_label = MUSCLE_PERIOD_LABELS[period_key]

    selected_exercise = page.session.get("muscle_selected_exercise")

    prs = database.get_personal_records(user_id)
    strength_exercises = database.get_distinct_strength_exercises(user_id)

    if period_key == "custom":
        period_logs = database.get_strength_logs_range(user_id, custom_start, custom_end)
    else:
        period_logs = database.get_strength_logs(user_id, days=MUSCLE_PERIOD_DAYS[period_key])

    volume_by_cat = {}
    sets_by_cat = {}
    for log in period_logs:
        ex = exercises_data.find_by_name(log["exercise_name"])
        cat = ex["category"] if ex else "Diğer"
        if cat not in STRENGTH_CATEGORIES:
            continue
        vol = (log["weight_kg"] or 0) * (log["reps"] or 0) * (log["sets"] or 0)
        volume_by_cat[cat] = volume_by_cat.get(cat, 0) + vol
        sets_by_cat[cat] = sets_by_cat.get(cat, 0) + (log["sets"] or 0)

    progression_by_ex = {}
    for ex_name in {log["exercise_name"] for log in period_logs}:
        ex_logs = [l for l in period_logs if l["exercise_name"] == ex_name and (l["weight_kg"] or 0) > 0]
        if len(ex_logs) >= 2:
            ex_logs.sort(key=lambda l: l["logged_at"])
            first_w = ex_logs[0]["weight_kg"]
            last_w = ex_logs[-1]["weight_kg"]
            progression_by_ex[ex_name] = (first_w, last_w, last_w - first_w)

    history = []
    if selected_exercise:
        if period_key == "custom":
            history = database.get_exercise_history_range(
                user_id, selected_exercise, custom_start, custom_end)
        else:
            history = database.get_exercise_history(
                user_id, selected_exercise, days=MUSCLE_PERIOD_DAYS[period_key])

    def set_period(p):
        def handler(e):
            page.session.set("muscle_period", p)
            refresh_view(page, "/muscle")
        return handler

    def period_btn(label, key):
        active = period_key == key
        return ft.FilledButton(
            label, on_click=set_period(key),
            style=ft.ButtonStyle(
                bgcolor=PRIMARY if active else SURFACE_DARK_2,
                color="white" if active else TEXT_SECONDARY,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(horizontal=18, vertical=14),
                text_style=ft.TextStyle(weight="bold", size=13),
            ),
        )

    period_buttons = ft.Row([
        period_btn("7 Gün", "7g"),
        period_btn("30 Gün", "30g"),
        period_btn("90 Gün", "90g"),
        period_btn("Özel aralık", "custom"),
    ], spacing=8, wrap=True)

    def on_start_change(e):
        if e.control.value:
            page.session.set("muscle_custom_start", e.control.value.date().isoformat())
            page.session.set("muscle_period", "custom")
            refresh_view(page, "/muscle")

    def on_end_change(e):
        if e.control.value:
            page.session.set("muscle_custom_end", e.control.value.date().isoformat())
            page.session.set("muscle_period", "custom")
            refresh_view(page, "/muscle")

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
        visible=(period_key == "custom"),
    )

    def on_exercise_change(e):
        page.session.set("muscle_selected_exercise", e.control.value)
        refresh_view(page, "/muscle")

    exercise_picker = ft.Dropdown(
        label="Hareket seç",
        value=selected_exercise if selected_exercise in strength_exercises else None,
        on_change=on_exercise_change,
        border_color=BORDER_DARK, focused_border_color=PRIMARY,
        bgcolor=SURFACE_DARK_2, border_radius=12,
        content_padding=ft.padding.all(16),
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        text_style=ft.TextStyle(color=TEXT_PRIMARY),
        options=[ft.dropdown.Option(name) for name in strength_exercises],
    )

    def build_volume_chart():
        cats = [c for c in STRENGTH_CATEGORIES if volume_by_cat.get(c, 0) > 0]
        if not cats:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FITNESS_CENTER, color=TEXT_MUTED, size=40),
                    ft.Text(f"{period_label}: henüz ağırlıklı çalışma yok",
                            color=TEXT_MUTED, size=13),
                    ft.Text("Egzersiz eklerken kg girersen burada görünecek",
                            color=TEXT_MUTED, size=11),
                ], horizontal_alignment="center", spacing=8),
                padding=ft.padding.symmetric(vertical=30),
                alignment=ft.alignment.center,
            )
        max_vol = max(volume_by_cat[c] for c in cats)
        max_y = ((int(max_vol) // 1000) + 1) * 1000
        groups = []
        labels = []
        for i, cat in enumerate(cats):
            vol = volume_by_cat[cat]
            sets = sets_by_cat[cat]
            groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0, to_y=vol,
                            width=22, color=PRIMARY_LIGHT,
                            border_radius=ft.border_radius.only(top_left=4, top_right=4),
                            tooltip=f"{cat}: {vol:,.0f} kg • {sets} set".replace(",", "."),
                        ),
                    ],
                )
            )
            labels.append(
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Text(cat.split(" ")[0], size=9, color=TEXT_MUTED),
                )
            )
        return ft.BarChart(
            bar_groups=groups,
            border=ft.border.all(0, "transparent"),
            left_axis=ft.ChartAxis(labels_size=50, title=ft.Text("kg", size=11, color=TEXT_MUTED)),
            bottom_axis=ft.ChartAxis(labels=labels, labels_size=30),
            horizontal_grid_lines=ft.ChartGridLines(color=BORDER_DARK, width=0.5, dash_pattern=[3, 3]),
            tooltip_bgcolor=SURFACE_DARK_2,
            tooltip_max_content_width=240,
            tooltip_fit_inside_horizontally=True,
            tooltip_fit_inside_vertically=True,
            tooltip_padding=ft.padding.symmetric(horizontal=10, vertical=6),
            max_y=max_y, min_y=0,
            interactive=True, expand=True, height=240,
        )

    def build_progress_chart():
        if not history:
            return ft.Container(
                content=ft.Text("Bu hareket için kayıt yok", color=TEXT_MUTED, size=13),
                padding=20, alignment=ft.alignment.center,
            )
        weight_points = []
        one_rm_points = []
        labels = []
        for i, h in enumerate(history):
            w = h["weight_kg"] or 0
            r = h["reps"] or 0
            weight_points.append(ft.LineChartDataPoint(x=i, y=w))
            one_rm_points.append(ft.LineChartDataPoint(x=i, y=database.estimate_1rm(w, r)))
            try:
                dt = datetime.fromisoformat(h["logged_at"])
                lbl = dt.strftime("%d/%m")
            except Exception:
                lbl = h["logged_at"][5:10]
            labels.append(ft.ChartAxisLabel(value=i, label=ft.Text(lbl, size=9, color=TEXT_MUTED)))

        max_y = max([p.y for p in one_rm_points] + [10]) * 1.15
        weight_series = ft.LineChartData(
            data_points=weight_points,
            color=PRIMARY_LIGHT, stroke_width=3, curved=False,
            point=True, stroke_cap_round=True,
        )
        one_rm_series = ft.LineChartData(
            data_points=one_rm_points,
            color=WARNING, stroke_width=2, curved=False,
            point=True, stroke_cap_round=True,
        )
        # Etiket çakışmaması için her zaman 6 etiket göstermeye çalış
        step = max(1, len(labels) // 6)
        labels = [labels[i] for i in range(0, len(labels), step)]
        return ft.LineChart(
            data_series=[weight_series, one_rm_series],
            border=ft.border.all(0, "transparent"),
            horizontal_grid_lines=ft.ChartGridLines(color=BORDER_DARK, width=0.5, dash_pattern=[3, 3]),
            left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("kg", size=11, color=TEXT_MUTED)),
            bottom_axis=ft.ChartAxis(labels=labels, labels_size=30),
            min_y=0, max_y=max_y,
            min_x=0, max_x=len(history) - 1 if len(history) > 1 else 1,
            tooltip_bgcolor=SURFACE_DARK_2,
            interactive=True, expand=True, height=240,
        )

    def render_pr_row(pr):
        ex_name = pr["exercise_name"]
        prog = progression_by_ex.get(ex_name)
        delta_widget = ft.Container()
        if prog and abs(prog[2]) >= 0.5:
            first_w, last_w, delta = prog
            color = SUCCESS if delta > 0 else DANGER if delta < 0 else TEXT_MUTED
            sign = "+" if delta > 0 else ""
            delta_widget = ft.Container(
                content=ft.Text(
                    f"{sign}{delta:g} kg ({first_w:g} → {last_w:g})",
                    size=11, color=color, weight="bold",
                ),
                bgcolor=f"{color}22",
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=6,
                margin=ft.margin.only(top=2),
            )

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.EMOJI_EVENTS, color=WARNING, size=22),
                    bgcolor=f"{WARNING}22",
                    padding=10, border_radius=10,
                ),
                ft.Column([
                    ft.Text(ex_name, size=14, weight="bold", color=TEXT_PRIMARY),
                    ft.Text(
                        f"En iyi: {pr['max_weight']:g} kg × {pr['best_reps']} tekrar"
                        + (f" • 1RM ≈ {pr['max_1rm']:g} kg" if pr['max_1rm'] else ""),
                        size=12, color=TEXT_MUTED,
                    ),
                    delta_widget,
                ], spacing=2, expand=True),
                ft.Text(f"{pr['max_weight']:g} kg", size=15, weight="bold", color=PRIMARY_LIGHT),
            ], spacing=12),
            bgcolor=SURFACE_DARK_2, border_radius=10,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            margin=ft.margin.only(bottom=6),
        )

    total_volume = sum(volume_by_cat.values())
    total_sets = sum(sets_by_cat.values())

    body = [
        period_buttons,
        custom_range_row,
        ft.Container(height=16),

        ft.ResponsiveRow([
            ft.Container(stat_card(ft.Icons.SCALE, f"{period_label} volüm",
                                   f"{total_volume:,.0f}".replace(",", "."),
                                   "kg", PRIMARY_LIGHT),
                         col={"xs": 12, "sm": 6}),
            ft.Container(stat_card(ft.Icons.FORMAT_LIST_NUMBERED, f"{period_label} set",
                                   total_sets, "set", SUCCESS),
                         col={"xs": 12, "sm": 6}),
        ], spacing=12, run_spacing=12),
        ft.Container(height=20),

        ft.Text(f"{period_label}: kas grubu volümü", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=INFO, size=16),
                ft.Text(
                    "Volüm = ağırlık × tekrar × set. Örn: 30 kg × 10 tekrar × 4 set = 1200 kg. "
                    "Bu sayı kas büyümesi için en önemli metriklerden biri — ne kadar "
                    "yüksekse o kas grubunda o kadar çok iş yapmışsındır.",
                    color=TEXT_SECONDARY, size=11, expand=True,
                ),
            ], vertical_alignment="start", spacing=8),
            bgcolor=f"{INFO}11", border_radius=8,
            padding=10,
            margin=ft.margin.only(top=4, bottom=10),
        ),
        card(build_volume_chart(), padding=14),
        ft.Container(height=20),

        ft.Text("Hareket bazlı progres", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Text("Bir hareketi seç, zaman içinde ağırlık ve 1RM tahminini gör",
                size=11, color=TEXT_MUTED),
        ft.Container(height=10),
        card(
            ft.Column([
                exercise_picker,
                ft.Container(height=10),
                ft.Row([
                    ft.Container(width=12, height=12, bgcolor=PRIMARY_LIGHT, border_radius=2),
                    ft.Text("Kaldırılan ağırlık", size=11, color=TEXT_SECONDARY),
                    ft.Container(width=14),
                    ft.Container(width=12, height=12, bgcolor=WARNING, border_radius=2),
                    ft.Text("Tahmini 1RM", size=11, color=TEXT_SECONDARY),
                ], spacing=6) if selected_exercise else ft.Container(),
                ft.Container(height=4),
                build_progress_chart() if selected_exercise else ft.Container(
                    content=ft.Text("Yukarıdan bir hareket seç",
                                    color=TEXT_MUTED, size=12, italic=True),
                    padding=20, alignment=ft.alignment.center,
                ),
            ], spacing=4),
            padding=14,
        ),
        ft.Container(height=20),

        ft.Text("Kişisel rekorlar ve ilerleme", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=INFO, size=16),
                ft.Text(
                    "Her hareket için tüm zamanların en yüksek ağırlığı. "
                    "1RM (One-Rep Max): bir tekrarda kaldırabileceğin tahmini maksimum "
                    "ağırlık (Epley formülü). Renkli etiket bu dönemdeki kg değişimini gösterir.",
                    color=TEXT_SECONDARY, size=11, expand=True,
                ),
            ], vertical_alignment="start", spacing=8),
            bgcolor=f"{INFO}11", border_radius=8,
            padding=10,
            margin=ft.margin.only(top=4, bottom=10),
        ),
        *(
            [render_pr_row(pr) for pr in prs] if prs
            else [ft.Container(
                content=ft.Text("Henüz ağırlıklı kayıt yok — egzersize kg gir, burada görünsün",
                                color=TEXT_MUTED, size=13),
                padding=20, alignment=ft.alignment.center,
            )]
        ),
        ft.Container(height=40),
    ]

    return shell(page, "/muscle", "Kas Gelişimi",
                 f"{period_label} performans takibi", body)


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

    # Vücut ölçüleri
    m_weight = text_field("Kilo (kg)", prefix_icon=ft.Icons.MONITOR_WEIGHT, width=160,
                          keyboard_type=ft.KeyboardType.NUMBER)
    m_chest = text_field("Göğüs (cm)", prefix_icon=ft.Icons.STRAIGHTEN, width=160,
                         keyboard_type=ft.KeyboardType.NUMBER)
    m_waist = text_field("Bel (cm)", prefix_icon=ft.Icons.STRAIGHTEN, width=160,
                         keyboard_type=ft.KeyboardType.NUMBER)
    m_hip = text_field("Kalça (cm)", prefix_icon=ft.Icons.STRAIGHTEN, width=160,
                       keyboard_type=ft.KeyboardType.NUMBER)
    m_arm = text_field("Kol (cm)", prefix_icon=ft.Icons.STRAIGHTEN, width=160,
                       keyboard_type=ft.KeyboardType.NUMBER)
    m_thigh = text_field("Bacak (cm)", prefix_icon=ft.Icons.STRAIGHTEN, width=160,
                         keyboard_type=ft.KeyboardType.NUMBER)
    m_fat = text_field("Yağ oranı (%)", prefix_icon=ft.Icons.OPACITY, width=160,
                       keyboard_type=ft.KeyboardType.NUMBER)
    m_note = text_field("Not (opsiyonel)", prefix_icon=ft.Icons.NOTE, width=340)

    def _opt_float(field):
        try:
            return float(field.value) if field.value else None
        except ValueError:
            return None

    def save_measurement(e):
        fields = [m_weight, m_chest, m_waist, m_hip, m_arm, m_thigh, m_fat]
        if not any(f.value for f in fields):
            show_snack(page, "En az bir ölçü gir", DANGER)
            return
        try:
            database.add_body_measurement(
                user_id=user_id,
                weight_kg=_opt_float(m_weight),
                chest_cm=_opt_float(m_chest),
                waist_cm=_opt_float(m_waist),
                hip_cm=_opt_float(m_hip),
                arm_cm=_opt_float(m_arm),
                thigh_cm=_opt_float(m_thigh),
                body_fat_pct=_opt_float(m_fat),
                note=m_note.value.strip() if m_note.value else None,
            )
            show_snack(page, "Ölçüm kaydedildi!", SUCCESS)
            refresh_view(page, "/profile")
        except Exception as ex:
            show_snack(page, f"Hata: {ex}", DANGER)

    measurements = database.get_body_measurements(user_id)

    def build_measurement_chart():
        if len(measurements) < 2:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.STRAIGHTEN, color=TEXT_MUTED, size=36),
                    ft.Text("Trend grafiği için en az 2 ölçüm gerekli",
                            color=TEXT_MUTED, size=12),
                ], horizontal_alignment="center", spacing=6),
                padding=20, alignment=ft.alignment.center,
            )
        series_defs = [
            ("weight_kg", "Kilo", PRIMARY_LIGHT),
            ("chest_cm",  "Göğüs", PROTEIN_COLOR),
            ("waist_cm",  "Bel", WARNING),
            ("arm_cm",    "Kol", SUCCESS),
            ("thigh_cm",  "Bacak", INFO),
            ("body_fat_pct", "Yağ %", FAT_COLOR),
        ]
        series_list = []
        all_vals = []
        for key, _, color in series_defs:
            points = []
            for i, m in enumerate(measurements):
                v = m.get(key)
                if v is not None and v > 0:
                    points.append(ft.LineChartDataPoint(x=i, y=float(v)))
                    all_vals.append(float(v))
            if len(points) >= 2:
                series_list.append(ft.LineChartData(
                    data_points=points,
                    color=color, stroke_width=2, curved=False,
                    point=True, stroke_cap_round=True,
                ))
        if not series_list:
            return ft.Container(
                content=ft.Text("Aynı ölçüyü en az iki kere kaydedince trend çıkar",
                                color=TEXT_MUTED, size=12),
                padding=20, alignment=ft.alignment.center,
            )
        max_y = max(all_vals) * 1.15
        min_y = max(0, min(all_vals) * 0.85)
        labels = []
        for i, m in enumerate(measurements):
            try:
                dt = datetime.fromisoformat(m["logged_at"])
                lbl = dt.strftime("%d/%m")
            except Exception:
                lbl = m["logged_at"][5:10]
            labels.append(ft.ChartAxisLabel(value=i, label=ft.Text(lbl, size=9, color=TEXT_MUTED)))
        step = max(1, len(labels) // 6)
        labels = [labels[i] for i in range(0, len(labels), step)]
        return ft.LineChart(
            data_series=series_list,
            border=ft.border.all(0, "transparent"),
            horizontal_grid_lines=ft.ChartGridLines(color=BORDER_DARK, width=0.5, dash_pattern=[3, 3]),
            left_axis=ft.ChartAxis(labels_size=40),
            bottom_axis=ft.ChartAxis(labels=labels, labels_size=30),
            min_y=min_y, max_y=max_y,
            min_x=0, max_x=len(measurements) - 1,
            tooltip_bgcolor=SURFACE_DARK_2,
            interactive=True, expand=True, height=260,
        )

    def render_measurement_row(m):
        parts = []
        for key, label, unit in [
            ("weight_kg", "Kilo", "kg"), ("chest_cm", "Göğüs", "cm"),
            ("waist_cm", "Bel", "cm"), ("hip_cm", "Kalça", "cm"),
            ("arm_cm", "Kol", "cm"), ("thigh_cm", "Bacak", "cm"),
            ("body_fat_pct", "Yağ", "%"),
        ]:
            v = m.get(key)
            if v is not None and v > 0:
                parts.append(f"{label}: {v:g} {unit}")

        def del_handler(e):
            database.delete_body_measurement(m["id"], user_id)
            show_snack(page, "Ölçüm silindi", WARNING)
            refresh_view(page, "/profile")

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.STRAIGHTEN, color=PRIMARY_LIGHT, size=20),
                ft.Column([
                    ft.Text(m["logged_at"][:10], size=12, weight="bold", color=TEXT_PRIMARY),
                    ft.Text(" • ".join(parts) if parts else "—",
                            size=11, color=TEXT_MUTED),
                    ft.Text(m["note"], size=10, color=TEXT_SECONDARY, italic=True)
                        if m.get("note") else ft.Container(),
                ], spacing=2, expand=True),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE, icon_color=DANGER, icon_size=18,
                    on_click=del_handler,
                ),
            ], spacing=10),
            bgcolor=SURFACE_DARK_2, border_radius=10,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            margin=ft.margin.only(bottom=6),
        )

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
        ft.Container(height=20),

        ft.Text("Vücut ölçüleri", size=14, weight="bold", color=TEXT_PRIMARY),
        ft.Text("Düzenli ölç, zaman içinde kasların gelişimini gör",
                size=11, color=TEXT_MUTED),
        ft.Container(height=10),
        card(
            ft.Column([
                ft.Row([m_weight, m_chest], spacing=10, wrap=True),
                ft.Row([m_waist, m_hip], spacing=10, wrap=True),
                ft.Row([m_arm, m_thigh], spacing=10, wrap=True),
                ft.Row([m_fat], spacing=10),
                m_note,
                ft.Container(height=6),
                primary_button("Yeni ölçüm kaydet", save_measurement,
                               icon=ft.Icons.ADD, width=240),
            ], spacing=10),
        ),
        ft.Container(height=16),
        card(build_measurement_chart(), padding=14),
        ft.Container(height=16),
        ft.Text(f"Geçmiş ölçümler ({len(measurements)})",
                size=13, weight="bold", color=TEXT_PRIMARY),
        ft.Container(height=8),
        *(
            [render_measurement_row(m) for m in reversed(measurements)] if measurements
            else [ft.Container(
                content=ft.Text("Henüz ölçüm yok", color=TEXT_MUTED, size=12),
                padding=16, alignment=ft.alignment.center,
            )]
        ),
        ft.Container(height=40),
    ]

    return shell(page, "/profile", "Profil",
                 "Bilgilerini görüntüle ve düzenle", body)
