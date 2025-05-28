# 📦 Importaciones necesarias
import ttkbootstrap as ttk                         # Interfaz moderna basada en ttk
from ttkbootstrap.constants import *               # Constantes de estilo
import tkinter as tk                               # Librería gráfica estándar
from tkinter import filedialog, messagebox         # Diálogos para archivos y mensajes
from PIL import Image, ImageTk                     # Manejo de imágenes
import subprocess, threading                       # Ejecutar procesos externos, tareas en paralelo
import os, json, re, io, urllib.request, shutil     # Utilidades generales
import pyperclip                                   # Acceso al portapapeles

# 🎬 Clase principal de la aplicación
class YouTubeDownloaderApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.title("🎬 YouTube Video Downloader")
        self.geometry("920x650")
        self.resizable(False, False)

        # Variables de estado
        self.url_var = tk.StringVar()              # Enlace del video
        self.output_dir = tk.StringVar(value=os.getcwd())  # Carpeta de destino
        self.format_map = {}                       # Mapa: etiqueta → formato video
        self.audio_map = {}                        # Mapa: etiqueta → formato audio
        self.selected_format = tk.StringVar(value="Seleccione calidad")
        self.selected_audio = tk.StringVar(value="Seleccionar audio")
        self.status_var = tk.StringVar(value="🔹 Listo para comenzar")

        # Construir interfaz y empezar a monitorear el portapapeles
        self.create_widgets()
        self.monitor_clipboard()

    def create_widgets(self):
        # 📐 Contenedor principal
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill='both', expand=True)

        # 🏷️ Etiqueta del título del video
        self.title_label = ttk.Label(frame, text="", font=("Segoe UI", 12, "bold"))
        self.title_label.grid(row=0, column=0, columnspan=4, sticky="w")

        # 🔗 Campo para enlace de YouTube
        ttk.Label(frame, text="🎥 Enlace de YouTube:", font=("Segoe UI", 11, "bold"), bootstyle="info")\
            .grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.url_var, width=90, font=("Consolas", 10))\
            .grid(row=2, column=0, columnspan=4, pady=5)

        # 📁 Selección de carpeta de destino
        ttk.Label(frame, text="📁 Carpeta de destino:", font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.output_dir, width=70, font=("Consolas", 10))\
            .grid(row=4, column=0, columnspan=3, pady=5)
        ttk.Button(frame, text="Seleccionar", command=self.select_folder, bootstyle="secondary-outline")\
            .grid(row=4, column=3, padx=(10, 0))

        # 🔍 Botón para obtener formatos disponibles
        ttk.Button(frame, text="🔍 Cargar formatos", command=self.load_formats, bootstyle="info-outline")\
            .grid(row=5, column=0, columnspan=4, pady=12)

        # 🎞️ Selectores de calidad de video y pista de audio
        self.format_menu = ttk.Combobox(frame, textvariable=self.selected_format, state="readonly", width=60, font=("Segoe UI", 10))
        self.format_menu.grid(row=6, column=0, columnspan=2, pady=6)

        self.audio_menu = ttk.Combobox(frame, textvariable=self.selected_audio, state="readonly", width=60, font=("Segoe UI", 10))
        self.audio_menu.grid(row=6, column=2, columnspan=2, pady=6)

        # ⬇ Botón de descarga
        ttk.Button(frame, text="⬇ Descargar", command=self.start_download, bootstyle="success")\
            .grid(row=7, column=0, columnspan=4, pady=16)

        # 📊 Barra de progreso
        self.progress = ttk.Progressbar(frame, orient="horizontal", length=860, mode="determinate", bootstyle="success")
        self.progress.grid(row=8, column=0, columnspan=4, pady=6)

        # 🖼️ Miniatura del video
        self.thumbnail_label = ttk.Label(frame)
        self.thumbnail_label.grid(row=9, column=0, columnspan=4, pady=10)

        # 📣 Estado actual
        ttk.Label(frame, textvariable=self.status_var, wraplength=860, font=("Segoe UI", 9, "italic"))\
            .grid(row=10, column=0, columnspan=4, sticky="w", pady=10)

    def is_valid_youtube_url(self, text):
        # Verifica si el texto es un enlace válido de YouTube
        pattern = r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}"
        return re.match(pattern, text.strip()) is not None

    def monitor_clipboard(self):
        # Monitorea el portapapeles cada 3 segundos
        try:
            clip = pyperclip.paste()
            if self.is_valid_youtube_url(clip) and clip != self.url_var.get():
                self.url_var.set(clip)
                self.status_var.set("🔗 Enlace detectado, cargando formatos...")
                self.load_formats()
        except Exception:
            pass
        self.after(3000, self.monitor_clipboard)

    def select_folder(self):
        # Abre un diálogo para seleccionar carpeta
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir.set(folder)

    def set_video_title(self, title):
        # Muestra el título del video en la parte superior
        self.title_label.configure(text=f"🎬 {title}" if title else "")

    def load_formats(self):
        # Carga información del video y los formatos disponibles
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("⚠️ Advertencia", "Por favor ingrese un enlace válido.")
            return

        self.status_var.set("🔄 Cargando formatos disponibles...")
        self.format_map.clear()
        self.audio_map.clear()
        self.selected_format.set("Cargando...")
        self.selected_audio.set("Cargando...")

        cmd = ["yt-dlp", "-j", url]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            video_info = json.loads(output)
            formats = video_info.get("formats", [])
            thumbnail_url = video_info.get("thumbnail")
            title = video_info.get("title")

            self.set_video_title(title)
            self.load_thumbnail(thumbnail_url)

            video_only = []
            audio_tracks = []

            for f in formats:
                fmt_id = f.get("format_id")
                acodec = f.get("acodec")
                vcodec = f.get("vcodec")
                height = f.get("height")
                fps = f.get("fps")
                lang = f.get("language") or "Desconocido"
                abr = f.get("abr", 0)

                if vcodec != "none" and height:
                    label = f"{height}p{int(fps) if fps else ''}"
                    video_only.append((label, fmt_id))
                elif vcodec == "none" and acodec != "none":
                    label = f"{lang} ({int(abr)} kbps)" if abr else lang
                    audio_tracks.append((label, fmt_id))

            # Cargar en los menús
            resolutions = []
            for label, v_id in sorted(video_only, reverse=True):
                if label not in resolutions:
                    self.format_map[label] = v_id
                    resolutions.append(label)

            audio_labels = []
            for label, a_id in sorted(audio_tracks, key=lambda x: x[0]):
                self.audio_map[label] = a_id
                audio_labels.append(label)

            self.format_menu['values'] = resolutions if resolutions else ["No disponible"]
            self.selected_format.set(resolutions[0] if resolutions else "No disponible")

            self.audio_menu['values'] = audio_labels if audio_labels else ["No disponible"]
            self.selected_audio.set(audio_labels[0] if audio_labels else "No disponible")

            self.status_var.set("✅ Formatos cargados correctamente.")

        except Exception as e:
            self.status_var.set(f"❌ Error: {e}")
            self.selected_format.set("Error")
            self.selected_audio.set("Error")

    def load_thumbnail(self, url):
        # Carga y muestra la miniatura del video
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read()
                img = Image.open(io.BytesIO(data)).resize((360, 200))
                self.thumb_image = ImageTk.PhotoImage(img)
                self.thumbnail_label.configure(image=self.thumb_image)
        except:
            self.thumbnail_label.configure(image="")

    def start_download(self):
        # Inicia la descarga del video con los formatos seleccionados
        url = self.url_var.get().strip()
        res_label = self.selected_format.get()
        audio_label = self.selected_audio.get()

        if res_label not in self.format_map or audio_label not in self.audio_map:
            messagebox.showwarning("⚠️ Advertencia", "Debe seleccionar una calidad de video y una pista de audio.")
            return

        video_id = self.format_map[res_label]
        audio_id = self.audio_map[audio_label]
        format_id = f"{video_id}+{audio_id}"

        self.status_var.set("⬇ Iniciando descarga...")
        self.progress['value'] = 0

        threading.Thread(target=self.download_video, args=(url, format_id), daemon=True).start()

    def download_video(self, url, format_id):
        # Ejecuta yt-dlp y actualiza la barra de progreso
        output_path = self.output_dir.get()
        output_template = os.path.join(output_path, "%(title)s.%(ext)s")

        cmd = [
            "yt-dlp", "-f", format_id,
            "--merge-output-format", "mp4",
            "-o", output_template,
            "--newline", url
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        prog_re = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")

        for line in proc.stdout:
            line = line.strip()
            m = prog_re.search(line)
            if m:
                self.progress['value'] = float(m.group(1))
                self.status_var.set(f"⏳ Descargando... {m.group(1)}%")
            else:
                self.status_var.set(line)

        proc.wait()
        if proc.returncode == 0:
            self.progress['value'] = 100
            self.status_var.set("✅ Descarga completada.")
            messagebox.showinfo("Éxito", "El video se descargó correctamente.")
        else:
            self.status_var.set("❌ Error durante la descarga.")


# 🚪 Punto de entrada principal
if __name__ == "__main__":
    if not shutil.which("yt-dlp"):
        messagebox.showerror("Error", "yt-dlp no está instalado o no está en el PATH.")
    else:
        app = YouTubeDownloaderApp()
        app.mainloop()
