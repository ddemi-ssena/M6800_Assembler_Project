# gui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import traceback # Hata ayıklama için

# --- YENİ IMPORT ---
from simulator_core.m6800_cpu import M6800CPU, CCR_CARRY, CCR_OVERFLOW, CCR_ZERO, CCR_NEGATIVE, CCR_INTERRUPT, CCR_HALF_CARRY

try:
    from assembler_core import assembler
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from assembler_core import assembler

from .widgets import CodeEditor, OutputDisplay
from .menu_bar import AppMenuBar

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("M6800 Assembler & Simulator - Tkinter") # Başlığı güncelleyebiliriz
        self.geometry("1200x700") # Simülatör paneli için biraz daha genişlik

        self.current_file_path = None

        # --- YENİ: Simülatör ile ilgili özellikler ---
        self.cpu_simulator = M6800CPU()
        self.program_loaded_in_simulator = False
        self.last_mc_segments = None # Assemble edilmiş son makine kodu
        self.last_sym_table = None   # Assemble edilmiş son sembol tablosu
        # --- YENİ SONU ---

        self._setup_ui() # Ana UI (assembler kısmı)
        self._setup_simulator_ui() # --- YENİ: Simülatör UI'ını kur ---
        
        self.menu_bar = AppMenuBar(self, self)
        self.update_simulator_display() # Başlangıçta registerları göster

    def _setup_ui(self):
        # Ana PanedWindow'ı oluşturalım, böylece simülatör panelini de ekleyebiliriz
        self.top_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.top_paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Sol Panel: Kod Editörü ve Derleme Butonu (eskisi gibi)
        left_assembler_frame = ttk.Frame(self.top_paned_window, padding=5) # Bu frame'i top_paned_window'a ekle
        self.code_editor = CodeEditor(left_assembler_frame, height=20, width=60)
        self.code_editor.pack(fill=tk.BOTH, expand=True, pady=(0,5))

        self.assemble_button = ttk.Button(left_assembler_frame, text="Assemble (F5)", command=self.run_assembly_process)
        self.assemble_button.pack(fill=tk.X, pady=(5,0))
        self.top_paned_window.add(left_assembler_frame, weight=2) # Assembler editörüne biraz daha fazla yer

        # Orta Panel: Çıktı Alanları (eskisi gibi)
        right_output_frame = ttk.Frame(self.top_paned_window, padding=5) # Bu frame'i de top_paned_window'a ekle
        notebook = ttk.Notebook(right_output_frame)

        self.listing_display = OutputDisplay(notebook, height=15, width=50)
        notebook.add(self.listing_display, text="Listeleme")

        self.symbol_table_display = OutputDisplay(notebook, height=15, width=50)
        notebook.add(self.symbol_table_display, text="Sembol Tablosu")

        self.machine_code_display = OutputDisplay(notebook, height=15, width=50)
        notebook.add(self.machine_code_display, text="Makine Kodu")

        self.error_display = OutputDisplay(notebook, height=5, width=50)
        self.error_display.configure(background="lightyellow")
        notebook.add(self.error_display, text="Hatalar/Uyarılar")

        notebook.pack(fill=tk.BOTH, expand=True)
        self.top_paned_window.add(right_output_frame, weight=3) # Çıktı alanlarına daha fazla yer

        # Durum Çubuğu (en altta kalacak)
        self.status_bar = ttk.Label(self, text="Hazır", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # --- YENİ METOT: _setup_simulator_ui ---
    def _setup_simulator_ui(self):
        sim_frame = ttk.LabelFrame(self.top_paned_window, text="CPU Simülatörü", padding=5)
        # self.top_paned_window'a ekliyoruz
        self.top_paned_window.add(sim_frame, weight=1) # Simülatöre daha az yer, ayarlanabilir

        reg_frame = ttk.Frame(sim_frame)
        reg_frame.pack(pady=5, fill=tk.X)

        ttk.Label(reg_frame, text="PC:", width=5).grid(row=0, column=0, sticky="w", padx=2)
        self.pc_var = tk.StringVar(value="$0000")
        ttk.Entry(reg_frame, textvariable=self.pc_var, state="readonly", width=7).grid(row=0, column=1, padx=2)

        ttk.Label(reg_frame, text="SP:", width=5).grid(row=1, column=0, sticky="w", padx=2)
        self.sp_var = tk.StringVar(value="$0000")
        ttk.Entry(reg_frame, textvariable=self.sp_var, state="readonly", width=7).grid(row=1, column=1, padx=2)
        
        ttk.Label(reg_frame, text="A:", width=5).grid(row=0, column=2, sticky="w", padx=(10,2))
        self.a_var = tk.StringVar(value="$00")
        ttk.Entry(reg_frame, textvariable=self.a_var, state="readonly", width=5).grid(row=0, column=3, padx=2)

        ttk.Label(reg_frame, text="B:", width=5).grid(row=1, column=2, sticky="w", padx=(10,2))
        self.b_var = tk.StringVar(value="$00")
        ttk.Entry(reg_frame, textvariable=self.b_var, state="readonly", width=5).grid(row=1, column=3, padx=2)

        ttk.Label(reg_frame, text="X:", width=5).grid(row=2, column=0, sticky="w", padx=2) # X'i A ve B'nin altına alalım
        self.x_var = tk.StringVar(value="$0000")
        ttk.Entry(reg_frame, textvariable=self.x_var, state="readonly", width=7).grid(row=2, column=1, padx=2)

        ttk.Label(reg_frame, text="CCR:", width=5).grid(row=3, column=0, sticky="w", padx=2, pady=(5,0))
        self.ccr_var = tk.StringVar(value="$C0 (------)") 
        ttk.Entry(reg_frame, textvariable=self.ccr_var, state="readonly", width=20).grid(row=3, column=1, columnspan=3, padx=2, pady=(5,0), sticky="ew")
        
        controls_frame = ttk.Frame(sim_frame)
        controls_frame.pack(pady=10, fill=tk.X)
        
        ttk.Button(controls_frame, text="Reset CPU", command=self.sim_reset).pack(side=tk.LEFT, padx=2)
        self.load_to_sim_button = ttk.Button(controls_frame, text="Load to Sim", command=self.load_program_to_simulator, state=tk.DISABLED)
        self.load_to_sim_button.pack(side=tk.LEFT, padx=2)
        self.step_button = ttk.Button(controls_frame, text="Step (F7)", command=self.sim_step, state=tk.DISABLED)
        self.step_button.pack(side=tk.LEFT, padx=2)
        # self.run_button = ttk.Button(controls_frame, text="Run (F8)", command=self.sim_run, state=tk.DISABLED)
        # self.run_button.pack(side=tk.LEFT, padx=2)

        # Klavye kısayolları (isteğe bağlı)
        self.bind_all("<F7>", lambda event: self.sim_step()) # bind_all tüm pencere için
        # self.bind_all("<F8>", lambda event: self.sim_run())
    # --- YENİ METOT SONU ---

    def _update_status(self, message):
        self.status_bar.config(text=message)

    # --- YENİ METOT: update_simulator_display ---
    def update_simulator_display(self):
        self.pc_var.set(f"${self.cpu_simulator.pc:04X}")
        self.sp_var.set(f"${self.cpu_simulator.sp:04X}")
        self.a_var.set(f"${self.cpu_simulator.acc_a:02X}")
        self.b_var.set(f"${self.cpu_simulator.acc_b:02X}")
        self.x_var.set(f"${self.cpu_simulator.ix:04X}")
        
        ccr_val = self.cpu_simulator.ccr
        h = 'H' if (ccr_val & CCR_HALF_CARRY) else '-'
        i_flag = 'I' if (ccr_val & CCR_INTERRUPT) else '-' # I bayrağı
        n = 'N' if (ccr_val & CCR_NEGATIVE) else '-'
        z = 'Z' if (ccr_val & CCR_ZERO) else '-'
        v = 'V' if (ccr_val & CCR_OVERFLOW) else '-'
        c = 'C' if (ccr_val & CCR_CARRY) else '-'
        # M6800 CCR bit sırası: X X H I N Z V C (X'ler her zaman 1)
        self.ccr_var.set(f"${ccr_val:02X} ({h}{i_flag}{n}{z}{v}{c})")
    # --- YENİ METOT SONU ---

    # --- YENİ METOT: load_program_to_simulator ---
    def load_program_to_simulator(self):
        if self.last_mc_segments: # Assemble edilmiş makine kodu varsa
            self.cpu_simulator.load_memory(self.last_mc_segments)
            
            start_address = 0xC000 # Varsayılan veya ilk segmentin adresi
            if self.last_mc_segments and self.last_mc_segments[0]:
                start_address = self.last_mc_segments[0][0]

            # END START direktifinden başlangıç adresini almayı dene
            # Bu bilgi assembler'dan (pass_one/pass_two) MainWindow'a aktarılmalı.
            # Şimdilik sembol tablosundan START'ı arayalım.
            if self.last_sym_table and self.last_sym_table.is_defined("START"):
                start_address = self.last_sym_table.get_symbol_value("START")
            
            # Reset sonrası PC, reset vektöründen ($FFFE) okunur.
            # Eğer programı belirli bir adresten başlatmak istiyorsak, PC'yi ona ayarlamalıyız.
            # Genellikle simülatör reset sonrası programı baştan başlatır.
            self.cpu_simulator.reset() # CPU'yu resetle (PC reset vektöründen okunacak)
            # Eğer reset vektörü programımızı işaret etmiyorsa, PC'yi manuel ayarla:
            if self.cpu_simulator.pc != start_address:
                 # Eğer programın başlangıç adresi sembol tablosunda START olarak tanımlıysa
                 # ve bu reset vektöründen farklıysa, PC'yi START'a ayarla.
                 # Genelde reset sonrası PC'yi kullanırız, programın ORG'u FFFE'deki adresi içermeli.
                 # Şimdilik, yüklenen programın ilk adresine PC'yi set edelim.
                 self.cpu_simulator.pc = start_address

            self.program_loaded_in_simulator = True
            self.step_button.config(state=tk.NORMAL)
            # self.run_button.config(state=tk.NORMAL) # Eğer run varsa
            self.update_simulator_display()
            self._update_status(f"Program simülatöre yüklendi. PC=${start_address:04X}")
            messagebox.showinfo("Simülatör", f"Program simülatör belleğine yüklendi.\nBaşlangıç PC: ${start_address:04X}")
        else:
            messagebox.showwarning("Simülatör", "Yüklenecek makine kodu bulunmuyor. Önce programı assemble edin.")
    # --- YENİ METOT SONU ---

    # --- YENİ METOTLAR: sim_reset, sim_step ---
    def sim_reset(self):
        self.cpu_simulator.reset()
        # Reset sonrası PC'yi başlangıç adresine ayarlama mantığı load_program_to_simulator'da
        # veya burada da tekrar edilebilir eğer program yüklüyse.
        if self.program_loaded_in_simulator and self.last_mc_segments:
            start_address = self.last_mc_segments[0][0]
            if self.last_sym_table and self.last_sym_table.is_defined("START"):
                start_address = self.last_sym_table.get_symbol_value("START")
            self.cpu_simulator.pc = start_address # Veya cpu_simulator.pc'yi reset sonrası olduğu gibi bırak
        
        self.update_simulator_display()
        self._update_status("CPU Resetlendi.")
        self.step_button.config(state=tk.NORMAL if self.program_loaded_in_simulator else tk.DISABLED)
        # self.run_button.config(state=tk.NORMAL if self.program_loaded_in_simulator else tk.DISABLED)

    def sim_step(self):
        if not self.program_loaded_in_simulator:
            messagebox.showwarning("Simülatör", "Önce programı simülatöre yükleyin.")
            return
        if self.cpu_simulator.halted:
            messagebox.showinfo("Simülatör", "CPU durdurulmuş. Resetleyin veya yeni program yükleyin.")
            self.step_button.config(state=tk.DISABLED)
            # self.run_button.config(state=tk.DISABLED)
            return
        
        try:
            success = self.cpu_simulator.step()
            self.update_simulator_display()
            if not success or self.cpu_simulator.halted:
                msg = "CPU durduruldu."
                if not success and not self.cpu_simulator.halted:
                     msg = "Simülasyon adımı başarısız oldu."
                elif self.cpu_simulator.halted:
                     msg = "CPU SWI veya bilinmeyen opcode ile durduruldu."
                
                messagebox.showinfo("Simülasyon", msg)
                self.step_button.config(state=tk.DISABLED)
                # self.run_button.config(state=tk.DISABLED)
                self._update_status(msg)
            else:
                self._update_status(f"Adım atıldı. PC=${self.cpu_simulator.pc:04X}")
        except Exception as e:
            messagebox.showerror("Simülasyon Hatası", f"Simülasyon sırasında kritik hata: {e}\n{traceback.format_exc()}")
            self.update_simulator_display()
            self._update_status(f"Simülasyon hatası: {e}")
    # --- YENİ METOTLAR SONU ---

    def new_file(self): # Bu metot aynı kalabilir
        if self._ask_save_if_needed():
            # ...
            self.load_to_sim_button.config(state=tk.DISABLED)
            self.step_button.config(state=tk.DISABLED)
            self.program_loaded_in_simulator = False


    def open_file(self): # Bu metot aynı kalabilir
        # ...
        if file_path:
            # ...
            self.load_to_sim_button.config(state=tk.DISABLED)
            self.step_button.config(state=tk.DISABLED)
            self.program_loaded_in_simulator = False

    def _ask_save_if_needed(self): # Bu metot aynı kalabilir
        # ...
        return True

    def save_file(self): # Bu metot aynı kalabilir
        # ...
        pass

    def save_file_as(self): # Bu metot aynı kalabilir
        # ...
        pass

    def run_assembly_process(self):
        self._update_status("Derleniyor...")
        self.listing_display.clear_text()
        self.symbol_table_display.clear_text()
        self.machine_code_display.clear_text()
        self.error_display.clear_text()

        # --- YENİ: Simülatör butonlarını pasif yap ---
        self.load_to_sim_button.config(state=tk.DISABLED)
        self.step_button.config(state=tk.DISABLED)
        self.program_loaded_in_simulator = False
        self.last_mc_segments = None # Önceki derleme sonuçlarını temizle
        self.last_sym_table = None
        # --- YENİ SONU ---

        source_code = self.code_editor.get_code()
        if not source_code.strip():
            messagebox.showwarning("Boş Kod", "Derlenecek kod bulunmuyor.")
            self._update_status("Derleme iptal edildi: Kod boş.")
            return

        source_lines = source_code.strip().split('\n')

        try:
            sym_table, proc_lines_p1, errs_p1 = assembler.pass_one(source_lines)

            if errs_p1:
                self.error_display.append_text("--- PASS 1 / LEXER HATALARI ---")
                for err_msg in errs_p1:
                    self.error_display.append_text(err_msg)

            final_listing, mc_segments, errs_p2_pass_two_only = assembler.pass_two(proc_lines_p1, sym_table)
            # errs_p2_pass_two_only: pass_two'nun sadece kendi içinde bulduğu YENİ hatalar olmalı.
            # Pass 1'den gelen hatalar zaten proc_lines_p1'deki entry['error']'da olmalı.

            self.symbol_table_display.set_text(str(sym_table))

            listing_text_lines = []
            for entry in final_listing:
                line = f"L:{entry['line_num']:<3} Adr:{entry['address_hex']:<6} Kod:{entry['machine_code_hex']:<10} "
                line += f"{entry['label'] or '':<8} {entry['mnemonic'] or '':<6} {entry['operand_str'] or '':<15}"
                if entry['comment']: line += f"; {entry['comment']}"
                listing_text_lines.append(line)
                if entry.get('error'): # Bu hata Lexer, Pass 1 veya Pass 2'den gelebilir
                    listing_text_lines.append(f"    HATA: {entry['error']}")
            self.listing_display.set_text("\n".join(listing_text_lines))

            # Sadece Pass 2'de yeni oluşan hataları göster
            if errs_p2_pass_two_only:
                self.error_display.append_text("\n--- PASS 2 ÖZGÜN HATALARI ---")
                for err_msg in errs_p2_pass_two_only:
                    self.error_display.append_text(err_msg)
            
            mc_text = []
            if mc_segments:
                for addr, byte_codes in mc_segments:
                    hex_codes = " ".join([f"{b:02X}" for b in byte_codes])
                    mc_text.append(f"Segment @ ${addr:04X}: {hex_codes}")
            # ... (mc_text için diğer koşullar) ...
            self.machine_code_display.set_text("\n".join(mc_text))

            total_errors = len(errs_p1) + len(errs_p2_pass_two_only)

            if total_errors == 0:
                self._update_status("Derleme başarıyla tamamlandı.")
                messagebox.showinfo("Başarılı", "Derleme başarıyla tamamlandı.")
                if mc_segments: # Sadece makine kodu üretildiyse yükleme butonunu aktif et
                    self.last_mc_segments = mc_segments
                    self.last_sym_table = sym_table
                    self.load_to_sim_button.config(state=tk.NORMAL)
            else:
                self._update_status(f"Derleme {total_errors} hata ile tamamlandı.")
                messagebox.showerror("Derleme Hatası", f"Derleme sırasında {total_errors} hata oluştu.")

        except Exception as e:
            self.error_display.append_text(f"\nBEKLENMEDİK KRİTİK DERLEME HATASI: {e}")
            self.error_display.append_text(traceback.format_exc())
            messagebox.showerror("Kritik Derleme Hatası", f"Beklenmedik bir hata oluştu:\n{e}")
            self._update_status(f"Kritik derleme hatası: {e}")