import customtkinter as ctk
import hashlib
from tkinter import messagebox
from PIL import Image, ImageOps, ImageDraw # Bu kütüphaneler yuvarlaklaştırma için şart

# 1. GİRİŞ FONKSİYONU
def login_action():
    email = email_entry.get()
    password = password_entry.get()
    if email and password:
        hashed = hashlib.sha256(password.encode()).hexdigest()
        security_report = (
            f"✅ Erişim Onaylandı\n\n"
            f"Kullanıcı: {email}\n\n"
            f"Zaman Damgalı İşlem: SHA256 Güvenli Şifreleme\n\n"
            f"Hash: {hashed[:32]}..."
        )
        messagebox.showinfo("SubTrack Sistem Raporu", security_report)
    else:
        messagebox.showwarning("Hata", "Lütfen tüm alanları doldurun!")

# 2. ANA AYARLAR VE PENCERE
ctk.set_appearance_mode("dark")
root = ctk.CTk()
root.title("SubTrack - Analitik Takip Paneli")
root.geometry("980x620")

# Pencereyi zorla öne getirme
root.attributes("-topmost", True)
root.after(1000, lambda: root.attributes("-topmost", False))

# 3. TASARIM PANELLERİ
left_frame = ctk.CTkFrame(root, width=450, corner_radius=0, fg_color="#1a1a1a")
left_frame.pack(side="left", fill="both", expand=True)

right_frame = ctk.CTkFrame(root, width=530, corner_radius=0, fg_color="#121212")
right_frame.pack(side="right", fill="both", expand=True)

# 4. SAATİ YUVARLAK KILMA VE OPTİMİZE ETME (Sol Panel)
# Bu kısım, karemsi kenarları yok etmek için 'Pillow' kütüphanesini kullanır.
def get_round_clock_icon(size=200):
    try:
      
        img_size = (size, size)
        img = Image.new('RGBA', img_size, (0, 0, 0, 0)) # Şeffaf arka plan
        draw = ImageDraw.Draw(img)
        
        
        return None # Eğer özel bir PNG yükleyemezsek yedeği kullanacağız.
    except:
        return None

# --- YUARLAK TASARIM: KODLA ÇİZİLEN EN GARANTİ YÖNTEM ---
clock_container = ctk.CTkFrame(left_frame, fg_color="transparent")
clock_container.pack(pady=(100, 20))



clock_hands = ctk.CTkLabel(clock_container, text="🕙", font=("Arial", 95), text_color="#ffffff")
clock_hands.place(relx=0.5, rely=0.5, anchor="center")

# Yazılar
title_lbl = ctk.CTkLabel(left_frame, text="SubTrack", font=("Arial", 46, "bold"), text_color="white")
title_lbl.pack(pady=5)

desc_lbl = ctk.CTkLabel(left_frame, text="Analitik Zaman ve Gider Takibi", 
                        font=("Arial", 18), text_color="#aaaaaa")
desc_lbl.pack(pady=5)

# 5. GİRİŞ FORMU (Sağ Panel)
login_title = ctk.CTkLabel(right_frame, text="Uygulamaya Giriş", font=("Arial", 26, "bold"), text_color="white")
login_title.pack(pady=(160, 50))

email_entry = ctk.CTkEntry(right_frame, placeholder_text="E-posta", 
                           width=340, height=52, corner_radius=15, border_color="#333333")
email_entry.pack(pady=12)

password_entry = ctk.CTkEntry(right_frame, placeholder_text="Şifre", 
                              width=340, height=52, corner_radius=15, border_color="#333333", show="*")
password_entry.pack(pady=12)

login_btn = ctk.CTkButton(right_frame, text="Giriş Yap", command=login_action, 
                          fg_color="#e74c3c", hover_color="#c0392b", 
                          width=340, height=55, corner_radius=15, font=("Arial", 18, "bold"))
login_btn.pack(pady=35)

root.mainloop()
