import flet as ft
import time
import cv2
import base64
import threading

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
REQUESTED_CAMERA_FPS = 120
JPEG_QUALITY = 45

def main(page: ft.Page):
    page.title = "NutriSnap - Canlı Kamera"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    is_camera_running = False
    cap = None

    def install_app_simulation(e):
        snack = ft.SnackBar(
            content=ft.Text("PWA Yükleme tetiklendi! Uygulama ana ekrana ekleniyor..."),
            bgcolor=ft.Colors.GREEN_700
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    page.appbar = ft.AppBar(
        title=ft.Text("Yemek Tarayıcı", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        center_title=True,
        bgcolor=ft.Colors.TEAL,
        actions=[
            ft.IconButton(
                icon=ft.Icons.INSTALL_MOBILE, 
                icon_color=ft.Colors.WHITE, 
                tooltip="Ana Ekrana Ekle",
                on_click=install_app_simulation
            )
        ]
    )

    def macro_widget(label, value, color):
        return ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=12, color=ft.Colors.BLACK54),
            ]
        )

    TRANSPARENT_PIXEL = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

    camera_image = ft.Image(
        src=f"data:image/png;base64,{TRANSPARENT_PIXEL}", 
        width=250, 
        height=250, 
        fit="cover", 
        border_radius=20,
        gapless_playback=True,
        placeholder_src=f"data:image/png;base64,{TRANSPARENT_PIXEL}",
        placeholder_fit="cover",
        fade_in_animation=0,
        placeholder_fade_out_animation=0,
        cache_width=250,
        cache_height=250,
        visible=False
    )

    camera_container = ft.Container(
        width=250,
        height=250,
        bgcolor=ft.Colors.GREY_200,
        border_radius=20,
        border=ft.border.all(2, ft.Colors.TEAL),
        alignment=ft.Alignment(0, 0), 
        content=ft.Icon(ft.Icons.RESTAURANT, size=80, color=ft.Colors.GREY)
    )

    results_card = ft.Card(
        elevation=4,
        visible=False,
        content=ft.Container(
            padding=20,
            width=350,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[] 
            )
        )
    )

    info_text = ft.Text(
        "Kamerayı açmak için aşağıdaki butona tıklayın.",
        text_align=ft.TextAlign.CENTER,
        color=ft.Colors.BLACK54,
        size=16
    )

    # --- YÜKSEK FPS, FLASH YAPMAYAN KAMERA DÖNGÜSÜ ---
    def update_camera_frame():
        nonlocal is_camera_running, cap
        
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        # Düşük çözünürlük + MJPG, çoğu webcam'de en yüksek FPS'i verir.
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, REQUESTED_CAMERA_FPS)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY] 

        while is_camera_running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.005)
                continue
                
            # Görüntüyü kare yap
            h, w, _ = frame.shape
            min_dim = min(h, w)
            start_x = (w - min_dim) // 2
            start_y = (h - min_dim) // 2
            cropped_frame = frame[start_y:start_y+min_dim, start_x:start_x+min_dim]
            
            # Görüntüyü UI'daki kutunun boyutuna küçült (250x250)
            resized_frame = cv2.resize(cropped_frame, (250, 250), interpolation=cv2.INTER_LINEAR)
            
            ok, im_arr = cv2.imencode('.jpg', resized_frame, encode_param)
            if not ok:
                continue

            im_b64 = base64.b64encode(im_arr).decode('utf-8')
            
            camera_image.src = f"data:image/jpeg;base64,{im_b64}"
            
            try:
                camera_image.update()
            except Exception:
                pass
            
        if cap is not None:
            cap.release()

    def handle_main_action(e):
        nonlocal is_camera_running
        
        if not is_camera_running:
            is_camera_running = True
            info_text.value = "Yemeği çerçeveye alın ve\ntekrar butona basarak fotoğrafı çekin."
            info_text.visible = True
            results_card.visible = False
            
            camera_image.visible = True
            camera_container.content = camera_image
            
            fab.icon = ft.Icons.CAMERA
            fab.tooltip = "Fotoğrafı Çek ve Analiz Et"
            fab.bgcolor = ft.Colors.RED_400 
            
            page.update()
            
            threading.Thread(target=update_camera_frame, daemon=True).start()

        else:
            is_camera_running = False 
            fab.disabled = True
            info_text.visible = False
            
            camera_container.content = ft.Stack([
                camera_image, 
                ft.Container( 
                    bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.ProgressRing(color=ft.Colors.TEAL),
                            ft.Text("Yapay Zeka Analiz Ediyor...", color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.BOLD)
                        ]
                    )
                )
            ])
            page.update()

            time.sleep(2)
            
            food_name = "tavuklu makarna"
            calories = 350
            macros = {"Protein": 30, "Karbonhidrat": 5, "Yağ": 20}
            advice = "Yüksek omega-3 içerikli harika bir tercih! Günlük hedefine uygun."

            camera_container.content = camera_image 
            
            results_card.content.content.controls = [
                ft.Text(food_name, size=22, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text(f"{calories} kcal", size=28, color=ft.Colors.TEAL, weight=ft.FontWeight.BOLD),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    controls=[
                        macro_widget("Protein", f"{macros['Protein']}g", ft.Colors.RED_ACCENT),
                        macro_widget("Karb", f"{macros['Karbonhidrat']}g", ft.Colors.ORANGE),
                        macro_widget("Yağ", f"{macros['Yağ']}g", ft.Colors.AMBER),
                    ]
                ),
                ft.Container(
                    margin=ft.margin.only(top=15),
                    padding=10,
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    content=ft.Text(f"💡 {advice}", color=ft.Colors.BLUE_800, italic=True, text_align=ft.TextAlign.CENTER)
                )
            ]
            
            results_card.visible = True
            
            fab.disabled = False
            fab.icon = ft.Icons.REPLAY
            fab.tooltip = "Yeni Görüntü Tara"
            fab.bgcolor = ft.Colors.TEAL
            page.update()

    fab = ft.FloatingActionButton(
        icon=ft.Icons.VIDEOCAM,
        tooltip="Kamerayı Aç", 
        bgcolor=ft.Colors.TEAL,
        on_click=handle_main_action
    )
    
    page.floating_action_button = fab
    page.floating_action_button_location = ft.FloatingActionButtonLocation.CENTER_FLOAT

    page.add(
        camera_container,
        ft.Container(height=10),
        info_text,
        results_card
    )

# Uygulamayı web tarayıcısında başlatmak için WEB_BROWSER view parametresini ekledik
ft.app(target=main, view=ft.AppView.WEB_BROWSER)