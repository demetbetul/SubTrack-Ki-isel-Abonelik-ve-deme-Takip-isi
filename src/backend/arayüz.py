import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import json
import os
import re

# ── Veri dosyası ──────────────────────────────────────────────
DATA_FILE = "users.json"

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

# ── Renkler & Fontlar ─────────────────────────────────────────
BG        = "#0D0F1A"   # koyu lacivert arka plan
CARD      = "#151828"   # kart arka planı
ACCENT    = "#4F8EF7"   # ana mavi aksan
ACCENT2   = "#A259FF"   # mor aksan
TEXT      = "#E8EAF6"   # açık metin
MUTED     = "#6B7280"   # soluk metin
ENTRY_BG  = "#1E2235"   # giriş kutusu arka planı
BORDER    = "#2A2F4A"   # kenarlık
SUCCESS   = "#34D399"   # yeşil (başarı)
ERROR     = "#F87171"   # kırmızı (hata)

FONT_TITLE  = ("Georgia", 26, "bold")
FONT_SUB    = ("Georgia", 11, "italic")
FONT_LABEL  = ("Helvetica", 10, "bold")
FONT_ENTRY  = ("Helvetica", 11)
FONT_BTN    = ("Helvetica", 11, "bold")
FONT_LINK   = ("Helvetica", 9, "underline")
FONT_SMALL  = ("Helvetica", 8)

# ── Yardımcı widget'lar ───────────────────────────────────────
class PlaceholderEntry(tk.Entry):
    """Placeholder destekli Entry"""
    def __init__(self, master, placeholder="", show_char="", **kw):
        super().__init__(master, **kw)
        self._ph       = placeholder
        self._show     = show_char
        self._focused  = False
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
        if self._showing_ph:
            return ""
        return self.get()


def styled_entry(parent, placeholder, show_char="", width=28):
    e = PlaceholderEntry(
        parent,
        placeholder=placeholder,
        show_char=show_char,
        width=width,
        bg=ENTRY_BG,
        fg=MUTED,
        insertbackground=ACCENT,
        relief="flat",
        font=FONT_ENTRY,
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
    )
    return e


def styled_button(parent, text, command, color=ACCENT, width=22):
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg="#FFFFFF",
        activebackground=ACCENT2,
        activeforeground="#FFFFFF",
        relief="flat",
        font=FONT_BTN,
        cursor="hand2",
        width=width,
        pady=8,
    )
    # Hover efekti
    btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT2))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def divider(parent):
    f = tk.Frame(parent, bg=CARD)
    tk.Frame(f, bg=BORDER, height=1, width=100).pack(side="left", padx=4, pady=8)
    tk.Label(f, text="veya", bg=CARD, fg=MUTED, font=FONT_SMALL).pack(side="left")
    tk.Frame(f, bg=BORDER, height=1, width=100).pack(side="left", padx=4, pady=8)
    return f


# ── Ana Uygulama ──────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SubTrack – Abonelik Yöneticisi")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._center(500, 620)
        self.users = load_users()
        self._show_login()

    def _center(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ── GİRİŞ EKRANI ─────────────────────────────────────────
    def _show_login(self):
        self._clear()
        self.geometry("500x620")
        self._center(500, 620)

        root_frame = tk.Frame(self, bg=BG)
        root_frame.pack(expand=True, fill="both", padx=40, pady=30)

        # Logo alanı
        logo_frame = tk.Frame(root_frame, bg=BG)
        logo_frame.pack(pady=(10, 0))
        self._draw_logo(logo_frame)

        tk.Label(root_frame, text="SubTrack", bg=BG, fg=TEXT,
                 font=FONT_TITLE).pack(pady=(8, 0))
        tk.Label(root_frame, text="Aboneliklerini akıllıca yönet", bg=BG,
                 fg=MUTED, font=FONT_SUB).pack(pady=(2, 20))

        # Kart
        card = tk.Frame(root_frame, bg=CARD, bd=0,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", pady=4, ipady=10)

        tk.Label(card, text="Hesabına Giriş Yap", bg=CARD, fg=TEXT,
                 font=("Helvetica", 13, "bold")).pack(pady=(18, 12))

        # E-posta
        tk.Label(card, text="E-POSTA", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.login_email = styled_entry(card, "ornek@mail.com")
        self.login_email.pack(padx=30, pady=(2, 10), ipady=6, fill="x")

        # Şifre
        tk.Label(card, text="ŞİFRE", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.login_pw = styled_entry(card, "••••••••", show_char="•")
        self.login_pw.pack(padx=30, pady=(2, 6), ipady=6, fill="x")

        self.login_msg = tk.Label(card, text="", bg=CARD, fg=ERROR,
                                  font=FONT_SMALL)
        self.login_msg.pack()

        btn = styled_button(card, "  Giriş Yap  ", self._do_login)
        btn.pack(pady=10)

        divider(card).pack()

        # Alt link
        bottom = tk.Frame(card, bg=CARD)
        bottom.pack(pady=(4, 16))
        tk.Label(bottom, text="Hesabın yok mu?", bg=CARD, fg=MUTED,
                 font=FONT_SMALL).pack(side="left")
        lnk = tk.Label(bottom, text=" Üye Ol", bg=CARD, fg=ACCENT,
                        font=FONT_LINK, cursor="hand2")
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda e: self._show_register())

        # Versiyon
        tk.Label(root_frame, text="v1.0  •  Veriler SHA-256 ile korunur",
                 bg=BG, fg=MUTED, font=FONT_SMALL).pack(pady=(12, 0))

    # ── KAYIT EKRANI ──────────────────────────────────────────
    def _show_register(self):
        self._clear()
        self.geometry("500x700")
        self._center(500, 700)

        root_frame = tk.Frame(self, bg=BG)
        root_frame.pack(expand=True, fill="both", padx=40, pady=20)

        logo_frame = tk.Frame(root_frame, bg=BG)
        logo_frame.pack(pady=(0, 0))
        self._draw_logo(logo_frame, size=40)

        tk.Label(root_frame, text="SubTrack", bg=BG, fg=TEXT,
                 font=("Georgia", 20, "bold")).pack(pady=(6, 0))
        tk.Label(root_frame, text="Yeni hesap oluştur", bg=BG,
                 fg=MUTED, font=FONT_SUB).pack(pady=(2, 14))

        card = tk.Frame(root_frame, bg=CARD, bd=0,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", pady=4, ipady=10)

        tk.Label(card, text="Üye Ol", bg=CARD, fg=TEXT,
                 font=("Helvetica", 13, "bold")).pack(pady=(18, 12))

        # Ad Soyad
        tk.Label(card, text="AD SOYAD", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.reg_name = styled_entry(card, "Adın Soyadın")
        self.reg_name.pack(padx=30, pady=(2, 10), ipady=6, fill="x")

        # E-posta
        tk.Label(card, text="E-POSTA", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.reg_email = styled_entry(card, "ornek@mail.com")
        self.reg_email.pack(padx=30, pady=(2, 10), ipady=6, fill="x")

        # Şifre
        tk.Label(card, text="ŞİFRE", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.reg_pw = styled_entry(card, "En az 6 karakter", show_char="•")
        self.reg_pw.pack(padx=30, pady=(2, 10), ipady=6, fill="x")

        # Şifre tekrar
        tk.Label(card, text="ŞİFRE TEKRAR", bg=CARD, fg=MUTED,
                 font=FONT_LABEL, anchor="w").pack(fill="x", padx=30)
        self.reg_pw2 = styled_entry(card, "Şifreni tekrar gir", show_char="•")
        self.reg_pw2.pack(padx=30, pady=(2, 6), ipady=6, fill="x")

        self.reg_msg = tk.Label(card, text="", bg=CARD, fg=ERROR,
                                font=FONT_SMALL, wraplength=340)
        self.reg_msg.pack()

        btn = styled_button(card, "  Hesap Oluştur  ", self._do_register,
                            color=SUCCESS)
        btn.pack(pady=10)

        divider(card).pack()

        bottom = tk.Frame(card, bg=CARD)
        bottom.pack(pady=(4, 16))
        tk.Label(bottom, text="Zaten hesabın var mı?", bg=CARD, fg=MUTED,
                 font=FONT_SMALL).pack(side="left")
        lnk = tk.Label(bottom, text=" Giriş Yap", bg=CARD, fg=ACCENT,
                        font=FONT_LINK, cursor="hand2")
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda e: self._show_login())

    # ── Logo (Canvas ile çizim) ───────────────────────────────
    def _draw_logo(self, parent, size=56):
        c = tk.Canvas(parent, width=size, height=size, bg=BG,
                      highlightthickness=0)
        c.pack()
        # Arka daire – mor gradient simülasyonu
        c.create_oval(2, 2, size-2, size-2, fill=ACCENT2, outline="")
        # İç daire
        m = size * 0.18
        c.create_oval(m, m, size-m, size-m, fill=ACCENT, outline="")
        # Para/takvim sembolü: basit "₺" ikonu
        cx, cy = size/2, size/2
        fs = max(10, size // 3)
        c.create_text(cx, cy, text="₺", fill="#FFFFFF",
                      font=("Helvetica", fs, "bold"))

    # ── İŞ MANTIĞI ───────────────────────────────────────────
    def _do_login(self):
        email = self.login_email.get_value().strip()
        pw    = self.login_pw.get_value()

        if not email or not pw:
            self.login_msg.config(text="Lütfen tüm alanları doldurun.", fg=ERROR)
            return

        hashed = hash_password(pw)
        if email in self.users and self.users[email]["password"] == hashed:
            name = self.users[email].get("name", "Kullanıcı")
            self._show_dashboard(name)
        else:
            self.login_msg.config(
                text="E-posta veya şifre hatalı.", fg=ERROR)

    def _do_register(self):
        name  = self.reg_name.get_value().strip()
        email = self.reg_email.get_value().strip()
        pw    = self.reg_pw.get_value()
        pw2   = self.reg_pw2.get_value()

        if not all([name, email, pw, pw2]):
            self.reg_msg.config(text="Lütfen tüm alanları doldurun.", fg=ERROR)
            return
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
            self.reg_msg.config(text="Geçerli bir e-posta adresi girin.", fg=ERROR)
            return
        if len(pw) < 6:
            self.reg_msg.config(text="Şifre en az 6 karakter olmalı.", fg=ERROR)
            return
        if pw != pw2:
            self.reg_msg.config(text="Şifreler eşleşmiyor.", fg=ERROR)
            return
        if email in self.users:
            self.reg_msg.config(text="Bu e-posta zaten kayıtlı.", fg=ERROR)
            return

        self.users[email] = {"name": name, "password": hash_password(pw)}
        save_users(self.users)
        messagebox.showinfo("Başarılı", f"Hoş geldin, {name}! 🎉\nŞimdi giriş yapabilirsin.")
        self._show_login()

    # ── DASHBOARD (geçici hoşgeldin ekranı) ──────────────────
    def _show_dashboard(self, name):
        self._clear()
        self.geometry("500x340")
        self._center(500, 340)

        f = tk.Frame(self, bg=BG)
        f.pack(expand=True, fill="both", padx=40, pady=40)

        self._draw_logo(f, size=64)
        tk.Label(f, text=f"Hoş geldin, {name}! 👋", bg=BG, fg=TEXT,
                 font=("Georgia", 18, "bold")).pack(pady=(16, 6))
        tk.Label(f, text="Ana ekran burada backend ekibine bağlanacak.",
                 bg=BG, fg=MUTED, font=FONT_ENTRY).pack()

        btn = styled_button(f, "Çıkış Yap", self._show_login, color=MUTED, width=16)
        btn.pack(pady=24)


if __name__ == "__main__":
    app = App()
    app.mainloop()