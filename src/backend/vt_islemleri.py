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
        return sqlite3.connect(self.db_adi)
    
    def tablolari_kur(self):
        """Gerekli tabloları oluşturur."""
        conn = self.baglanti_ac()
        cursor = conn.cursor()
        
        # kullanicilar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kullanicilar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_adi TEXT UNIQUE NOT NULL,
                sifre_ozeti TEXT NOT NULL
            )
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


class KullaniciIslemleri(VeritabaniTabani):
    """Kullanıcı kaydı ve girişini yoneten sinif."""
    
    def __init__(self, db_adi: str = 'subtrack.db'):
        super().__init__(db_adi)
    
    def kayit_ol(self, kullanici_adi: str, sifre: str) -> bool:
        """
        Yeni bir kullanıcı kaydeder.
        
        Parametreler:
            kullanici_adi (str): Kayıt olacak kullanıcının adı
            sifre (str): Kullanıcının şifresi (hashlenecek)
        
        Dönüş:
            bool: Kayıt başarılıysa True, başarısızsa False
        """
        try:
            # Şifreyi hashle
            sifre_ozeti = sifreyi_ozetle(sifre)
            
            # Veritabanına bağlan
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            # Kullanıcıyı ekle
            cursor.execute('''
                INSERT INTO kullanicilar (kullanici_adi, sifre_ozeti)
                VALUES (?, ?)
            ''', (kullanici_adi, sifre_ozeti))
            
            conn.commit()
            conn.close()
            
            return True
        
        except sqlite3.IntegrityError:
            # Kullanıcı adı zaten varsa
            return False
    
    def giris_yap(self, kullanici_adi: str, sifre: str) -> bool:
        """
        Kullanıcının girişini doğrular.
        
        Parametreler:
            kullanici_adi (str): Giriş yapacak kullanıcının adı
            sifre (str): Giriş yapacak kullanıcının şifresi
        
        Dönüş:
            bool: Giriş başarılıysa True, başarısızsa False
        """
        # Veritabanına bağlan
        conn = self.baglanti_ac()
        cursor = conn.cursor()
        
        # Kullanıcıyı ara
        cursor.execute('''
            SELECT id, sifre_ozeti FROM kullanicilar WHERE kullanici_adi = ?
        ''', (kullanici_adi,))
        
        sonuc = cursor.fetchone()
        conn.close()
        
        # Kullanıcı bulunamadıysa False döner
        if sonuc is None:
            return False
        
        # Şifreyi doğrula
        kayitli_ozet = sonuc[1]
        dogrulama_sonucu = sifreyi_dogrula(kayitli_ozet, sifre)
        
        return dogrulama_sonucu


class AbonelikIslemleri(VeritabaniTabani):
    """Abonelik ekleme, silme ve getirme islemlerini yoneten sinif."""
    
    def __init__(self, db_adi: str = 'subtrack.db'):
        super().__init__(db_adi)
    
    def ekle(self, servis_adi: str, tutar: float, tarih: str, 
             kategori: str, kullanici_id: int):
        """
        Yeni bir abonelik ekler ve eklenen kaydın ID'sini döner.
        Hata durumunda False döner.
        """
        conn = None
        try:
            # Tutar değerinin sayı olup olmadığını kontrol et
            if not isinstance(tutar, (int, float)):
                raise ValueError(f"Tutar sayı olmalıdır, '{tutar}' tipi alındı.")
            
            # Tutar negatif olamaz
            if tutar < 0:
                raise ValueError("Tutar negatif olamaz.")
            
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
            
            return yeni_id
        
        except ValueError as e:
            # Veri tipi hatası
            print(f"❌ VERİ HATASI: {e}")
            return False
        
        except sqlite3.DatabaseError as e:
            # Veritabanı hatası
            print(f"❌ VERİTABANI HATASI: {e}")
            return False
        
        except Exception as e:
            # Diğer beklenmeyen hatalar
            print(f"❌ BEKLENMEYEN HATA: {e}")
            return False
        
        finally:
            # Bağlantı her durumda kapatılır
            if conn is not None:
                conn.close()
    
    def sil(self, abone_id: int) -> bool:
        """Verilen ID'ye sahip aboneliği siler."""
        conn = self.baglanti_ac()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM abonelikler WHERE id = ?', (abone_id,))
        conn.commit()
        etkilenen_satir = cursor.rowcount
        conn.close()
        
        return etkilenen_satir > 0
    
    def listele_hepsi(self, kullanici_id: int) -> List[Dict]:
        """Bir kullanıcının tum aboneliklerini listeler."""
        conn = self.baglanti_ac()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, servis_adi, tutar, odeme_tarihi, kategori 
            FROM abonelikler 
            WHERE kullanici_id = ?
            ORDER BY odeme_tarihi DESC
        ''', (kullanici_id,))
        
        satirlar = cursor.fetchall()
        conn.close()
        
        abonelikler = []
        for satir in satirlar:
            abonelikler.append({
                'id': satir[0],
                'servis_adi': satir[1],
                'tutar': satir[2],
                'odeme_tarihi': satir[3],
                'kategori': satir[4]
            })
        
        return abonelikler



class AnalizMerkezi(VeritabaniTabani):
    """Abone maliyetleri ve kategorilere göre analiz yapan sinif."""
    
    def __init__(self, db_adi: str = 'subtrack.db'):
        super().__init__(db_adi)
    
    def aylik_toplam_hesapla(self, kullanici_id: int, yil: int = None, ay: int = None) -> float:
        """Belirtilen ay için toplam abonelik maliyetini hesaplar."""
        if yil is None or ay is None:
            simdi = datetime.now()
            yil = simdi.year
            ay = simdi.month
        
        conn = self.baglanti_ac()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(tutar) FROM abonelikler 
            WHERE kullanici_id = ? 
            AND strftime('%Y-%m', odeme_tarihi) = ?
        ''', (kullanici_id, f'{yil:04d}-{ay:02d}'))
        
        sonuc = cursor.fetchone()[0]
        conn.close()
        
        return sonuc if sonuc is not None else 0.0
    
    def kategori_ozeti_getir(self, kullanici_id: int) -> List[Dict]:
        """Aboneliklerin kategori özetini getirir."""
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
        conn.close()
        
        kategoriler = []
        for satir in satirlar:
            kategoriler.append({
                'kategori': satir[0],
                'toplam_tutar': satir[1],
                'abone_sayisi': satir[2]
            })
        
        return kategoriler
    
    def yaklasan_odemeleri_bul(self, kullanici_id: int, gun_sayisi: int = 3) -> List[Dict]:
        """
        Belirtilen gün içinde ödeme tarihi olan abonelikleri bulur.
        
        Parametreler:
            kullanici_id (int): Kullanıcının ID'si
            gun_sayisi (int): Kaç gün içindeki ödemeleri bulsun (varsayılan: 3)
        
        Dönüş:
            List[Dict]: Yaklaşan ödeme tarihi olan aboneliklerin listesi
        """
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
        conn.close()
        
        yaklasan_odemeler = []
        for satir in satirlar:
            yaklasan_odemeler.append({
                'id': satir[0],
                'servis_adi': satir[1],
                'tutar': satir[2],
                'odeme_tarihi': satir[3],
                'kategori': satir[4]
            })
        
        return yaklasan_odemeler
    
if __name__ == "__main__":
    # Test için nesneleri oluşturuyoruz
    islem = AbonelikIslemleri()
    analiz = AnalizMerkezi()
    
    # MANUEL VERİ GİRİŞİ (Deneme yapıyoruz)
    print("Veri ekleniyor...")
    islem.ekle("Netflix", 189.90, "2026-05-15", "Eglence", 1)
    
    # VERİLERİ ÇEKİP TERMİNALDE GÖRME
    liste = islem.listele_hepsi(1)
    print("Veritabanındaki Abonelikler:", liste)
    
    # Hatalı veri denemesi (Tutar yerine yazı yazıyoruz)
islem.ekle("Netflix", "Çok Pahalı", "2026-05-15", "Eglence", 1)
