import sqlite3
from typing import List, Dict
from datetime import datetime, timedelta
from guvenlik import sifreyi_ozetle, sifreyi_dogrula

class VeritabaniTabani:
    """Veritabani baglantisini ve tablo olusturmayı yoneten temel sinif."""
    
    def __init__(self, db_adi: str = 'subtrack.db'):
        self.db_adi = db_adi
        self.tablolari_kur()
    
    def baglanti_ac(self) -> sqlite3.Connection:
        """Veritabanına bağlantı açar."""
        try:
            return sqlite3.connect(self.db_adi)
        except sqlite3.Error as e:
            raise Exception(f"Veritabanı bağlantısı açılamadı: {str(e)}")
    
    def tablolari_kur(self):
        """Gerekli tabloları oluşturur."""
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            # kullanicilar tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kullanicilar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kullanici_adi TEXT UNIQUE NOT NULL,
                    sifre_ozeti TEXT NOT NULL,
                    profil_foto TEXT DEFAULT 'default_avatar.png',
                    butce_hedefi REAL DEFAULT 2000.0
                )
            ''')
            
            # Mevcut tabloda profil_foto veya butce_hedefi sütunu yoksa ekle
            cursor.execute("PRAGMA table_info(kullanicilar)")
            mevcut_sutunlar = [row[1] for row in cursor.fetchall()]
            if 'profil_foto' not in mevcut_sutunlar:
                cursor.execute('''
                    ALTER TABLE kullanicilar ADD COLUMN profil_foto TEXT DEFAULT 'default_avatar.png'
                ''')
            if 'butce_hedefi' not in mevcut_sutunlar:
                cursor.execute('''
                    ALTER TABLE kullanicilar ADD COLUMN butce_hedefi REAL DEFAULT 2000.0
                ''')
            
            # abonelikler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS abonelikler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    servis_adi TEXT NOT NULL,
                    tutar REAL NOT NULL,
                    odeme_tarihi TEXT NOT NULL,
                    kategori TEXT NOT NULL,
                    kullanici_id INTEGER NOT NULL,
                    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar (id)
                )
            ''')
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            raise Exception(f"Tablolar oluşturulurken hata: {str(e)}")
        except Exception as e:
            raise Exception(f"Beklenmeyen hata: {str(e)}")


class KullaniciIslemleri(VeritabaniTabani):
    """Kullanıcı kaydı ve girişini yoneten sinif."""
    
    def __init__(self, db_adi: str = 'subtrack.db'):
        super().__init__(db_adi)
    
    def kayit_ol(self, kullanici_adi: str, sifre: str) -> tuple:
        """
        Yeni bir kullanıcı kaydeder. Mükerrer kayıt ve güvenlik kontrolü yapar.
        
        Parametreler:
            kullanici_adi (str): Kayıt olacak kullanıcının adı
            sifre (str): Kullanıcının şifresi (hashlenecek)
        
        Dönüş:
            tuple: (başarı: bool, mesaj: str) 
                   Başarılı: (True, "Başarıyla kayıt olundu")
                   Mükerrer: (False, "Bu kullanıcı adı zaten mevcut")
                   Hata: (False, "hata mesajı")
        """
        # Giriş doğrulaması
        if not kullanici_adi or not sifre:
            return (False, "Kullanıcı adı ve şifre boş olamaz")
        
        if len(kullanici_adi) < 3:
            return (False, "Kullanıcı adı en az 3 karakter olmalıdır")
        
        if len(sifre) < 6:
            return (False, "Şifre en az 6 karakter olmalıdır")
        
        # Veritabanına bağlan
        conn = self.baglanti_ac()
        cursor = conn.cursor()
        
        try:
            # Kullanıcı adının zaten veritabanında olup olmadığını kontrol et
            cursor.execute('''
                SELECT id FROM kullanicilar WHERE kullanici_adi = ?
            ''', (kullanici_adi,))
            
            if cursor.fetchone() is not None:
                conn.close()
                return (False, "Bu kullanıcı adı zaten alınmış!")
            
            # Şifreyi guvenlik.py ile hashle
            sifre_ozeti = sifreyi_ozetle(sifre)
            
            # Kullanıcıyı veritabanına ekle
            cursor.execute('''
                INSERT INTO kullanicilar (kullanici_adi, sifre_ozeti, profil_foto)
                VALUES (?, ?, ?)
            ''', (kullanici_adi, sifre_ozeti, 'default_avatar.png'))
            
            conn.commit()
            return (True, "Kayıt başarıyla tamamlandı!")
        
        except sqlite3.IntegrityError:
            return (False, "Bu kullanıcı adı zaten alınmış!")
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Kayıt sırasında beklenmeyen hata: {str(e)}")
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def giris_yap(self, kullanici_adi: str, sifre: str) -> tuple:
        """
        Kullanıcının girişini doğrular.
        
        Parametreler:
            kullanici_adi (str): Giriş yapacak kullanıcının adı
            sifre (str): Giriş yapacak kullanıcının şifresi
        
        Dönüş:
            tuple: (başarı: bool, kullanici_id: int veya None, kullanici_adi: str veya None)
                   Başarılı: (True, id, kullanici_adi)
                   Başarısız: (False, None, None)
        """
        try:
            # Veritabanına bağlan
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            # Kullanıcıyı ara
            cursor.execute('''
                SELECT id, sifre_ozeti FROM kullanicilar WHERE kullanici_adi = ?
            ''', (kullanici_adi,))
            
            sonuc = cursor.fetchone()
            
            # Kullanıcı bulunamadıysa False döner
            if sonuc is None:
                return (False, None, None)
            
            # Şifreyi doğrula
            kullanici_id = sonuc[0]
            kayitli_ozet = sonuc[1]
            dogrulama_sonucu = sifreyi_dogrula(kayitli_ozet, sifre)
            
            if dogrulama_sonucu:
                return (True, kullanici_id, kullanici_adi)
            return (False, None, None)
        
        except sqlite3.Error as e:
            return (False, None, None)  # Giriş hatasında detay vermiyoruz güvenlik için
        except Exception as e:
            return (False, None, None)  # Giriş hatasında detay vermiyoruz güvenlik için
        finally:
            if 'conn' in locals():
                conn.close()

    def profil_bilgisi_getir(self, kullanici_id: int) -> tuple:
        """Kullanıcının profil bilgilerini döner."""
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, kullanici_adi, profil_foto
                FROM kullanicilar
                WHERE id = ?
            ''', (kullanici_id,))
            satir = cursor.fetchone()

            if satir is None:
                return (False, "Kullanıcı bulunamadı.")

            return (True, {
                'id': satir[0],
                'kullanici_adi': satir[1],
                'profil_foto': satir[2]
            })
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()

    def profil_foto_guncelle(self, kullanici_id: int, yeni_yol: str) -> tuple:
        """Kullanıcının profil fotoğrafı yolunu günceller."""
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE kullanicilar
                SET profil_foto = ?
                WHERE id = ?
            ''', (yeni_yol, kullanici_id))
            conn.commit()

            if cursor.rowcount == 0:
                return (False, "Kullanıcı bulunamadı.")
            return (True, "Profil fotoğrafı güncellendi.")
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()

    def butce_guncelle(self, kullanici_id: int, yeni_limit: float) -> tuple:
        """Kullanıcının bütçe hedefini günceller."""
        if yeni_limit is None:
            return (False, "Yeni bütçe limiti boş olamaz.")
        if not isinstance(yeni_limit, (int, float)):
            return (False, "Bütçe limiti sayı olmalıdır.")
        if yeni_limit < 0:
            return (False, "Bütçe limiti negatif olamaz.")

        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE kullanicilar
                SET butce_hedefi = ?
                WHERE id = ?
            ''', (float(yeni_limit), kullanici_id))
            conn.commit()

            if cursor.rowcount == 0:
                return (False, "Kullanıcı bulunamadı.")
            return (True, "Bütçe hedefi başarıyla güncellendi.")
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()

    def butce_getir(self, kullanici_id: int) -> tuple:
        """Kullanıcının bütçe hedefini döner."""
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COALESCE(butce_hedefi, 2000.0)
                FROM kullanicilar
                WHERE id = ?
            ''', (kullanici_id,))
            satir = cursor.fetchone()

            if satir is None:
                return (False, "Kullanıcı bulunamadı.")

            return (True, float(satir[0]))
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()


class AbonelikIslemleri(VeritabaniTabani):
    """Abonelik ekleme, silme ve getirme islemlerini yoneten sinif."""
    
    def __init__(self, db_adi: str = 'subtrack.db'):
        super().__init__(db_adi)
    
    def ekle(self, servis_adi: str, tutar: float, tarih: str, 
             kategori: str, kullanici_id: int) -> tuple:
        """
        Yeni bir abonelik ekler ve eklenen kaydın ID'sini döner.
        Hata durumunda (False, hata_mesaji) döner.
        """
        conn = None
        try:
            # Tutar değerinin sayı olup olmadığını kontrol et
            if not isinstance(tutar, (int, float)):
                return (False, f"Tutar sayı olmalıdır, '{tutar}' tipi alındı.")
            
            # Tutar negatif olamaz
            if tutar < 0:
                return (False, "Tutar negatif olamaz.")
            
            # Parametreleri bir demet (tuple) olarak net bir şekilde veriyoruz
            veriler = (servis_adi, tutar, tarih, kategori, kullanici_id)
            
            # Veritabanına bağlan
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            # Veriyi ekle
            cursor.execute('''
                INSERT INTO abonelikler (servis_adi, tutar, odeme_tarihi, kategori, kullanici_id)
                VALUES (?, ?, ?, ?, ?)
            ''', veriler)
            
            conn.commit()
            yeni_id = cursor.lastrowid
            
            return (True, yeni_id)
        
        except ValueError as e:
            return (False, f"Veri hatası: {str(e)}")
        
        except sqlite3.DatabaseError as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        
        finally:
            # Bağlantı her durumda kapatılır
            if conn is not None:
                conn.close()
    
    def sil(self, abone_id: int) -> tuple:
        """Verilen ID'ye sahip aboneliği siler."""
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM abonelikler WHERE id = ?', (abone_id,))
            conn.commit()
            etkilenen_satir = cursor.rowcount
            
            if etkilenen_satir > 0:
                return (True, "Abonelik başarıyla silindi.")
            else:
                return (False, "Silinecek abonelik bulunamadı.")
        
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()
    
    def listele_hepsi(self, kullanici_id: int) -> tuple:
        """Bir kullanıcının tum aboneliklerini listeler."""
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, servis_adi, tutar, odeme_tarihi, kategori 
                FROM abonelikler 
                WHERE kullanici_id = ?
                ORDER BY odeme_tarihi DESC
            ''', (kullanici_id,))
            
            satirlar = cursor.fetchall()
            
            abonelikler = []
            for satir in satirlar:
                abonelikler.append({
                    'id': satir[0],
                    'servis_adi': satir[1],
                    'tutar': satir[2],
                    'odeme_tarihi': satir[3],
                    'kategori': satir[4]
                })
            
            return (True, abonelikler)
        
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()
    
    def toplam_maliyet_hesapla(self, kullanici_id: int) -> tuple:
        """
        Belirtilen kullanıcının tüm aboneliklerinin toplam tutarını hesaplar.
        
        Parametreler:
            kullanici_id (int): Kullanıcının ID'si
        
        Dönüş:
            tuple: (başarı: bool, toplam_tutar: float veya hata_mesaji: str)
        """
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT SUM(tutar) FROM abonelikler 
                WHERE kullanici_id = ?
            ''', (kullanici_id,))
            
            sonuc = cursor.fetchone()[0]
            
            return (True, sonuc if sonuc is not None else 0.0)
        
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()
    
    def kategori_bazli_dagilim(self, kullanici_id: int) -> tuple:
        """
        Belirtilen kullanıcının kategoriye göre harcama dağılımını hesaplar.
        
        Parametreler:
            kullanici_id (int): Kullanıcının ID'si
        
        Dönüş:
            tuple: (başarı: bool, dagilim: Dict veya hata_mesaji: str)
                  Başarılı: (True, {'Eglence': 450, 'Egitim': 200})
                  Hata: (False, "hata mesajı")
        """
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT kategori, SUM(tutar) as toplam_tutar
                FROM abonelikler
                WHERE kullanici_id = ?
                GROUP BY kategori
                ORDER BY toplam_tutar DESC
            ''', (kullanici_id,))
            
            satirlar = cursor.fetchall()
            
            dagilim = {}
            for satir in satirlar:
                kategori = satir[0]
                toplam_tutar = satir[1]
                dagilim[kategori] = toplam_tutar
            
            return (True, dagilim)
        
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()
    
    def yaklasan_odemeler(self, kullanici_id: int, limit: int = 3) -> tuple:
        """
        Belirtilen kullanıcının ödeme tarihi en yakın olan abonelikleri getirir.
        
        Parametreler:
            kullanici_id (int): Kullanıcının ID'si
            limit (int): Kaç adet abonelik döndürülecek (varsayılan: 3)
        
        Dönüş:
            tuple: (başarı: bool, odemeler: List[Dict] veya hata_mesaji: str)
        """
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, servis_adi, tutar, odeme_tarihi, kategori
                FROM abonelikler
                WHERE kullanici_id = ?
                ORDER BY odeme_tarihi ASC
                LIMIT ?
            ''', (kullanici_id, limit))
            
            satirlar = cursor.fetchall()
            
            odemeler = []
            for satir in satirlar:
                odemeler.append({
                    'id': satir[0],
                    'servis_adi': satir[1],
                    'tutar': satir[2],
                    'odeme_tarihi': satir[3],
                    'kategori': satir[4]
                })
            
            return (True, odemeler)
        
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()



class AnalizMerkezi(VeritabaniTabani):
    """Abone maliyetleri ve kategorilere göre analiz yapan sinif."""
    
    def __init__(self, db_adi: str = 'subtrack.db'):
        super().__init__(db_adi)
    
    def aylik_toplam_hesapla(self, kullanici_id: int, yil: int = None, ay: int = None) -> tuple:
        """Belirtilen ay için toplam abonelik maliyetini hesaplar."""
        if yil is None or ay is None:
            simdi = datetime.now()
            yil = simdi.year
            ay = simdi.month
        
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT SUM(tutar) FROM abonelikler 
                WHERE kullanici_id = ? 
                AND strftime('%Y-%m', odeme_tarihi) = ?
            ''', (kullanici_id, f'{yil:04d}-{ay:02d}'))
            
            sonuc = cursor.fetchone()[0]
            
            return (True, sonuc if sonuc is not None else 0.0)
        
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()

    def butce_durumu_getir(self, kullanici_id: int) -> tuple:
        """Kullanıcının bütçe durumu özetini döner."""
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COALESCE(SUM(a.tutar), 0.0), COALESCE(k.butce_hedefi, 2000.0)
                FROM kullanicilar k
                LEFT JOIN abonelikler a ON a.kullanici_id = k.id
                WHERE k.id = ?
            ''', (kullanici_id,))

            satir = cursor.fetchone()
            if satir is None:
                return (False, "Kullanıcı bulunamadı.")

            toplam_harcama = float(satir[0])
            butce_hedefi = float(satir[1]) if satir[1] is not None else 2000.0
            oran = (toplam_harcama / butce_hedefi * 100.0) if butce_hedefi > 0 else 0.0

            return (True, {
                'toplam_harcama': toplam_harcama,
                'butce_hedefi': butce_hedefi,
                'butce_orani': round(oran, 2)
            })
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()
    
    def kategori_ozeti_getir(self, kullanici_id: int) -> tuple:
        """Aboneliklerin kategori özetini getirir."""
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT kategori, SUM(tutar) as toplam_tutar, COUNT(*) as abone_sayisi
                FROM abonelikler
                WHERE kullanici_id = ?
                GROUP BY kategori
                ORDER BY toplam_tutar DESC
            ''', (kullanici_id,))
            
            satirlar = cursor.fetchall()
            
            kategoriler = []
            for satir in satirlar:
                kategoriler.append({
                    'kategori': satir[0],
                    'toplam_tutar': satir[1],
                    'abone_sayisi': satir[2]
                })
            
            return (True, kategoriler)
        
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()
    
    def yaklasan_odemeleri_bul(self, kullanici_id: int, gun_sayisi: int = 3) -> tuple:
        """
        Belirtilen gün içinde ödeme tarihi olan abonelikleri bulur.
        
        Parametreler:
            kullanici_id (int): Kullanıcının ID'si
            gun_sayisi (int): Kaç gün içindeki ödemeleri bulsun (varsayılan: 3)
        
        Dönüş:
            tuple: (başarı: bool, odemeler: List[Dict] veya hata_mesaji: str)
        """
        conn = None
        try:
            # Bugünün tarihini al
            bugun = datetime.now()
            
            # Yaklaşan ödeme tarihi sınırını hesapla
            limit_tarihi = bugun + datetime.timedelta(days=gun_sayisi)
            
            # Bugün ile limit tarihi arasında ödeme olan abonelikleri ara
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, servis_adi, tutar, odeme_tarihi, kategori
                FROM abonelikler
                WHERE kullanici_id = ?
                AND DATE(odeme_tarihi) BETWEEN DATE(?) AND DATE(?)
                ORDER BY odeme_tarihi ASC
            ''', (kullanici_id, bugun.strftime('%Y-%m-%d'), limit_tarihi.strftime('%Y-%m-%d')))
            
            satirlar = cursor.fetchall()
            
            yaklasan_odemeler = []
            for satir in satirlar:
                yaklasan_odemeler.append({
                    'id': satir[0],
                    'servis_adi': satir[1],
                    'tutar': satir[2],
                    'odeme_tarihi': satir[3],
                    'kategori': satir[4]
                })
            
            return (True, yaklasan_odemeler)
        
        except sqlite3.Error as e:
            return (False, f"Veritabanı hatası: {str(e)}")
        except Exception as e:
            return (False, f"Beklenmeyen hata: {str(e)}")
        finally:
            if conn is not None:
                conn.close()
    
if __name__ == "__main__":
    # Test için nesneleri oluşturuyoruz
    islem = AbonelikIslemleri()
    analiz = AnalizMerkezi()
    
    # MANUEL VERİ GİRİŞİ (Deneme yapıyoruz)
    print("Demo veriler ekleniyor...")
    islem.ekle("Netflix", 189.90, "2026-05-15", "Eğlence", 1)
    islem.ekle("Spotify", 29.90, "2026-05-20", "Eğlence", 1)
    islem.ekle("ChatGPT Plus", 99.00, "2026-05-10", "Yazılım", 1)
    islem.ekle("Udemy", 149.90, "2026-05-25", "Eğitim", 1)
    
    # VERİLERİ ÇEKİP TERMİNALDE GÖRME
    liste = islem.listele_hepsi(1)
    print("Veritabanındaki Abonelikler:", liste)
    
    # Hatalı veri denemesi (Tutar yerine yazı yazıyoruz)
    islem.ekle("Netflix", "Çok Pahalı", "2026-05-15", "Eglence", 1)
    # Önce sınıftan bir nesne oluşturuyoruz
    kullanici_servisi = KullaniciIslemleri() 

    # Şimdi o nesne üzerinden fonksiyonu çağırıyoruz
    kullanici_servisi.kayit_ol("demet", "1234") 
    print("Kullanıcı başarıyla kaydedildi!")

