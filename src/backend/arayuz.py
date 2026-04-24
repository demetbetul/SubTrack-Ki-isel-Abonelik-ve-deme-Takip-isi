import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageOps, ImageDraw
from vt_islemleri import KullaniciIslemleri

# Global değişkenler
kullanici_islemleri = KullaniciIslemleri()
aktif_tab = "login"  # "login" veya "register"

# 1. GİRİŞ FONKSİYONU
def login_action():
    email = email_entry.get()
    password = password_entry.get()
    
    # Alan kontrolü
    if not email or not password:
        hata_label.configure(text="❌ Lütfen tüm alanları doldurun!", text_color="#ff6b6b")
        return
    
    # Veritabanında giriş doğrulaması
    giris_basarili = kullanici_islemleri.giris_yap(email, password)
    
    if giris_basarili:
        hata_label.configure(text="✅ Giriş başarılı! Hoşgeldiniz.", text_color="#51cf66")
        messagebox.showinfo("Başarılı", f"Hoşgeldiniz {email}!")
        # TODO: Ana ekrana geç
    else:
        hata_label.configure(text="❌ Kullanıcı adı veya şifre yanlış!", text_color="#ff6b6b")

# 2. KAYIT FONKSİYONU
def kayit_action():
    kullanici_adi = kayit_username_entry.get()
    sifre = kayit_password_entry.get()
    sifre_tekrar = kayit_password_repeat_entry.get()
    
    # Alan kontrolü
    if not kullanici_adi or not sifre or not sifre_tekrar:
        kayit_hata_label.configure(text="❌ Lütfen tüm alanları doldurun!", text_color="#ff6b6b")
        return
    
    # Şifre eşleşme kontrolü
    if sifre != sifre_tekrar:
        kayit_hata_label.configure(text="❌ Şifreler eşleşmiyor!", text_color="#ff6b6b")
        return
    
    # Veritabanına kayıt yap
    basarili, mesaj = kullanici_islemleri.kayit_ol(kullanici_adi, sifre)
    
    if basarili:
        kayit_hata_label.configure(text=f"✅ {mesaj}", text_color="#51cf66")
        messagebox.showinfo("Başarılı", mesaj)
        # Alanları temizle
        kayit_username_entry.delete(0, ctk.END)
        kayit_password_entry.delete(0, ctk.END)
        kayit_password_repeat_entry.delete(0, ctk.END)
    else:
        kayit_hata_label.configure(text=f"❌ {mesaj}", text_color="#ff6b6b")

# 3. SEKMELERİ GÖSTERİ/GİZLE
def show_login_tab():
    global aktif_tab
    aktif_tab = "login"
    # Login kütüphanesini göster
    login_frame.pack(side="right", fill="both", expand=True)
    # Register kütüphanesini gizle
    register_frame.pack_forget()
    # Buton renklerini güncelle
    login_tab_btn.configure(fg_color="#e74c3c", text_color="white")
    register_tab_btn.configure(fg_color="#333333", text_color="#aaaaaa")

def show_register_tab():
    global aktif_tab
    aktif_tab = "register"
    # Register kütüphanesini göster
    register_frame.pack(side="right", fill="both", expand=True)
    # Login kütüphanesini gizle
    login_frame.pack_forget()
    # Buton renklerini güncelle
    register_tab_btn.configure(fg_color="#e74c3c", text_color="white")
    login_tab_btn.configure(fg_color="#333333", text_color="#aaaaaa")

# 4. ANA AYARLAR VE PENCERE
ctk.set_appearance_mode("dark")
root = ctk.CTk()
root.title("SubTrack - Analitik Takip Paneli")
root.geometry("980x620")

# Pencereyi zorla öne getirme
root.attributes("-topmost", True)
root.after(1000, lambda: root.attributes("-topmost", False))

# 5. TASARIM PANELLERİ
left_frame = ctk.CTkFrame(root, width=450, corner_radius=0, fg_color="#1a1a1a")
left_frame.pack(side="left", fill="both", expand=True)

# SOL PANEL - Logo ve Başlık
clock_container = ctk.CTkFrame(left_frame, fg_color="transparent")
clock_container.pack(pady=(100, 20))

clock_hands = ctk.CTkLabel(clock_container, text="🕙", font=("Arial", 95), text_color="#ffffff")
clock_hands.pack()

title_lbl = ctk.CTkLabel(left_frame, text="SubTrack", font=("Arial", 46, "bold"), text_color="white")
title_lbl.pack(pady=5)

desc_lbl = ctk.CTkLabel(left_frame, text="Analitik Zaman ve Gider Takibi", 
                        font=("Arial", 18), text_color="#aaaaaa")
desc_lbl.pack(pady=5)

# 6. SAĞ PANEL - TAB YÖNETİMİ
right_panel = ctk.CTkFrame(root, width=530, corner_radius=0, fg_color="#121212")
right_panel.pack(side="right", fill="both", expand=True)

# Tab seçim butonları
tab_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
tab_frame.pack(pady=20, padx=20, fill="x")

login_tab_btn = ctk.CTkButton(tab_frame, text="Giriş Yap", command=show_login_tab,
                              fg_color="#e74c3c", text_color="white", width=160, height=40,
                              font=("Arial", 14, "bold"))
login_tab_btn.pack(side="left", padx=5)

register_tab_btn = ctk.CTkButton(tab_frame, text="Kayıt Ol", command=show_register_tab,
                                 fg_color="#333333", text_color="#aaaaaa", width=160, height=40,
                                 font=("Arial", 14, "bold"))
register_tab_btn.pack(side="left", padx=5)

# 7. GİRİŞ TAB
login_frame = ctk.CTkFrame(right_panel, fg_color="#121212")

login_title = ctk.CTkLabel(login_frame, text="Uygulamaya Giriş", font=("Arial", 26, "bold"), text_color="white")
login_title.pack(pady=(40, 50))

email_entry = ctk.CTkEntry(login_frame, placeholder_text="Kullanıcı Adı", 
                           width=340, height=52, corner_radius=15, border_color="#333333")
email_entry.pack(pady=12)

password_entry = ctk.CTkEntry(login_frame, placeholder_text="Şifre", 
                              width=340, height=52, corner_radius=15, border_color="#333333", show="*")
password_entry.pack(pady=12)

login_btn = ctk.CTkButton(login_frame, text="Giriş Yap", command=login_action, 
                          fg_color="#e74c3c", hover_color="#c0392b", 
                          width=340, height=55, corner_radius=15, font=("Arial", 18, "bold"))
login_btn.pack(pady=35)

# Durum mesajı etiketi
hata_label = ctk.CTkLabel(login_frame, text="", font=("Arial", 12), text_color="#ff6b6b")
hata_label.pack(pady=10)

login_frame.pack(side="right", fill="both", expand=True)

# 8. KAYIT TAB
register_frame = ctk.CTkFrame(right_panel, fg_color="#121212")

register_title = ctk.CTkLabel(register_frame, text="Yeni Hesap Oluştur", font=("Arial", 26, "bold"), text_color="white")
register_title.pack(pady=(30, 40))

kayit_username_entry = ctk.CTkEntry(register_frame, placeholder_text="Kullanıcı Adı", 
                                    width=340, height=52, corner_radius=15, border_color="#333333")
kayit_username_entry.pack(pady=10)

kayit_password_entry = ctk.CTkEntry(register_frame, placeholder_text="Şifre", 
                                    width=340, height=52, corner_radius=15, border_color="#333333", show="*")
kayit_password_entry.pack(pady=10)

kayit_password_repeat_entry = ctk.CTkEntry(register_frame, placeholder_text="Şifreyi Tekrar Girin", 
                                           width=340, height=52, corner_radius=15, border_color="#333333", show="*")
kayit_password_repeat_entry.pack(pady=10)

register_btn = ctk.CTkButton(register_frame, text="Kayıt Ol", command=kayit_action, 
                             fg_color="#51cf66", hover_color="#40c057", 
                             width=340, height=55, corner_radius=15, font=("Arial", 18, "bold"))
register_btn.pack(pady=25)

# Kayıt durum mesajı etiketi
kayit_hata_label = ctk.CTkLabel(register_frame, text="", font=("Arial", 12), text_color="#ff6b6b")
kayit_hata_label.pack(pady=10)

root.mainloop()
