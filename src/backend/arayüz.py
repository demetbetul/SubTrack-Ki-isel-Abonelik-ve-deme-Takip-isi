import tkinter as tk
import os
from tkinter import ttk, messagebox, filedialog
import re
from PIL import Image, ImageTk, ImageDraw
from vt_islemleri import KullaniciIslemleri, AbonelikIslemleri, AnalizMerkezi
from tkcalendar import DateEntry

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

# Kategori renkleri
KAT_RENK = {
    'Eğlence': '#F87171',
    'Eğitim':  '#34D399',
    'Yazılım': '#4F8EF7',
    'Sağlık':  '#FBBF24',
    'Diğer':   '#A259FF',
}


# ── Yardımcı Widget'lar ───────────────────────────────────────
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


# ── Ana Uygulama ──────────────────────────────────────────────
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

        tk.Label(root, text="v1.0  •  Veriler SHA-256 ile korunur",
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
        self._center(780, 640)

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
            ("🏠  Genel Bakış",    self._tab_genel),
            ("➕  Abonelik Ekle",  self._tab_ekle),
            ("�  Profilim",       self._tab_profil),
            ("�📋  Aboneliklerim",  self._tab_liste),
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

    # ── TAB: GENEL BAKIŞ ──────────────────────────────────────
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

        toplam   = toplam if bas1 else 0.0
        liste    = liste  if bas2 else []
        yaklas   = yaklas if bas3 else []
        katlar   = katlar if bas4 else []
        butce    = butce  if bas5 else {'toplam_harcama': 0.0, 'butce_hedefi': 2000.0, 'butce_orani': 0.0}

        # ── Özet kartları ──
        kart_satir = tk.Frame(inner, bg=BG)
        kart_satir.pack(fill="x", pady=(0, 16))

        self._ozet_kart(kart_satir, "💳  Toplam Aylık",
                        f"₺{toplam:,.2f}", ACCENT)
        self._ozet_kart(kart_satir, "📦  Aktif Abonelik",
                        str(len(liste)), ACCENT2)
        ortalama = (toplam / len(liste)) if liste else 0
        self._ozet_kart(kart_satir, "�  Ortalama",
                        f"₺{ortalama:,.2f}", SUCCESS)

        # ── Bütçe İzleme Çubuğu ──
        self._butce_takip_cubugu(inner, butce)

        # ── Yaklaşan ödemeler ──
        tk.Label(inner, text="⏰  Yaklaşan Ödemeler", bg=BG, fg=TEXT,
                 font=FONT_H3).pack(anchor="w", pady=(8, 6))

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

    def _butce_takip_cubugu(self, parent, butce):
        """Bütçe durumunu gösteren ilerleme çubuğu ve etiket."""
        harcama = butce.get('toplam_harcama', 0.0)
        hedef = butce.get('butce_hedefi', 2000.0)
        oran = butce.get('butce_orani', 0.0)
        
        kalan = max(0, hedef - harcama)
        kalan_oran = max(0, 100 - oran)
        
        # Renk seçimi
        if oran < 70:
            bar_renk = SUCCESS
        elif oran < 90:
            bar_renk = WARNING
        else:
            bar_renk = ERROR
        
        # İçerik çerçevesi
        container = tk.Frame(parent, bg=BG)
        container.pack(fill="x", pady=(16, 0))
        
        # Başlık
        tk.Label(container, text="💰  Bütçe İzleme", bg=BG, fg=TEXT,
                 font=FONT_H3).pack(anchor="w", pady=(0, 8))
        
        # Çubuk çerçevesi
        bar_frame = tk.Frame(container, bg=ENTRY_BG, height=28)
        bar_frame.pack(fill="x", pady=(0, 6))
        bar_frame.pack_propagate(False)
        
        # Dolu kısım
        if hedef > 0:
            dolu_yuzde = min(oran, 100.0)
            dolu_frame = tk.Frame(bar_frame, bg=bar_renk, height=28)
            dolu_frame.place(relwidth=dolu_yuzde/100.0, relheight=1)
        
        # Bilgi etiketi
        info_text = f"₺{harcama:,.2f} / ₺{hedef:,.2f} (Limitinize {kalan_oran:.1f}% kaldı)"
        tk.Label(bar_frame, text=info_text, bg=ENTRY_BG, fg=TEXT,
                 font=FONT_H3, anchor="center").pack(fill="both", expand=True)

    # ── TAB: ABONELİK EKLE ────────────────────────────────────
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

        # Servis Adı
        tk.Label(card, text="SERVİS ADI", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=24, pady=(18, 0))
        self.yeni_servis = styled_entry(card, "Netflix, Spotify, Gym...")
        self.yeni_servis.pack(padx=24, pady=(4, 12), ipady=6, fill="x")

        # Tutar
        tk.Label(card, text="TUTAR (₺)", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=24)
        self.yeni_tutar = styled_entry(card, "0.00")
        self.yeni_tutar.pack(padx=24, pady=(4, 12), ipady=6, fill="x")

        # Ödeme Tarihi
        tk.Label(card, text="ÖDEME TARİHİ", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=24)
        self.yeni_tarih = DateEntry(card,
                                    background=ACCENT,
                                    foreground=TEXT,
                                    bordercolor=BORDER,
                                    date_pattern='y-mm-dd',
                                    font=FONT_ENTRY,
                                    width=18)
        self.yeni_tarih.pack(padx=24, pady=(4, 12), ipady=6, fill="x")

        # Kategori (Combobox)
        tk.Label(card, text="KATEGORİ", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=24)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                        fieldbackground=ENTRY_BG, background=ENTRY_BG,
                        foreground=TEXT, selectbackground=ACCENT,
                        bordercolor=BORDER, arrowcolor=ACCENT,
                        relief="flat")

        self.yeni_kat = ttk.Combobox(card, values=KATEGORILER,
                                     style="Dark.TCombobox",
                                     font=FONT_ENTRY, state="readonly")
        self.yeni_kat.set("Eğlence")
        self.yeni_kat.pack(padx=24, pady=(4, 6), ipady=4, fill="x")

        self.ekle_msg = tk.Label(card, text="", bg=CARD, fg=ERROR,
                                 font=FONT_SMALL)
        self.ekle_msg.pack(pady=(4, 0))

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(pady=14)
        styled_button(btn_row, "  Kaydet  ", self._save_new_subscription,
                      color=SUCCESS, width=16).pack(side="left", padx=6)
        styled_button(btn_row, "  Temizle  ", self._temizle_form,
                      color=MUTED, width=12).pack(side="left", padx=6)

    def _temizle_form(self):
        from datetime import datetime

        for e in [self.yeni_servis, self.yeni_tutar]:
            e._showing_ph = False
            e.delete(0, tk.END)
            e._on_focus_out(None)

        self.yeni_tarih.set_date(datetime.now())
        self.yeni_kat.set("Eğlence")
        self.ekle_msg.config(text="")

    # ── TAB: ABONELİKLERİM ────────────────────────────────────
    def _tab_liste(self):
        self._clear_main()
        self._set_active_nav(3)

        outer = tk.Frame(self.main_area, bg=BG)
        outer.pack(fill="both", expand=True, padx=30, pady=24)

        tk.Label(outer, text="Aboneliklerim", bg=BG, fg=TEXT,
                 font=FONT_H2).pack(anchor="w")
        tk.Label(outer, text="Kayıtlı tüm abonelikler",
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
                        ("Tarih", 12), ("Kategori", 12), ("", 6)]:
            tk.Label(header, text=col, bg=CARD, fg=MUTED,
                     font=FONT_LABEL, width=w, anchor="w").pack(side="left", padx=6, pady=6)

        sf = ScrollFrame(outer)
        sf.pack(fill="both", expand=True)
        inner = sf.inner

        for item in liste:
            self._liste_satiri(inner, item)

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
                      color=ACCENT, width=18, pady=10).pack(pady=(8, 0))

    def _liste_satiri(self, parent, item):
        renk = KAT_RENK.get(item['kategori'], MUTED)
        row = tk.Frame(parent, bg=CARD2, highlightthickness=1,
                       highlightbackground=BORDER)
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

        sil_btn = tk.Button(row, text="🗑", bg=CARD2, fg=ERROR,
                             activebackground=ERROR, activeforeground="#FFF",
                             relief="flat", cursor="hand2", font=FONT_H3,
                             command=lambda aid=item['id']: self._sil_onayla(aid))
        sil_btn.pack(side="right", padx=10)

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
        yeni_yol = os.path.join(proje_kok, kayit_adi)

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