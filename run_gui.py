# run_gui.py (GUI Başlatıcısı)
import tkinter as tk # Eğer Tkinter kullanıyorsanız
# from PySide6.QtWidgets import QApplication # Eğer PySide6 kullanıyorsanız
import sys
import os

# Proje kök dizinini Python'un arama yoluna ekleyelim
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# GUI ana pencere sınıfınızı import edin
try:
    # Bir önceki cevaptaki Tkinter örneğine göre:
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"HATA: GUI modülleri yüklenemedi. Proje yapınızı kontrol edin.")
    print(f"Detay: {e}")
    print("PYTHONPATH ortam değişkeninizin doğru ayarlandığından veya")
    print("bu script'i proje kök dizininden çalıştırdığınızdan emin olun.")
    sys.exit(1)

if __name__ == "__main__":
    # Tkinter için:
    app_gui = MainWindow()
    app_gui.mainloop()

    # PySide6/PyQt için:
    # app = QApplication(sys.argv)
    # window = MainWindow() # Sizin PyQt/PySide ana pencere sınıfınız
    # window.show()
    # sys.exit(app.exec())