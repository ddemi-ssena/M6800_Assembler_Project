# gui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os # Dosya yolu işlemleri için

# assembler_core paketinden gerekli modülleri import et
# Proje kök dizininin Python path'ine eklenmiş olması gerekebilir
# veya main.py'den çalıştırırken bu importlar sorunsuz olmalı.
try:
    from assembler_core import assembler
except ImportError:
    # Eğer doğrudan bu dosyayı çalıştırmaya çalışıyorsak (test amaçlı)
    # ve assembler_core bir üst dizindeyse, sys.path'i ayarlamamız gerekebilir.
    # Genellikle main.py üzerinden çalıştıracağımız için bu bloğa ihtiyaç olmayabilir.
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from assembler_core import assembler


from .widgets import CodeEditor, OutputDisplay # Kendi widget'larımız
from .menu_bar import AppMenuBar # Menü çubuğumuz

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("M6800 Assembler - Tkinter")
        self.geometry("900x700")

        self.current_file_path = None # Açık olan dosyanın yolu

        self._setup_ui()
        self.menu_bar = AppMenuBar(self, self) # Menü çubuğunu oluştur ve app_logic olarak kendini (MainWindow) ver

    def _setup_ui(self):
        # Ana çerçeveyi PanedWindow ile ikiye bölmek daha esnek olabilir
        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Sol Panel: Kod Editörü ve Derleme Butonu
        left_frame = ttk.Frame(main_paned_window, padding=5)
        self.code_editor = CodeEditor(left_frame, height=20, width=60)
        self.code_editor.pack(fill=tk.BOTH, expand=True, pady=(0,5))

        self.assemble_button = ttk.Button(left_frame, text="Assemble (F5)", command=self.run_assembly_process)
        self.assemble_button.pack(fill=tk.X, pady=(5,0))
        main_paned_window.add(left_frame, weight=1) # weight ile boyutlandırma önceliği

        # Sağ Panel: Çıktı Alanları (Sekmeli olabilir)
        right_frame = ttk.Frame(main_paned_window, padding=5)
        notebook = ttk.Notebook(right_frame) # Sekmeli görünüm için

        self.listing_display = OutputDisplay(notebook, height=15, width=50)
        notebook.add(self.listing_display, text="Listeleme")

        self.symbol_table_display = OutputDisplay(notebook, height=15, width=50)
        notebook.add(self.symbol_table_display, text="Sembol Tablosu")

        self.machine_code_display = OutputDisplay(notebook, height=15, width=50)
        notebook.add(self.machine_code_display, text="Makine Kodu")

        self.error_display = OutputDisplay(notebook, height=5, width=50)
        self.error_display.configure(background="lightyellow") # Hata alanı için farklı renk
        notebook.add(self.error_display, text="Hatalar/Uyarılar")

        notebook.pack(fill=tk.BOTH, expand=True)
        main_paned_window.add(right_frame, weight=2) # Sağ panel biraz daha geniş olsun

        # --- Durum Çubuğu ---
        self.status_bar = ttk.Label(self, text="Hazır", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _update_status(self, message):
        self.status_bar.config(text=message)

    def new_file(self):
        if self._ask_save_if_needed():
            self.code_editor.clear_code()
            self.listing_display.clear_text()
            self.symbol_table_display.clear_text()
            self.machine_code_display.clear_text()
            self.error_display.clear_text()
            self.current_file_path = None
            self.title("M6800 Assembler - Tkinter - Yeni Dosya")
            self._update_status("Yeni dosya oluşturuldu.")

    def _ask_save_if_needed(self):
        # TODO: Kod editöründe değişiklik olup olmadığını kontrol et
        # Şimdilik her zaman True dönüyoruz
        # if self.code_editor.edit_modified(): # Değişiklik varsa
        #    response = messagebox.askyesnocancel("Kaydet?", "Değişiklikleri kaydetmek ister misiniz?")
        #    if response is True: self.save_file()
        #    elif response is None: return False # Cancel
        return True

    def open_file(self):
        if not self._ask_save_if_needed():
            return

        file_path = filedialog.askopenfilename(
            defaultextension=".asm",
            filetypes=[("Assembly Dosyaları", "*.asm *.s"), ("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.code_editor.set_code(f.read())
                self.current_file_path = file_path
                self.title(f"M6800 Assembler - Tkinter - {os.path.basename(file_path)}")
                self._update_status(f"Dosya açıldı: {file_path}")
            except Exception as e:
                messagebox.showerror("Dosya Açma Hatası", f"Dosya okunamadı:\n{e}")
                self._update_status(f"Dosya açma hatası: {e}")


    def save_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.code_editor.get_code())
                self.title(f"M6800 Assembler - Tkinter - {os.path.basename(self.current_file_path)}")
                self._update_status(f"Dosya kaydedildi: {self.current_file_path}")
                # self.code_editor.edit_modified(False) # Değişiklik bayrağını sıfırla
            except Exception as e:
                messagebox.showerror("Dosya Kaydetme Hatası", f"Dosya kaydedilemedi:\n{e}")
                self._update_status(f"Dosya kaydetme hatası: {e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".asm",
            filetypes=[("Assembly Dosyaları", "*.asm *.s"), ("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            self.current_file_path = file_path
            self.save_file() # save_file şimdi current_file_path'i kullanacak

    def run_assembly_process(self):
        self._update_status("Derleniyor...")
        self.listing_display.clear_text()
        self.symbol_table_display.clear_text()
        self.machine_code_display.clear_text()
        self.error_display.clear_text() # Hata ekranını her seferinde temizle

        source_code = self.code_editor.get_code()
        if not source_code.strip():
            messagebox.showwarning("Boş Kod", "Derlenecek kod bulunmuyor.")
            self._update_status("Derleme iptal edildi: Kod boş.")
            return

        source_lines = source_code.strip().split('\n')

        try:
            # --- Pass 1 ---
            sym_table, proc_lines_p1, errs_p1 = assembler.pass_one(source_lines)

            # --- Pass 1 Hatalarını Göster (Hatalar/Uyarılar Sekmesi) ---
            # errs_p1 listesi zaten formatlı mesajlar içermeli ("Satır X (Lexer): ..." veya "Satır X: ...")
            if errs_p1:
                self.error_display.append_text("--- PASS 1 / LEXER HATALARI ---")
                for err_msg in errs_p1:
                    self.error_display.append_text(err_msg)

            # --- Pass 2 ---
            # Pass 2'ye, Pass 1'den gelen işlenmiş satırları (hatalarıyla birlikte) ve sembol tablosunu veriyoruz.
            final_listing, mc_segments, errs_p2_combined = assembler.pass_two(proc_lines_p1, sym_table)

            # --- Sembol Tablosunu Göster ---
            self.symbol_table_display.set_text(str(sym_table))

            # --- Listelemeyi Oluştur ve Göster ---
            listing_text_lines = [] # Listeleme için satırları biriktireceğimiz liste
            for entry in final_listing:
                # Temel listeleme satırını oluştur
                line = f"L:{entry['line_num']:<3} Adr:{entry['address_hex']:<6} Kod:{entry['machine_code_hex']:<10} "
                line += f"{entry['label'] or '':<8} {entry['mnemonic'] or '':<6} {entry['operand_str'] or '':<15}"
                if entry['comment']:
                    line += f"; {entry['comment']}"
                listing_text_lines.append(line)

                # Eğer bu satır için bir hata varsa (Lexer, Pass 1 veya Pass 2'den), listelemeye ekle
                # entry['error'] ham hata mesajını içerir (örn: "Tanımsız ifade...")
                # errs_p1 zaten formatlı ("Satır X (Lexer): ...")
                # errs_p2_combined da formatlı olabilir veya ham olabilir, assembler.py'ye bağlı.
                # Şimdilik, entry['error']'ı doğrudan kullanalım.
                # Pass 1'den gelen hatalar (lexer dahil) zaten entry['error'] içinde olmalı.
                # Pass 2'de oluşan yeni hatalar da pass_two tarafından entry['error']'a eklenir.
                if entry.get('error'):
                    # Hatanın kaynağını (P1, P2) belirtmek için daha karmaşık bir mantık kurulabilir,
                    # ama en basit haliyle hata mesajını yazdıralım.
                    # Hata mesajının başına "HATA:" ekleyebiliriz.
                    # `errs_p1` zaten genel hata ekranında gösteriliyor, bu yüzden burada
                    # sadece satırın yanında hatayı göstermek yeterli olabilir.
                    # Eğer `errs_p1` içindeki mesaj, `entry['error']` ile aynıysa (veya onu içeriyorsa),
                    # bu bir Pass 1/Lexer hatasıdır.
                    
                    # Basitleştirilmiş gösterim:
                    listing_text_lines.append(f"    HATA: {entry['error']}")

            self.listing_display.set_text("\n".join(listing_text_lines))


            # --- Sadece Pass 2'de Oluşan Farklı Hataları Göster (Hatalar/Uyarılar Sekmesi) ---
            # errs_p2_combined, pass_two'dan dönen tüm Pass 2 hatalarını içerir.
            # Bunlardan Pass 1'de zaten raporlanmamış olanları ayıklamaya gerek yok,
            # çünkü Pass 1 hataları zaten errs_p1 ile yukarıda gösterildi.
            # Sadece errs_p2_combined'daki (Pass 1'den gelenler hariç) hataları göstermek istiyorsak:
            
            unique_pass2_errors = []
            if errs_p2_combined: # Eğer pass_two'dan herhangi bir hata mesajı listesi döndüyse
                pass1_error_raw_messages = set() # Pass 1'den gelen ham hata mesajlarını tutmak için
                for p1_entry in proc_lines_p1:
                    if p1_entry.get('error'):
                        pass1_error_raw_messages.add(p1_entry['error'])
                
                for p2_err_msg_from_pass_two in errs_p2_combined:
                    # p2_err_msg_from_pass_two, "Satır X: mesaj" formatında olabilir.
                    # Eğer bu mesajın özü, Pass 1'den gelen bir hatanın özü değilse,
                    # o zaman bu gerçekten yeni bir Pass 2 hatasıdır.
                    # Bu karşılaştırma biraz karmaşık olabilir.
                    # Şimdilik, errs_p2_combined'ı olduğu gibi yazdıralım ve
                    # assembler.py'nin pass_two fonksiyonunun sadece YENİ P2 hatalarını döndürdüğünü varsayalım.
                    # (assembler.py'de `errors_pass2` listesi sadece P2'de oluşanları tutuyordu)
                    is_already_in_p1_formatted_list = False
                    for p1_formatted_err in errs_p1:
                        # errs_p2_combined'daki mesajlar "Satır X: Hata" formatında olabilir
                        # p1_formatted_err "Satır X (Lexer): Hata" veya "Satır X: Hata" formatında
                        # Basit bir `in` kontrolü deneyebiliriz.
                        if p2_err_msg_from_pass_two in p1_formatted_err or \
                           p1_formatted_err in p2_err_msg_from_pass_two : # Çok kaba bir kontrol
                            is_already_in_p1_formatted_list = True
                            break
                    if not is_already_in_p1_formatted_list:
                         unique_pass2_errors.append(p2_err_msg_from_pass_two)


            if unique_pass2_errors: # Eğer gerçekten sadece Pass 2'ye özgü yeni hatalar varsa
                self.error_display.append_text("\n--- PASS 2 HATALARI ---")
                for err_msg in unique_pass2_errors:
                    self.error_display.append_text(err_msg)
            elif errs_p2_combined and not errs_p1: # Pass1'de hata yoktu ama Pass2'de var (bu durum unique_pass2_errors ile kapsanmalı)
                 self.error_display.append_text("\n--- PASS 2 HATALARI ---")
                 for err_msg in errs_p2_combined:
                     self.error_display.append_text(err_msg)


            # --- Makine Kodunu Göster ---
            mc_text = []
            if mc_segments:
                for addr, byte_codes in mc_segments:
                    hex_codes = " ".join([f"{b:02X}" for b in byte_codes])
                    mc_text.append(f"Segment @ ${addr:04X}: {hex_codes}")
            elif not (errs_p1 or unique_pass2_errors or (errs_p2_combined and not errs_p1)): # Hata yoksa ve segment yoksa
                mc_text.append("(Makine kodu üretilmedi - Muhtemelen sadece pseudo-op'lar veya boş kod.)")
            else: # Hata varsa ve segment yoksa
                mc_text.append("(Hatalar nedeniyle makine kodu üretilmedi veya boş.)")
            self.machine_code_display.set_text("\n".join(mc_text))

            # --- Durum Mesajı ve Bilgilendirme ---
            total_errors = len(errs_p1) + len(unique_pass2_errors)
            if errs_p2_combined and not errs_p1 and not unique_pass2_errors: # Sadece P2 hataları varsa ve unique boşsa, P2'nin tamamını al
                total_errors = len(errs_p2_combined)


            if total_errors == 0:
                 self._update_status("Derleme başarıyla tamamlandı.")
                 messagebox.showinfo("Başarılı", "Derleme başarıyla tamamlandı.")
            else:
                self._update_status(f"Derleme {total_errors} hata ile tamamlandı.")
                messagebox.showerror("Derleme Hatası", f"Derleme sırasında {total_errors} hata oluştu. Lütfen 'Hatalar/Uyarılar' sekmesini ve Listelemeyi kontrol edin.")

        except Exception as e:
            self.error_display.append_text(f"\nBEKLENMEDİK KRİTİK DERLEME HATASI: {e}")
            import traceback
            self.error_display.append_text(traceback.format_exc())
            messagebox.showerror("Kritik Derleme Hatası", f"Beklenmedik bir hata oluştu:\n{e}")
            self._update_status(f"Kritik derleme hatası: {e}")