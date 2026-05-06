import tkinter as tk
import os
from tkinter import ttk, messagebox, filedialog
import re
from PIL import Image, ImageTk, ImageDraw
from vt_islemleri import KullaniciIslemleri, AbonelikIslemleri, AnalizMerkezi
from tkcalendar import DateEntry
from datetime import datetime

# ── Matplotlib için Tkinter backend ───────────────────────────
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ── win10toast (opsiyonel – kurulu değilse bildirim atlanır) ──
try:
    from win10toast import ToastNotifier
    _TOAST_AVAILABLE = True
except ImportError:
    _TOAST_AVAILABLE = False

# ─────────────────────────────────────────────────────────────
#  RENK & FONT PALETİ
# ─────────────────────────────────────────────────────────────
BG       = "#0D0F1A"
CARD     = "#151828"
CARD2    = "#1A1F35"
ACCENT   = "#4F8EF7"
ACCENT2  = "#A259FF"
TEXT     = "#E8EAF6"
MUTED    = "#6B7280"
ENTRY_BG = "#1E2235"
BORDER   = "#2A2F4A"
SUCCESS  = "#34D399"
ERROR    = "#F87171"
WARNING  = "#FBBF24"

FONT_TITLE  = ("Georgia", 26, "bold")
FONT_SUB    = ("Georgia", 11, "italic")
FONT_LABEL  = ("Helvetica", 10, "bold")
FONT_ENTRY  = ("Helvetica", 11)
FONT_BTN    = ("Helvetica", 11, "bold")
FONT_LINK   = ("Helvetica", 9, "underline")
FONT_SMALL  = ("Helvetica", 8)
FONT_H2     = ("Helvetica", 13, "bold")
FONT_H3     = ("Helvetica", 11, "bold")

KATEGORILER = ['Eğlence', 'Eğitim', 'Yazılım', 'Sağlık', 'Diğer']

KAT_RENK = {
    'Eğlence': '#F87171',
    'Eğitim':  '#34D399',
    'Yazılım': '#4F8EF7',
    'Sağlık':  '#FBBF24',
    'Diğer':   '#A259FF',
}

# Matplotlib karanlık tema ayarları
PLT_BG   = "#0D0F1A"
PLT_CARD = "#151828"
PLT_TEXT = "#E8EAF6"
PLT_MUTED= "#6B7280"


# ─────────────────────────────────────────────────────────────
#  YARDIMCI WİDGET'LAR
# ─────────────────────────────────────────────────────────────
class PlaceholderEntry(tk.Entry):
    def __init__(self, master, placeholder="", show_char="", **kw):
        super().__init__(master, **kw)
        self._ph = placeholder
        self._show = show_char
        self._showing_ph = True
        self.config(fg=MUTED, show="")
        self.insert(0, placeholder)
        self.bind("<FocusIn>",  self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _):
        if self._showing_ph:
            self.delete(0, tk.END)
            self.config(fg=TEXT, show=self._show)
            self._showing_ph = False

    def _on_focus_out(self, _):
        if not self.get():
            self.config(fg=MUTED, show="")
            self.insert(0, self._ph)
            self._showing_ph = True

    def get_value(self):
        return "" if self._showing_ph else self.get()

    def set_value(self, val):
        self._showing_ph = False
        self.config(fg=TEXT, show=self._show)
        self.delete(0, tk.END)
        self.insert(0, val)


def styled_entry(parent, placeholder, show_char=""):
    return PlaceholderEntry(
        parent, placeholder=placeholder, show_char=show_char,
        bg=ENTRY_BG, fg=MUTED, insertbackground=ACCENT,
        relief="flat", font=FONT_ENTRY,
        highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
    )


def styled_button(parent, text, command, color=ACCENT, width=22, pady=8):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg="#FFFFFF", activebackground=ACCENT2,
        activeforeground="#FFFFFF", relief="flat",
        font=FONT_BTN, cursor="hand2", width=width, pady=pady,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT2))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def divider(parent):
    f = tk.Frame(parent, bg=CARD)
    tk.Frame(f, bg=BORDER, height=1, width=100).pack(side="left", padx=4, pady=8)
    tk.Label(f, text="veya", bg=CARD, fg=MUTED, font=FONT_SMALL).pack(side="left")
    tk.Frame(f, bg=BORDER, height=1, width=100).pack(side="left", padx=4, pady=8)
    return f


def section_line(parent, bg=BG):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=8)


def draw_logo(parent, bg_color, size=56):
    c = tk.Canvas(parent, width=size, height=size, bg=bg_color, highlightthickness=0)
    c.pack()
    c.create_oval(2, 2, size-2, size-2, fill=ACCENT2, outline="")
    m = size * 0.18
    c.create_oval(m, m, size-m, size-m, fill=ACCENT, outline="")
    c.create_text(size/2, size/2, text="₺", fill="#FFFFFF",
                  font=("Helvetica", max(10, size//3), "bold"))


# ── Scrollable Frame ──────────────────────────────────────────
class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=BG, **kw):
        super().__init__(parent, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical",
                                      command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(
                            scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<MouseWheel>",
                         lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))


# ─────────────────────────────────────────────────────────────
#  ANA UYGULAMA
# ─────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SubTrack – Abonelik Yöneticisi")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.kullanici_motoru  = KullaniciIslemleri()
        self.abonelik_motoru   = AbonelikIslemleri()
        self.analiz_motoru     = AnalizMerkezi()

        self.current_user_id   = None
        self.current_username  = None

        self._show_login()

    def _center(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _get_profile_image(self, size=(60, 60)):
        profil_yol = None
        if self.current_user_id is not None:
            bas, veri = self.kullanici_motoru.profil_bilgisi_getir(self.current_user_id)
            if bas and isinstance(veri, dict):
                profil_yol = veri.get('profil_foto')

        aranan_yollar = [profil_yol, 'default_avatar.png'] if profil_yol else ['default_avatar.png']
        image_obj = None
        for yol in aranan_yollar:
            if not yol:
                continue
            try:
                image_obj = Image.open(yol).convert('RGBA')
                break
            except Exception:
                image_obj = None

        if image_obj is None:
            image_obj = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image_obj)
            draw.ellipse((0, 0, size[0]-1, size[1]-1), fill=(148, 163, 184, 255))
        else:
            image_obj = image_obj.resize(size, Image.LANCZOS)

        return ImageTk.PhotoImage(image_obj)

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ════════════════════════════════════════════════════════════
    # GİRİŞ EKRANI
    # ════════════════════════════════════════════════════════════
    def _show_login(self):
        self._clear()
        self._center(500, 600)

        root = tk.Frame(self, bg=BG)
        root.pack(expand=True, fill="both", padx=40, pady=30)

        lf = tk.Frame(root, bg=BG)
        lf.pack(pady=(10, 0))
        draw_logo(lf, BG)

        tk.Label(root, text="SubTrack", bg=BG, fg=TEXT,
                 font=FONT_TITLE).pack(pady=(8, 0))
        tk.Label(root, text="Aboneliklerini akıllıca yönet", bg=BG,
                 fg=MUTED, font=FONT_SUB).pack(pady=(2, 20))

        card = tk.Frame(root, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", pady=4, ipady=10)

        tk.Label(card, text="Hesabına Giriş Yap", bg=CARD, fg=TEXT,
                 font=FONT_H2).pack(pady=(18, 12))

        tk.Label(card, text="KULLANICI ADI", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.login_email = styled_entry(card, "Kullanıcı adını gir")
        self.login_email.pack(padx=30, pady=(2, 10), ipady=6, fill="x")

        tk.Label(card, text="ŞİFRE", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.login_pw = styled_entry(card, "••••••••", show_char="•")
        self.login_pw.pack(padx=30, pady=(2, 6), ipady=6, fill="x")

        self.login_msg = tk.Label(card, text="", bg=CARD, fg=ERROR,
                                  font=FONT_SMALL)
        self.login_msg.pack()

        styled_button(card, "  Giriş Yap  ", self._do_login).pack(pady=10)
        divider(card).pack()

        bot = tk.Frame(card, bg=CARD)
        bot.pack(pady=(4, 16))
        tk.Label(bot, text="Hesabın yok mu?", bg=CARD, fg=MUTED,
                 font=FONT_SMALL).pack(side="left")
        lnk = tk.Label(bot, text=" Üye Ol", bg=CARD, fg=ACCENT,
                        font=FONT_LINK, cursor="hand2")
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda e: self._show_register())

        tk.Label(root, text="v2.0  •  Veriler SHA-256 ile korunur",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(pady=(12, 0))

    # ════════════════════════════════════════════════════════════
    # KAYIT EKRANI
    # ════════════════════════════════════════════════════════════
    def _show_register(self):
        self._clear()
        self._center(500, 640)

        root = tk.Frame(self, bg=BG)
        root.pack(expand=True, fill="both", padx=40, pady=20)

        lf = tk.Frame(root, bg=BG)
        lf.pack()
        draw_logo(lf, BG, size=44)

        tk.Label(root, text="SubTrack", bg=BG, fg=TEXT,
                 font=("Georgia", 20, "bold")).pack(pady=(6, 0))
        tk.Label(root, text="Yeni hesap oluştur", bg=BG,
                 fg=MUTED, font=FONT_SUB).pack(pady=(2, 14))

        card = tk.Frame(root, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", pady=4, ipady=10)

        tk.Label(card, text="Üye Ol", bg=CARD, fg=TEXT,
                 font=FONT_H2).pack(pady=(18, 12))

        tk.Label(card, text="KULLANICI ADI", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.reg_name = styled_entry(card, "En az 3 karakter")
        self.reg_name.pack(padx=30, pady=(2, 10), ipady=6, fill="x")

        tk.Label(card, text="ŞİFRE", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.reg_pw = styled_entry(card, "En az 6 karakter", show_char="•")
        self.reg_pw.pack(padx=30, pady=(2, 10), ipady=6, fill="x")

        tk.Label(card, text="ŞİFRE TEKRAR", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.reg_pw2 = styled_entry(card, "Şifreni tekrar gir", show_char="•")
        self.reg_pw2.pack(padx=30, pady=(2, 6), ipady=6, fill="x")

        self.reg_msg = tk.Label(card, text="", bg=CARD, fg=ERROR,
                                font=FONT_SMALL, wraplength=340)
        self.reg_msg.pack()

        styled_button(card, "  Hesap Oluştur  ", self._do_register,
                      color=SUCCESS).pack(pady=10)
        divider(card).pack()

        bot = tk.Frame(card, bg=CARD)
        bot.pack(pady=(4, 16))
        tk.Label(bot, text="Zaten hesabın var mı?", bg=CARD, fg=MUTED,
                 font=FONT_SMALL).pack(side="left")
        lnk = tk.Label(bot, text=" Giriş Yap", bg=CARD, fg=ACCENT,
                        font=FONT_LINK, cursor="hand2")
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda e: self._show_login())

    # ════════════════════════════════════════════════════════════
    # DASHBOARD
    # ════════════════════════════════════════════════════════════
    def _show_dashboard(self, name=None):
        if name:
            self.current_username = name
        self._clear()
        self._center(960, 680)

        # ── Sol kenar çubuğu ──────────────────────────────────
        sidebar = tk.Frame(self, bg=CARD, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        lf = tk.Frame(sidebar, bg=CARD)
        lf.pack(pady=(28, 4))
        profile_img = self._get_profile_image(size=(44, 44))
        profile_label = tk.Label(lf, image=profile_img, bg=CARD)
        profile_label.image = profile_img
        profile_label.pack()
        tk.Label(sidebar, text="SubTrack", bg=CARD, fg=TEXT,
                 font=("Georgia", 14, "bold")).pack()
        tk.Label(sidebar, text=f"@{self.current_username}", bg=CARD,
                 fg=MUTED, font=FONT_SMALL).pack(pady=(2, 20))

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=4)

        nav_items = [
            ("🏠  Genel Bakış",     self._tab_genel),
            ("➕  Abonelik Ekle",   self._tab_ekle),
            ("👤  Profilim",        self._tab_profil),
            ("📋  Aboneliklerim",   self._tab_liste),
            ("📊  Grafikler",       self._tab_grafikler),
            ("🔮  Projeksiyon",     self._tab_projeksiyon),
        ]
        self.nav_btns = []
        for label, cmd in nav_items:
            b = tk.Button(sidebar, text=label, command=cmd,
                          bg=CARD, fg=TEXT, activebackground=ENTRY_BG,
                          activeforeground=ACCENT, relief="flat",
                          font=FONT_H3, cursor="hand2", anchor="w",
                          padx=18, pady=10, width=20)
            b.bind("<Enter>", lambda e, btn=b: btn.config(bg=ENTRY_BG, fg=ACCENT))
            b.bind("<Leave>", lambda e, btn=b: btn.config(
                bg=ACCENT if btn.cget("fg") == "#FFFFFF" else CARD,
                fg=TEXT if btn.cget("fg") != "#FFFFFF" else "#FFFFFF"))
            b.pack(fill="x")
            self.nav_btns.append(b)

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=16)

        styled_button(sidebar, "⬅  Çıkış Yap", self._show_login,
                      color=MUTED, width=18, pady=6).pack(padx=16)

        # ── Ana içerik alanı ──────────────────────────────────
        self.main_area = tk.Frame(self, bg=BG)
        self.main_area.pack(side="left", fill="both", expand=True)

        self._tab_genel()

        # ── Uygulama açılışında bildirim gönder ──────────────
        self.after(1500, self._bildirim_gonder)

    def _set_active_nav(self, index):
        for i, b in enumerate(self.nav_btns):
            if i == index:
                b.config(bg=ACCENT, fg="#FFFFFF")
                b.unbind("<Enter>")
                b.unbind("<Leave>")
            else:
                b.config(bg=CARD, fg=TEXT)
                b.bind("<Enter>", lambda e, btn=b: btn.config(bg=ENTRY_BG, fg=ACCENT))
                b.bind("<Leave>", lambda e, btn=b: btn.config(bg=CARD, fg=TEXT))

    def _clear_main(self):
        for w in self.main_area.winfo_children():
            w.destroy()

    # ════════════════════════════════════════════════════════════
    # BİLDİRİM SİSTEMİ (win10toast)
    # ════════════════════════════════════════════════════════════
    def _bildirim_gonder(self):
        """
        Uygulama açıldığında yarın ödeme tarihi olan abonelikleri kontrol eder.
        win10toast kuruluysa Windows bildirimi, değilse uygulama içi uyarı gösterir.
        """
        bas, odemeler = self.abonelik_motoru.yarin_odemeleri_bul(self.current_user_id)
        if not bas or not odemeler:
            return

        mesaj_listesi = "\n".join(
            f"• {o['servis_adi']}  ₺{o['tutar']:,.2f}" for o in odemeler
        )

        if _TOAST_AVAILABLE:
            try:
                toaster = ToastNotifier()
                baslik = f"SubTrack – {len(odemeler)} Ödeme Yarın!"
                mesaj = f"Yarın ödenecek abonelikler:\n{mesaj_listesi}"
                # threaded=True: UI'yi bloke etmez
                toaster.show_toast(baslik, mesaj, duration=8, threaded=True)
            except Exception:
                # Bildirim gönderilemezse sessizce geç
                pass
        else:
            # Fallback: Uygulama içi popup
            isimler = ", ".join(o['servis_adi'] for o in odemeler)
            messagebox.showwarning(
                "⏰ Yaklaşan Ödeme Hatırlatıcısı",
                f"Yarın ödeme tarihi olan abonelikleriniz:\n\n{mesaj_listesi}\n\n"
                f"(Windows bildirimleri için: pip install win10toast)"
            )

    # ════════════════════════════════════════════════════════════
    # TAB: GENEL BAKIŞ
    # ════════════════════════════════════════════════════════════
    def _tab_genel(self):
        self._clear_main()
        self._set_active_nav(0)

        sf = ScrollFrame(self.main_area)
        sf.pack(fill="both", expand=True)
        inner = sf.inner
        inner.config(padx=24, pady=20)

        tk.Label(inner, text="Genel Bakış", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w")
        tk.Label(inner, text="Abonelik durumuna hızlı göz at",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 16))

        # ── Backend çağrıları ──
        bas1, toplam = self.abonelik_motoru.toplam_maliyet_hesapla(self.current_user_id)
        bas2, liste  = self.abonelik_motoru.listele_hepsi(self.current_user_id)
        bas3, yaklas = self.abonelik_motoru.yaklasan_odemeler(self.current_user_id, limit=3)
        bas4, katlar = self.analiz_motoru.kategori_ozeti_getir(self.current_user_id)
        bas5, butce  = self.analiz_motoru.butce_durumu_getir(self.current_user_id)

        toplam = toplam if bas1 else 0.0
        liste  = liste  if bas2 else []
        yaklas = yaklas if bas3 else []
        katlar = katlar if bas4 else []
        butce  = butce  if bas5 else {'toplam_harcama': 0.0, 'butce_hedefi': 2000.0, 'butce_orani': 0.0}

        # ── Özet kartları ──
        kart_satir = tk.Frame(inner, bg=BG)
        kart_satir.pack(fill="x", pady=(0, 16))

        self._ozet_kart(kart_satir, "💳  Toplam Aylık",   f"₺{toplam:,.2f}", ACCENT)
        self._ozet_kart(kart_satir, "📦  Aktif Abonelik", str(len(liste)),    ACCENT2)
        ortalama = (toplam / len(liste)) if liste else 0
        self._ozet_kart(kart_satir, "📈  Ortalama",       f"₺{ortalama:,.2f}", SUCCESS)

        # ── Dinamik Bütçe Çubuğu ──
        self._butce_takip_cubugu(inner, butce)

        # ── İptal Önerisi ──
        self._iptal_onerisi_goster(inner)

        # ── Yaklaşan ödemeler ──
        tk.Label(inner, text="⏰  Yaklaşan Ödemeler", bg=BG, fg=TEXT,
                 font=FONT_H3).pack(anchor="w", pady=(16, 6))

        if yaklas:
            for item in yaklas:
                self._yaklashan_satir(inner, item)
        else:
            tk.Label(inner, text="Yaklaşan ödeme bulunmuyor.",
                     bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=4)

        section_line(inner)

        # ── Kategori dağılımı (mini bar chart) ──
        tk.Label(inner, text="📂  Kategori Dağılımı", bg=BG, fg=TEXT,
                 font=FONT_H3).pack(anchor="w", pady=(0, 8))

        if katlar:
            maks = max(k['toplam_tutar'] for k in katlar) or 1
            for k in katlar:
                self._kategori_bar(inner, k, maks)
        else:
            tk.Label(inner, text="Henüz veri yok.",
                     bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", padx=4)

    def _ozet_kart(self, parent, baslik, deger, renk):
        card = tk.Frame(parent, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(side="left", expand=True, fill="x", padx=6, ipadx=10, ipady=12)
        tk.Label(card, text=baslik, bg=CARD, fg=MUTED,
                 font=FONT_SMALL).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(card, text=deger, bg=CARD, fg=renk,
                 font=("Helvetica", 18, "bold")).pack(anchor="w", padx=12, pady=(0, 10))

    def _yaklashan_satir(self, parent, item):
        row = tk.Frame(parent, bg=CARD2, highlightthickness=1,
                       highlightbackground=BORDER)
        row.pack(fill="x", pady=3, ipady=6)

        renk = KAT_RENK.get(item['kategori'], MUTED)
        tk.Frame(row, bg=renk, width=4).pack(side="left", fill="y")

        tk.Label(row, text=item['servis_adi'], bg=CARD2, fg=TEXT,
                 font=FONT_H3).pack(side="left", padx=12)
        tk.Label(row, text=item['odeme_tarihi'], bg=CARD2, fg=MUTED,
                 font=FONT_SMALL).pack(side="left")
        tk.Label(row, text=f"₺{item['tutar']:,.2f}", bg=CARD2,
                 fg=WARNING, font=FONT_H3).pack(side="right", padx=14)

    def _kategori_bar(self, parent, k, maks):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=3)

        renk = KAT_RENK.get(k['kategori'], MUTED)
        tk.Label(row, text=k['kategori'], bg=BG, fg=TEXT,
                 font=FONT_SMALL, width=10, anchor="w").pack(side="left")

        bar_frame = tk.Frame(row, bg=ENTRY_BG, height=14, width=320)
        bar_frame.pack(side="left", padx=8)
        bar_frame.pack_propagate(False)

        oran = k['toplam_tutar'] / maks
        dolu = tk.Frame(bar_frame, bg=renk, height=14,
                        width=int(320 * oran))
        dolu.pack(side="left", fill="y")

        tk.Label(row, text=f"₺{k['toplam_tutar']:,.2f}", bg=BG,
                 fg=renk, font=FONT_SMALL).pack(side="left", padx=6)

    # ── Dinamik Bütçe Çubuğu (Yeşil→Sarı→Kırmızı) ───────────
    def _butce_takip_cubugu(self, parent, butce):
        """
        Harcama oranına göre renk değiştiren dinamik bütçe çubuğu.
        %0-69: Yeşil | %70-89: Sarı | %90+: Kırmızı
        Bütçe aşıldıysa negatif farkı ve uyarı mesajını gösterir.
        """
        harcama = butce.get('toplam_harcama', 0.0)
        hedef   = butce.get('butce_hedefi', 2000.0)
        oran    = butce.get('butce_orani', 0.0)
        fark    = hedef - harcama

        # Renk seçimi
        if oran < 70:
            bar_renk = SUCCESS
            durum_ikon = "✅"
        elif oran < 90:
            bar_renk = WARNING
            durum_ikon = "⚠️"
        else:
            bar_renk = ERROR
            durum_ikon = "🚨"

        container = tk.Frame(parent, bg=BG)
        container.pack(fill="x", pady=(16, 0))

        # Başlık satırı
        baslik_row = tk.Frame(container, bg=BG)
        baslik_row.pack(fill="x")
        tk.Label(baslik_row, text=f"{durum_ikon}  Bütçe İzleme", bg=BG, fg=TEXT,
                 font=FONT_H3).pack(side="left")

        # Bütçe güncelle butonu
        guncelle_btn = tk.Label(
            baslik_row, text="✏️ Bütçeyi Güncelle", bg=BG, fg=ACCENT,
            font=FONT_LINK, cursor="hand2"
        )
        guncelle_btn.pack(side="right")
        guncelle_btn.bind("<Button-1>", lambda e: self._butce_guncelle_modal())

        # Progress bar gövdesi
        bar_frame = tk.Frame(container, bg=ENTRY_BG, height=28)
        bar_frame.pack(fill="x", pady=(8, 4))
        bar_frame.pack_propagate(False)

        if hedef > 0:
            dolu_yuzde = min(oran, 100.0)
            dolu_frame = tk.Frame(bar_frame, bg=bar_renk, height=28)
            dolu_frame.place(relwidth=dolu_yuzde / 100.0, relheight=1)

        # İçerik etiketi (progress bar üstünde)
        bar_lbl = tk.Label(
            bar_frame,
            text=f"₺{harcama:,.2f} / ₺{hedef:,.2f}  ({oran:.1f}%)",
            bg=ENTRY_BG, fg=TEXT, font=FONT_H3, anchor="center"
        )
        bar_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Alt bilgi satırı
        if fark >= 0:
            bilgi_text = f"Bütçenizden ₺{fark:,.2f} kaldı."
            bilgi_renk = bar_renk
        else:
            bilgi_text = f"⚠️ Bütçenizi ₺{abs(fark):,.2f} aştınız!"
            bilgi_renk = ERROR

        tk.Label(container, text=bilgi_text, bg=BG, fg=bilgi_renk,
                 font=FONT_SMALL).pack(anchor="w", pady=(2, 0))

    # ── İptal Önerisi Kartı ───────────────────────────────────
    def _iptal_onerisi_goster(self, parent):
        """Bütçe aşıldıysa kullanıcıya akıllı iptal önerisi gösterir."""
        bas, oneri = self.analiz_motoru.iptal_onerisi_getir(self.current_user_id)
        if not bas or not oneri.get('oneri_var'):
            return

        oneri_kart = tk.Frame(parent, bg="#2A1A1A", highlightthickness=1,
                              highlightbackground=ERROR)
        oneri_kart.pack(fill="x", pady=(12, 0))

        baslik = tk.Frame(oneri_kart, bg="#2A1A1A")
        baslik.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(baslik, text="💡 Akıllı Öneri", bg="#2A1A1A", fg=ERROR,
                 font=FONT_H3).pack(side="left")

        tk.Label(oneri_kart, text=oneri['sebep'], bg="#2A1A1A", fg=TEXT,
                 font=FONT_SMALL, wraplength=680, justify="left").pack(
                 anchor="w", padx=14, pady=(0, 10))

    # ════════════════════════════════════════════════════════════
    # TAB: ABONELİK EKLE
    # ════════════════════════════════════════════════════════════
    def _tab_ekle(self):
        self._clear_main()
        self._set_active_nav(1)

        outer = tk.Frame(self.main_area, bg=BG)
        outer.pack(fill="both", expand=True, padx=30, pady=24)

        tk.Label(outer, text="Yeni Abonelik Ekle", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w")
        tk.Label(outer, text="Abonelik bilgilerini doldur ve kaydet",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 16))

        card = tk.Frame(outer, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", ipady=10)

        tk.Label(card, text="SERVİS ADI", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=24, pady=(18, 0))
        self.yeni_servis = styled_entry(card, "Netflix, Spotify, Gym...")
        self.yeni_servis.pack(padx=24, pady=(4, 12), ipady=6, fill="x")

        tk.Label(card, text="TUTAR (₺)", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=24)
        self.yeni_tutar = styled_entry(card, "0.00")
        self.yeni_tutar.pack(padx=24, pady=(4, 12), ipady=6, fill="x")

        tk.Label(card, text="ÖDEME TARİHİ", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=24)
        self.yeni_tarih = DateEntry(card,
                                    background=ACCENT, foreground=TEXT,
                                    bordercolor=BORDER, date_pattern='y-mm-dd',
                                    font=FONT_ENTRY, width=18)
        self.yeni_tarih.pack(padx=24, pady=(4, 12), ipady=6, fill="x")

        tk.Label(card, text="KATEGORİ", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=24)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                        fieldbackground=ENTRY_BG, background=ENTRY_BG,
                        foreground=TEXT, selectbackground=ACCENT,
                        bordercolor=BORDER, arrowcolor=ACCENT, relief="flat")

        self.yeni_kat = ttk.Combobox(card, values=KATEGORILER,
                                     style="Dark.TCombobox",
                                     font=FONT_ENTRY, state="readonly")
        self.yeni_kat.set("Eğlence")
        self.yeni_kat.pack(padx=24, pady=(4, 6), ipady=4, fill="x")

        self.ekle_msg = tk.Label(card, text="", bg=CARD, fg=ERROR, font=FONT_SMALL)
        self.ekle_msg.pack(pady=(4, 0))

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(pady=14)
        styled_button(btn_row, "  Kaydet  ", self._save_new_subscription,
                      color=SUCCESS, width=16).pack(side="left", padx=6)
        styled_button(btn_row, "  Temizle  ", self._temizle_form,
                      color=MUTED, width=12).pack(side="left", padx=6)

    def _temizle_form(self):
        for e in [self.yeni_servis, self.yeni_tutar]:
            e._showing_ph = False
            e.delete(0, tk.END)
            e._on_focus_out(None)
        self.yeni_tarih.set_date(datetime.now())
        self.yeni_kat.set("Eğlence")
        self.ekle_msg.config(text="")

    # ════════════════════════════════════════════════════════════
    # TAB: PROFİLİM
    # ════════════════════════════════════════════════════════════
    def _tab_profil(self):
        self._clear_main()
        self._set_active_nav(2)

        outer = tk.Frame(self.main_area, bg=BG)
        outer.pack(fill="both", expand=True, padx=30, pady=24)

        tk.Label(outer, text="Profilim", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w")
        tk.Label(outer, text="Kişisel hesabını ve profil fotoğrafını yönet.",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 16))

        card = tk.Frame(outer, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", ipady=24)

        img = self._get_profile_image(size=(120, 120))
        foto_frame = tk.Frame(card, bg=CARD)
        foto_frame.pack(pady=(12, 10))
        foto_label = tk.Label(foto_frame, image=img, bg=CARD)
        foto_label.image = img
        foto_label.pack()

        tk.Label(card, text=f"@{self.current_username}".upper(), bg=CARD,
                 fg=TEXT, font=("Helvetica", 16, "bold")).pack(pady=(10, 4))

        styled_button(card, "Fotoğrafı Değiştir", self._change_profile_photo,
                      color=ACCENT, width=18, pady=10).pack(pady=(8, 16))

    # ════════════════════════════════════════════════════════════
    # TAB: ABONELİKLERİM (Düzenleme özelliğiyle)
    # ════════════════════════════════════════════════════════════
    def _tab_liste(self):
        self._clear_main()
        self._set_active_nav(3)

        outer = tk.Frame(self.main_area, bg=BG)
        outer.pack(fill="both", expand=True, padx=30, pady=24)

        tk.Label(outer, text="Aboneliklerim", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w")
        tk.Label(outer, text="Kayıtlı tüm abonelikler – düzenlemek için satıra tıklayın",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 14))

        bas, liste = self.abonelik_motoru.listele_hepsi(self.current_user_id)
        liste = liste if bas else []

        if not liste:
            tk.Label(outer, text="Henüz abonelik eklenmemiş.",
                     bg=BG, fg=MUTED, font=FONT_ENTRY).pack(pady=40)
            styled_button(outer, "➕  İlk Aboneliği Ekle",
                          self._tab_ekle, width=24).pack()
            return

        # Başlık satırı
        header = tk.Frame(outer, bg=CARD)
        header.pack(fill="x", pady=(0, 4))
        for col, w in [("Servis", 16), ("Tutar", 10),
                        ("Tarih", 12), ("Kategori", 12), ("", 10)]:
            tk.Label(header, text=col, bg=CARD, fg=MUTED,
                     font=FONT_LABEL, width=w, anchor="w").pack(side="left", padx=6, pady=6)

        sf = ScrollFrame(outer)
        sf.pack(fill="both", expand=True)
        inner = sf.inner

        for item in liste:
            self._liste_satiri(inner, item)

    def _liste_satiri(self, parent, item):
        renk = KAT_RENK.get(item['kategori'], MUTED)
        row = tk.Frame(parent, bg=CARD2, highlightthickness=1,
                       highlightbackground=BORDER, cursor="hand2")
        row.pack(fill="x", pady=2)

        tk.Frame(row, bg=renk, width=4).pack(side="left", fill="y")

        tk.Label(row, text=item['servis_adi'], bg=CARD2, fg=TEXT,
                 font=FONT_H3, width=15, anchor="w").pack(side="left", padx=8, pady=8)
        tk.Label(row, text=f"₺{item['tutar']:,.2f}", bg=CARD2, fg=SUCCESS,
                 font=FONT_ENTRY, width=9, anchor="w").pack(side="left", padx=4)
        tk.Label(row, text=item['odeme_tarihi'], bg=CARD2, fg=MUTED,
                 font=FONT_SMALL, width=11, anchor="w").pack(side="left", padx=4)
        tk.Label(row, text=item['kategori'], bg=CARD2, fg=renk,
                 font=FONT_SMALL, width=11, anchor="w").pack(side="left", padx=4)

        # ── Düzenle butonu ──
        duz_btn = tk.Button(row, text="✏️", bg=CARD2, fg=ACCENT,
                             activebackground=ACCENT, activeforeground="#FFF",
                             relief="flat", cursor="hand2", font=FONT_H3,
                             command=lambda i=item: self._duzenle_modal(i))
        duz_btn.pack(side="right", padx=4)

        sil_btn = tk.Button(row, text="🗑", bg=CARD2, fg=ERROR,
                             activebackground=ERROR, activeforeground="#FFF",
                             relief="flat", cursor="hand2", font=FONT_H3,
                             command=lambda aid=item['id']: self._sil_onayla(aid))
        sil_btn.pack(side="right", padx=6)

        # Satıra tıklayarak da düzenleme açılır
        row.bind("<Button-1>", lambda e, i=item: self._duzenle_modal(i))

    # ════════════════════════════════════════════════════════════
    # MODAL: ABONELİK DÜZENLE
    # ════════════════════════════════════════════════════════════
    def _duzenle_modal(self, item: dict):
        """
        Seçili abonelik için düzenleme modalı açar.
        Tutar ve ödeme tarihi güncellenebilir.
        """
        modal = tk.Toplevel(self)
        modal.title(f"Düzenle – {item['servis_adi']}")
        modal.configure(bg=BG)
        modal.resizable(False, False)
        modal.grab_set()  # Modal davranışı

        # Pencereyi ortala
        modal.update_idletasks()
        pw, ph = 440, 440
        sw, sh = modal.winfo_screenwidth(), modal.winfo_screenheight()
        modal.geometry(f"{pw}x{ph}+{(sw-pw)//2}+{(sh-ph)//2}")

        outer = tk.Frame(modal, bg=BG)
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        # Başlık
        tk.Label(outer, text=f"✏️  {item['servis_adi']}", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w")
        tk.Label(outer, text="Abonelik bilgilerini güncelleyin",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 16))

        card = tk.Frame(outer, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", ipady=8)

        # Servis adı (salt okunur – sadece görünüm için)
        tk.Label(card, text="SERVİS ADI", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=20, pady=(14, 0))
        servis_ent = styled_entry(card, "")
        servis_ent.set_value(item['servis_adi'])
        servis_ent.pack(padx=20, pady=(4, 10), ipady=6, fill="x")

        # Tutar
        tk.Label(card, text="YENİ TUTAR (₺)", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=20)
        tutar_ent = styled_entry(card, "0.00")
        tutar_ent.set_value(str(item['tutar']))
        tutar_ent.pack(padx=20, pady=(4, 10), ipady=6, fill="x")

        # Tarih
        tk.Label(card, text="YENİ ÖDEME TARİHİ", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=20)
        tarih_pick = DateEntry(card,
                               background=ACCENT, foreground=TEXT,
                               bordercolor=BORDER, date_pattern='y-mm-dd',
                               font=FONT_ENTRY, width=18)
        try:
            tarih_pick.set_date(datetime.strptime(item['odeme_tarihi'], '%Y-%m-%d'))
        except Exception:
            pass
        tarih_pick.pack(padx=20, pady=(4, 10), ipady=6, fill="x")

        # Kategori
        tk.Label(card, text="KATEGORİ", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=20)
        kat_cb = ttk.Combobox(card, values=KATEGORILER,
                              style="Dark.TCombobox",
                              font=FONT_ENTRY, state="readonly")
        kat_cb.set(item['kategori'])
        kat_cb.pack(padx=20, pady=(4, 6), ipady=4, fill="x")

        # Mesaj etiketi
        msg_lbl = tk.Label(card, text="", bg=CARD, fg=ERROR, font=FONT_SMALL)
        msg_lbl.pack()

        def _kaydet():
            servis = servis_ent.get_value().strip()
            tutar_str = tutar_ent.get_value().strip()
            kat = kat_cb.get()

            if not servis or not tutar_str:
                msg_lbl.config(text="Tüm alanları doldurun.", fg=ERROR)
                return
            try:
                tutar = float(tutar_str)
                if tutar <= 0:
                    raise ValueError
            except ValueError:
                msg_lbl.config(text="Geçerli bir tutar girin.", fg=ERROR)
                return

            try:
                tarih = tarih_pick.get_date().strftime('%Y-%m-%d')
            except Exception:
                msg_lbl.config(text="Geçerli bir tarih seçin.", fg=ERROR)
                return

            bas, mesaj = self.abonelik_motoru.guncelle(
                item['id'], servis, tutar, tarih, kat
            )
            if bas:
                modal.destroy()
                self._tab_liste()
            else:
                msg_lbl.config(text=mesaj, fg=ERROR)

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(pady=12, fill="x")
        styled_button(btn_row, "  Kaydet  ", _kaydet,
                      color=SUCCESS, width=14).pack(side="left", padx=4)
        styled_button(btn_row, "  İptal  ", modal.destroy,
                      color=MUTED, width=10).pack(side="left", padx=4)

    # ════════════════════════════════════════════════════════════
    # MODAL: BÜTÇE GÜNCELLE
    # ════════════════════════════════════════════════════════════
    def _butce_guncelle_modal(self):
        """Kullanıcının aylık bütçe hedefini güncellemesini sağlar."""
        modal = tk.Toplevel(self)
        modal.title("Bütçe Hedefini Güncelle")
        modal.configure(bg=BG)
        modal.resizable(False, False)
        modal.grab_set()

        modal.update_idletasks()
        pw, ph = 380, 260
        sw, sh = modal.winfo_screenwidth(), modal.winfo_screenheight()
        modal.geometry(f"{pw}x{ph}+{(sw-pw)//2}+{(sh-ph)//2}")

        outer = tk.Frame(modal, bg=BG)
        outer.pack(fill="both", expand=True, padx=24, pady=20)

        tk.Label(outer, text="💰 Bütçe Hedefini Belirle", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w")
        tk.Label(outer, text="Aylık maksimum abonelik harcamanızı girin",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 14))

        card = tk.Frame(outer, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", ipady=8)

        tk.Label(card, text="YENİ BÜTÇE LİMİTİ (₺)", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=20, pady=(14, 0))

        # Mevcut bütçeyi göster
        bas, mevcut = self.kullanici_motoru.butce_getir(self.current_user_id)
        butce_ent = styled_entry(card, "2000.00")
        if bas:
            butce_ent.set_value(str(mevcut))
        butce_ent.pack(padx=20, pady=(4, 10), ipady=6, fill="x")

        msg_lbl = tk.Label(card, text="", bg=CARD, fg=ERROR, font=FONT_SMALL)
        msg_lbl.pack()

        def _kaydet():
            val = butce_ent.get_value().strip()
            try:
                limit = float(val)
                if limit < 0:
                    raise ValueError
            except ValueError:
                msg_lbl.config(text="Geçerli bir tutar girin (örn: 3000)", fg=ERROR)
                return

            bas2, mesaj2 = self.kullanici_motoru.butce_guncelle(self.current_user_id, limit)
            if bas2:
                modal.destroy()
                self._tab_genel()
            else:
                msg_lbl.config(text=mesaj2, fg=ERROR)

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(pady=10, fill="x")
        styled_button(btn_row, "  Kaydet  ", _kaydet,
                      color=SUCCESS, width=14).pack(side="left", padx=4)
        styled_button(btn_row, "  İptal  ", modal.destroy,
                      color=MUTED, width=10).pack(side="left", padx=4)

    # ════════════════════════════════════════════════════════════
    # TAB: GRAFİKLER (Matplotlib)
    # ════════════════════════════════════════════════════════════
    def _tab_grafikler(self):
        """
        İki grafik gösterir:
          1. Kategori Dağılımı – Pasta Grafiği (Pie Chart)
          2. Aylık Harcama Trendi – Çizgi Grafiği (Line Chart)
             (Mevcut aboneliklerin son 6 ay simülasyonu)
        """
        self._clear_main()
        self._set_active_nav(4)

        outer = tk.Frame(self.main_area, bg=BG)
        outer.pack(fill="both", expand=True, padx=20, pady=16)

        tk.Label(outer, text="📊 Grafiksel Analiz", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w")
        tk.Label(outer, text="Harcamalarını görselleştir",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 14))

        # Verileri çek
        bas1, dagilim = self.abonelik_motoru.kategori_bazli_dagilim(self.current_user_id)
        bas2, liste   = self.abonelik_motoru.listele_hepsi(self.current_user_id)

        if not bas1 or not dagilim:
            tk.Label(outer, text="Grafik için yeterli veri yok. Önce abonelik ekleyin.",
                     bg=BG, fg=MUTED, font=FONT_ENTRY).pack(pady=60)
            return

        # ── Figure oluştur ──────────────────────────────────────
        fig = Figure(figsize=(9, 5), facecolor=PLT_BG)
        fig.subplots_adjust(wspace=0.4, left=0.08, right=0.95)

        # ── 1. Pasta Grafiği ────────────────────────────────────
        ax1 = fig.add_subplot(121)
        ax1.set_facecolor(PLT_CARD)

        etiketler = list(dagilim.keys())
        degerler  = list(dagilim.values())
        renkler   = [KAT_RENK.get(k, '#888888') for k in etiketler]

        wedges, texts, autotexts = ax1.pie(
            degerler,
            labels=None,
            colors=renkler,
            autopct='%1.1f%%',
            startangle=140,
            pctdistance=0.78,
            wedgeprops={'linewidth': 2, 'edgecolor': PLT_BG}
        )
        for at in autotexts:
            at.set_color(PLT_TEXT)
            at.set_fontsize(8)

        # Legend
        legend_patches = [
            mpatches.Patch(color=renkler[i], label=f"{etiketler[i]}  ₺{degerler[i]:,.0f}")
            for i in range(len(etiketler))
        ]
        ax1.legend(handles=legend_patches, loc="lower center",
                   bbox_to_anchor=(0.5, -0.18), ncol=2,
                   fontsize=7, frameon=False,
                   labelcolor=PLT_TEXT, facecolor=PLT_BG)
        ax1.set_title("Kategori Dağılımı", color=PLT_TEXT, fontsize=10, pad=12)

        # ── 2. Çizgi Grafiği (Aylık Trend Simülasyonu) ──────────
        ax2 = fig.add_subplot(122)
        ax2.set_facecolor(PLT_CARD)

        # Mevcut toplam abonelik tutarından 6 aylık trend simüle et
        # Gerçek proje için aylık snapshot tablosu eklenebilir;
        # burada mevcut toplam üzerine küçük varyasyon uyguluyoruz.
        bas3, toplam = self.abonelik_motoru.toplam_maliyet_hesapla(self.current_user_id)
        toplam = toplam if bas3 else 0.0

        import random
        random.seed(self.current_user_id or 42)
        aylar = []
        degerler_cizgi = []
        simdi = datetime.now()
        for i in range(5, -1, -1):
            ay_dt = datetime(simdi.year if simdi.month > i else simdi.year - 1,
                             ((simdi.month - i - 1) % 12) + 1, 1)
            aylar.append(ay_dt.strftime('%b %Y'))
            # Küçük rastgele sapma (±%15) ile trend
            sapma = 1 + random.uniform(-0.15, 0.15)
            degerler_cizgi.append(round(toplam * sapma, 2))
        # Son ay her zaman gerçek toplam
        degerler_cizgi[-1] = toplam

        ax2.plot(aylar, degerler_cizgi, color=ACCENT, linewidth=2.5,
                 marker='o', markersize=6, markerfacecolor=ACCENT2)
        ax2.fill_between(range(len(aylar)), degerler_cizgi,
                         alpha=0.15, color=ACCENT)

        ax2.set_xticks(range(len(aylar)))
        ax2.set_xticklabels(aylar, rotation=30, ha='right',
                            color=PLT_MUTED, fontsize=7)
        ax2.tick_params(axis='y', colors=PLT_MUTED, labelsize=7)
        ax2.spines['bottom'].set_color(BORDER)
        ax2.spines['left'].set_color(BORDER)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.set_facecolor(PLT_CARD)
        ax2.yaxis.label.set_color(PLT_MUTED)
        ax2.set_title("Aylık Harcama Trendi", color=PLT_TEXT, fontsize=10, pad=12)
        ax2.set_ylabel("₺ Tutar", color=PLT_MUTED, fontsize=8)
        ax2.grid(axis='y', color=BORDER, linestyle='--', alpha=0.4)

        # ── Canvas'a yerleştir ──────────────────────────────────
        canvas = FigureCanvasTkAgg(fig, master=outer)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ════════════════════════════════════════════════════════════
    # TAB: PROJEKSİYON & AKILLI ANALİZ
    # ════════════════════════════════════════════════════════════
    def _tab_projeksiyon(self):
        """
        Yıllık maliyet projeksiyonu ve akıllı iptal önerisi gösterir.
        """
        self._clear_main()
        self._set_active_nav(5)

        sf = ScrollFrame(self.main_area)
        sf.pack(fill="both", expand=True)
        inner = sf.inner
        inner.config(padx=24, pady=20)

        tk.Label(inner, text="🔮 Akıllı Projeksiyon", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w")
        tk.Label(inner, text="Gelecek yılki tahmini abonelik yükü ve öneriler",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(2, 16))

        # Veri çek
        bas, proj = self.analiz_motoru.yillik_projeksiyon_hesapla(self.current_user_id)

        if not bas:
            tk.Label(inner, text=f"Veri alınamadı: {proj}",
                     bg=BG, fg=ERROR, font=FONT_SMALL).pack()
            return

        if proj['aylik_toplam'] == 0:
            tk.Label(inner, text="Projeksiyon için önce abonelik ekleyin.",
                     bg=BG, fg=MUTED, font=FONT_ENTRY).pack(pady=40)
            return

        # ── Özet Kartları ──────────────────────────────────────
        kart_row = tk.Frame(inner, bg=BG)
        kart_row.pack(fill="x", pady=(0, 20))

        ozet_veriler = [
            ("📅 Aylık Toplam",      f"₺{proj['aylik_toplam']:,.2f}",       ACCENT),
            ("📆 Yıllık Toplam",     f"₺{proj['yillik_toplam']:,.2f}",      ACCENT2),
            ("🚀 Gelecek Yıl (+%10)",f"₺{proj['gelecek_yil_tahmini']:,.2f}", WARNING),
            ("📊 Abonelik Başı Ort.", f"₺{proj['aylik_ortalama']:,.2f}",     SUCCESS),
        ]
        for baslik, deger, renk in ozet_veriler:
            self._ozet_kart(kart_row, baslik, deger, renk)

        section_line(inner)

        # ── Projeksiyon Çubuğu ─────────────────────────────────
        tk.Label(inner, text="📈 Yıllık Maliyet Karşılaştırması",
                 bg=BG, fg=TEXT, font=FONT_H3).pack(anchor="w", pady=(0, 10))

        proj_frame = tk.Frame(inner, bg=CARD, highlightthickness=1,
                              highlightbackground=BORDER)
        proj_frame.pack(fill="x", ipady=14)

        maks_proj = proj['gelecek_yil_tahmini']
        for etiket, deger, renk in [
            ("Bu Yıl", proj['yillik_toplam'], ACCENT),
            ("Gelecek Yıl (Tahmini)", proj['gelecek_yil_tahmini'], WARNING),
        ]:
            satir = tk.Frame(proj_frame, bg=CARD)
            satir.pack(fill="x", padx=16, pady=4)
            tk.Label(satir, text=etiket, bg=CARD, fg=MUTED,
                     font=FONT_SMALL, width=24, anchor="w").pack(side="left")
            bar_f = tk.Frame(satir, bg=ENTRY_BG, height=20, width=380)
            bar_f.pack(side="left")
            bar_f.pack_propagate(False)
            oran = (deger / maks_proj) if maks_proj > 0 else 0
            tk.Frame(bar_f, bg=renk, height=20,
                     width=int(380 * oran)).pack(side="left", fill="y")
            tk.Label(satir, text=f"₺{deger:,.2f}", bg=CARD,
                     fg=renk, font=FONT_SMALL).pack(side="left", padx=8)

        section_line(inner)

        # ── İptal Önerisi ──────────────────────────────────────
        tk.Label(inner, text="💡 Akıllı İptal Önerisi",
                 bg=BG, fg=TEXT, font=FONT_H3).pack(anchor="w", pady=(0, 8))

        bas2, oneri = self.analiz_motoru.iptal_onerisi_getir(self.current_user_id)

        if bas2:
            if oneri['oneri_var']:
                oneri_kart = tk.Frame(inner, bg="#2A1A1A", highlightthickness=1,
                                      highlightbackground=ERROR)
                oneri_kart.pack(fill="x")
                tk.Label(oneri_kart, text=oneri['sebep'],
                         bg="#2A1A1A", fg=TEXT,
                         font=FONT_SMALL, wraplength=640, justify="left").pack(
                         anchor="w", padx=14, pady=12)
            else:
                iyi_kart = tk.Frame(inner, bg="#0D2A1A", highlightthickness=1,
                                    highlightbackground=SUCCESS)
                iyi_kart.pack(fill="x")
                tk.Label(iyi_kart, text=f"✅  {oneri['sebep']}",
                         bg="#0D2A1A", fg=SUCCESS,
                         font=FONT_H3).pack(anchor="w", padx=14, pady=12)

        # ── En Pahalı Abonelik ─────────────────────────────────
        if proj.get('en_pahali'):
            en = proj['en_pahali']
            section_line(inner)
            tk.Label(inner, text="🏆 En Pahalı Abonelik",
                     bg=BG, fg=TEXT, font=FONT_H3).pack(anchor="w", pady=(0, 8))
            en_kart = tk.Frame(inner, bg=CARD2, highlightthickness=1,
                               highlightbackground=BORDER)
            en_kart.pack(fill="x")
            renk = KAT_RENK.get(en['kategori'], MUTED)
            tk.Frame(en_kart, bg=renk, width=4).pack(side="left", fill="y")
            tk.Label(en_kart, text=en['servis_adi'], bg=CARD2, fg=TEXT,
                     font=FONT_H3).pack(side="left", padx=12, pady=10)
            tk.Label(en_kart, text=en['kategori'], bg=CARD2, fg=renk,
                     font=FONT_SMALL).pack(side="left", padx=8)
            tk.Label(en_kart, text=f"₺{en['tutar']:,.2f}/ay",
                     bg=CARD2, fg=ERROR, font=FONT_H3).pack(side="right", padx=14)

    # ════════════════════════════════════════════════════════════
    # İŞ MANTIĞI
    # ════════════════════════════════════════════════════════════
    def _do_login(self):
        kullanici_adi = self.login_email.get_value().strip()
        sifre         = self.login_pw.get_value()

        if not kullanici_adi or not sifre:
            self.login_msg.config(text="Lütfen tüm alanları doldurun.")
            return

        basarili, kullanici_id, adi = self.kullanici_motoru.giris_yap(
            kullanici_adi, sifre)

        if basarili:
            self.current_user_id = kullanici_id
            self._show_dashboard(adi)
        else:
            self.login_msg.config(text="Kullanıcı adı veya şifre hatalı.")

    def _do_register(self):
        username = self.reg_name.get_value().strip()
        pw       = self.reg_pw.get_value()
        pw2      = self.reg_pw2.get_value()

        if not all([username, pw, pw2]):
            self.reg_msg.config(text="Lütfen tüm alanları doldurun.")
            return
        if len(username) < 3:
            self.reg_msg.config(text="Kullanıcı adı en az 3 karakter olmalı.")
            return
        if len(pw) < 6:
            self.reg_msg.config(text="Şifre en az 6 karakter olmalı.")
            return
        if pw != pw2:
            self.reg_msg.config(text="Şifreler eşleşmiyor.")
            return

        basarili, mesaj = self.kullanici_motoru.kayit_ol(username, pw)

        if basarili:
            messagebox.showinfo("Başarılı",
                                f"Hoş geldin, {username}! 🎉\nKayıt tamamlandı.")
            self._show_login()
        else:
            self.reg_msg.config(text=mesaj)

    def _save_new_subscription(self):
        servis_adi = self.yeni_servis.get_value().strip()
        fiyat_str  = self.yeni_tutar.get_value().strip()
        kategori   = self.yeni_kat.get()

        try:
            tarih = self.yeni_tarih.get_date().strftime('%Y-%m-%d')
        except Exception:
            self.ekle_msg.config(text="Lütfen geçerli bir tarih seçin.", fg=ERROR)
            return

        if not all([servis_adi, fiyat_str, tarih]):
            self.ekle_msg.config(text="Lütfen tüm alanları doldurun.", fg=ERROR)
            return

        try:
            fiyat = float(fiyat_str)
        except ValueError:
            self.ekle_msg.config(text="Tutar sayı olmalıdır (örn: 49.90)", fg=ERROR)
            return

        if fiyat <= 0:
            self.ekle_msg.config(text="Tutar 0'dan büyük olmalıdır.", fg=ERROR)
            return

        basarili, sonuc = self.abonelik_motoru.ekle(
            servis_adi, fiyat, tarih, kategori, self.current_user_id)

        if basarili:
            self.ekle_msg.config(
                text=f"✓ '{servis_adi}' başarıyla eklendi!", fg=SUCCESS)
            self._temizle_form()
        else:
            self.ekle_msg.config(text=str(sonuc), fg=ERROR)

    def _sil_onayla(self, abonelik_id):
        onay = messagebox.askyesno(
            "Aboneliği Sil",
            "Bu aboneliği silmek istediğinden emin misin?"
        )
        if onay:
            bas, _ = self.abonelik_motoru.sil(abonelik_id)
            if bas:
                self._tab_liste()
            else:
                messagebox.showerror("Hata", "Silme işlemi başarısız.")

    def _change_profile_photo(self):
        dosya_yolu = filedialog.askopenfilename(
            title="Profil Fotoğrafı Seç",
            filetypes=[
                ("Resim Dosyaları", "*.png;*.jpg;*.jpeg"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg;*.jpeg")
            ]
        )
        if not dosya_yolu:
            return

        try:
            img = Image.open(dosya_yolu).convert('RGBA')
            img = img.resize((120, 120), Image.LANCZOS)
        except Exception:
            messagebox.showerror("Hata", "Seçilen resmi açarken bir hata oluştu.")
            return

        proje_kok = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        kayit_adi = f"profile_{self.current_user_id}.png"
        yeni_yol  = os.path.join(proje_kok, kayit_adi)

        try:
            img.save(yeni_yol)
        except Exception:
            messagebox.showerror("Hata", "Profil fotoğrafı kaydedilemedi.")
            return

        basarili, mesaj = self.kullanici_motoru.profil_foto_guncelle(
            self.current_user_id, yeni_yol)
        if not basarili:
            messagebox.showerror("Hata", mesaj)
            return

        self._show_dashboard(self.current_username)
        self._tab_profil()


if __name__ == "__main__":
    app = App()
    app.mainloop()