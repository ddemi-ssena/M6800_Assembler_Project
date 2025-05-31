# gui/widgets.py

import tkinter as tk
from tkinter import ttk

class CodeEditor(tk.Text):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        # Burada CodeEditor'a özel ayarlar yapabilirsiniz
        # Örneğin, satır numaraları, sözdizimi vurgulama vb.
        self.configure(wrap=tk.WORD, undo=True) # Örnek yapılandırma
        self.tag_configure("sel", background="lightblue") # Seçim için renk

    def get_code(self):
        return self.get("1.0", tk.END)

    def set_code(self, text):
        self.delete("1.0", tk.END)
        self.insert("1.0", text)

    def clear_code(self):
        self.delete("1.0", tk.END)

    # Değişiklik takibi için edit_modified gibi metodlar eklenebilir
    # def edit_modified(self, arg=None):
    #     # Tkinter'in kendi edit_modified metodunu kullanır
    #     return super().edit_modified(arg)


class OutputDisplay(tk.Text):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        # Burada OutputDisplay'e özel ayarlar yapabilirsiniz
        # Örneğin, sadece okunabilir yapma
        self.configure(state=tk.DISABLED, wrap=tk.WORD) # Başlangıçta sadece okunabilir

    def set_text(self, text):
        self.configure(state=tk.NORMAL) # Yazmak için etkinleştir
        self.delete("1.0", tk.END)
        self.insert("1.0", text)
        self.configure(state=tk.DISABLED) # Tekrar sadece okunabilir yap

    def append_text(self, text):
        self.configure(state=tk.NORMAL)
        self.insert(tk.END, text + "\n")
        self.see(tk.END) # En sona kaydır
        self.configure(state=tk.DISABLED)

    def clear_text(self):
        self.configure(state=tk.NORMAL)
        self.delete("1.0", tk.END)
        self.configure(state=tk.DISABLED)

# Eğer başka widget'larınız varsa onları da buraya ekleyin.
# Örneğin, menu_bar.py'daki AppMenuBar da eğer burada tanımlanacaksa:
# class AppMenuBar(tk.Menu):
#     def __init__(self, master=None, app_logic=None, **kwargs):
#         super().__init__(master, **kwargs)
#         # ... menü içeriği ...