import sys
import requests
import zipfile
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

MANIFEST_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/manifest.json"

# ── خيط التحميل (عشان ما يتجمد الواجهة) ──────────────────
class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        r = requests.get(self.url, stream=True)
        total = int(r.headers.get("content-length", 0))
        downloaded = 0

        with open(self.save_path, "wb") as f:
            for chunk in r.iter_content(1024 * 64):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    self.progress.emit(int(downloaded / total * 100))

        self.finished.emit(self.save_path)

# ── الواجهة الرئيسية ───────────────────────────────────────
class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 My Launcher")
        self.setMinimumSize(800, 500)
        self.apps = []
        self.init_ui()
        self.load_manifest()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # العنوان
        title = QLabel("🎮 My Launcher")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # قائمة البرامج
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Arial", 13))
        self.list_widget.itemClicked.connect(self.on_select)
        layout.addWidget(self.list_widget)

        # شريط التحميل
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # الأزرار
        btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("⬇️ تحميل")
        self.btn_launch   = QPushButton("▶️ تشغيل")
        self.btn_download.clicked.connect(self.download_app)
        self.btn_launch.clicked.connect(self.launch_app)
        btn_layout.addWidget(self.btn_download)
        btn_layout.addWidget(self.btn_launch)
        layout.addLayout(btn_layout)

        self.status = QLabel("جارٍ تحميل القائمة...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)

    def load_manifest(self):
        try:
            data = requests.get(MANIFEST_URL, timeout=5).json()
            self.apps = data["apps"]
            self.list_widget.clear()
            for app in self.apps:
                self.list_widget.addItem(f"{app['name']}  —  v{app['version']}  ({app['size_mb']} MB)")
            self.status.setText(f"✅ {len(self.apps)} برنامج متاح")
        except Exception as e:
            self.status.setText(f"❌ فشل تحميل القائمة: {e}")

    def on_select(self, item):
        idx = self.list_widget.row(item)
        app = self.apps[idx]
        self.status.setText(f"اخترت: {app['name']}")

    def download_app(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            self.status.setText("⚠️ اختر برنامجاً أولاً")
            return

        app = self.apps[idx]
        os.makedirs("downloads", exist_ok=True)
        save_path = f"downloads/{app['id']}.zip"

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status.setText(f"⬇️ جارٍ تحميل {app['name']}...")

        self.thread = DownloadThread(app["download_url"], save_path)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self.on_download_done)
        self.thread.start()

    def on_download_done(self, path):
        # فك الضغط
        with zipfile.ZipFile(path, "r") as z:
            z.extractall(path.replace(".zip", ""))
        self.progress_bar.setVisible(False)
        self.status.setText("✅ اكتمل التحميل!")

    def launch_app(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            self.status.setText("⚠️ اختر برنامجاً أولاً")
            return

        app = self.apps[idx]
        exe_path = f"downloads/{app['id']}/main.exe"  # غيّر حسب اسم الملف
        if os.path.exists(exe_path):
            os.startfile(exe_path)
        else:
            self.status.setText("❌ البرنامج غير محمّل بعد")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec())