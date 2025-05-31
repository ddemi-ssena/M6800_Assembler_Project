# gui/menu_bar.py

import tkinter as tk
from tkinter import ttk # messagebox, filedialog vb. app_logic üzerinden çağrılacak

class AppMenuBar(tk.Menu):
    def __init__(self, master_window, app_logic): # master_window Tk() ana penceresi, app_logic ise MainWindow örneği
        super().__init__(master_window)
        self.app_logic = app_logic # Dosya işlemleri vb. için MainWindow'daki metodları çağıracak

        # Dosya Menüsü
        file_menu = tk.Menu(self, tearoff=0)
        file_menu.add_command(label="Yeni", command=self.app_logic.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Aç...", command=self.app_logic.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Kaydet", command=self.app_logic.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Farklı Kaydet...", command=self.app_logic.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=master_window.quit) # veya app_logic.quit_app
        self.add_cascade(label="Dosya", menu=file_menu)

        # Düzenle Menüsü (Örnek, henüz işlevsel değil)
        edit_menu = tk.Menu(self, tearoff=0)
        edit_menu.add_command(label="Geri Al", command=lambda: self.app_logic.code_editor.edit_undo(), accelerator="Ctrl+Z")
        edit_menu.add_command(label="Yinele", command=lambda: self.app_logic.code_editor.edit_redo(), accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Kes", command=lambda: self.app_logic.code_editor.event_generate("<<Cut>>"), accelerator="Ctrl+X")
        edit_menu.add_command(label="Kopyala", command=lambda: self.app_logic.code_editor.event_generate("<<Copy>>"), accelerator="Ctrl+C")
        edit_menu.add_command(label="Yapıştır", command=lambda: self.app_logic.code_editor.event_generate("<<Paste>>"), accelerator="Ctrl+V")
        self.add_cascade(label="Düzenle", menu=edit_menu)

        # Çalıştır Menüsü
        run_menu = tk.Menu(self, tearoff=0)
        run_menu.add_command(label="Assemble", command=self.app_logic.run_assembly_process, accelerator="F5")
        self.add_cascade(label="Çalıştır", menu=run_menu)

        # Yardım Menüsü (Örnek)
        help_menu = tk.Menu(self, tearoff=0)
        help_menu.add_command(label="Hakkında", command=self.show_about_dialog)
        self.add_cascade(label="Yardım", menu=help_menu)

        # Ana pencereye menüyü ata
        master_window.config(menu=self)

    def show_about_dialog(self):
        # app_logic üzerinden messagebox çağrılabilir veya doğrudan import edilebilir
        # from tkinter import messagebox # Eğer doğrudan kullanılacaksa
        # messagebox.showinfo("Hakkında", "M6800 Assembler GUI\nSürüm 1.0")
        if hasattr(self.app_logic, 'messagebox'): # Eğer app_logic'te messagebox varsa
             self.app_logic.messagebox.showinfo("Hakkında", "M6800 Assembler GUI\nSürüm 1.0")
        else: # Geçici fallback
             print("Hakkında: M6800 Assembler GUI Sürüm 1.0")


# Önemli: `main_window.py` içindeki `AppMenuBar` oluşturma satırını kontrol edin.
# self.menu_bar = AppMenuBar(self, self)
# Burada ilk `self` ana pencere (tk.Tk örneği), ikinci `self` ise `MainWindow` örneği (app_logic olarak).
# Bu yapı `AppMenuBar` sınıfının `__init__` metoduna uygun olmalı.