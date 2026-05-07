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
            
            # Mevcut tabloda eksik sütunlar varsa ekle
            cursor.execute("PRAGMA table_info(kullanicilar)")
            mevcut_sutunlar = [row[1] for row in cursor.fetchall()]
            if 'profil_foto' not in mevcut_sutunlar:
                cursor.execute("ALTER TABLE kullanicilar ADD COLUMN profil_foto TEXT DEFAULT 'default_avatar.png'")
            if 'butce_hedefi' not in mevcut_sutunlar:
                cursor.execute("ALTER TABLE kullanicilar ADD COLUMN butce_hedefi REAL DEFAULT 2000.0")
            
            # abonelikler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS abonelikler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    servis_adi TEXT NOT NULL,
                    tutar REAL NOT NULL,
                    odeme_tarihi TEXT NOT NULL,
                    kategori TEXT NOT NULL,
                    kullanici_id INTEGER NOT NULL,
                    odendi_mi INTEGER DEFAULT 0,
                    FOREIGN KEY (kullanici_id) REFERENCES kullanicilar (id)
                )
            ''')

            # Mevcut abonelikler tablosunda odendi_mi sütunu yoksa ekle (migration)
            cursor.execute("PRAGMA table_info(abonelikler)")
            abone_sutunlar = [row[1] for row in cursor.fetchall()]
            if 'odendi_mi' not in abone_sutunlar:
                cursor.execute("ALTER TABLE abonelikler ADD COLUMN odendi_mi INTEGER DEFAULT 0")
            
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
        if not kullanici_adi or not sifre:
            return (False, "Kullanıcı adı ve şifre boş olamaz")
        if len(kullanici_adi) < 3:
            return (False, "Kullanıcı adı en az 3 karakter olmalıdır")
        if len(sifre) < 6:
            return (False, "Şifre en az 6 karakter olmalıdır")
        
        conn = self.baglanti_ac()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM kullanicilar WHERE kullanici_adi = ?', (kullanici_adi,))
            if cursor.fetchone() is not None:
                conn.close()
                return (False, "Bu kullanıcı adı zaten alınmış!")
            
            sifre_ozeti = sifreyi_ozetle(sifre)
            cursor.execute(
                'INSERT INTO kullanicilar (kullanici_adi, sifre_ozeti, profil_foto) VALUES (?, ?, ?)',
                (kullanici_adi, sifre_ozeti, 'default_avatar.png')
            )
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
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('SELECT id, sifre_ozeti FROM kullanicilar WHERE kullanici_adi = ?', (kullanici_adi,))
            sonuc = cursor.fetchone()
            
            if sonuc is None:
                return (False, None, None)
            
            kullanici_id = sonuc[0]
            kayitli_ozet = sonuc[1]
            
            if sifreyi_dogrula(kayitli_ozet, sifre):
                return (True, kullanici_id, kullanici_adi)
            return (False, None, None)
        
        except Exception:
            return (False, None, None)
        finally:
            if 'conn' in locals():
                conn.close()

    def profil_bilgisi_getir(self, kullanici_id: int) -> tuple:
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id, kullanici_adi, profil_foto FROM kullanicilar WHERE id = ?',
                (kullanici_id,)
            )
            satir = cursor.fetchone()
            if satir is None:
                return (False, "Kullanıcı bulunamadı.")
            return (True, {'id': satir[0], 'kullanici_adi': satir[1], 'profil_foto': satir[2]})
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    def profil_foto_guncelle(self, kullanici_id: int, yeni_yol: str) -> tuple:
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('UPDATE kullanicilar SET profil_foto = ? WHERE id = ?', (yeni_yol, kullanici_id))
            conn.commit()
            if cursor.rowcount == 0:
                return (False, "Kullanıcı bulunamadı.")
            return (True, "Profil fotoğrafı güncellendi.")
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    def butce_guncelle(self, kullanici_id: int, yeni_limit: float) -> tuple:
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
            cursor.execute('UPDATE kullanicilar SET butce_hedefi = ? WHERE id = ?', (float(yeni_limit), kullanici_id))
            conn.commit()
            if cursor.rowcount == 0:
                return (False, "Kullanıcı bulunamadı.")
            return (True, "Bütçe hedefi başarıyla güncellendi.")
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    def butce_getir(self, kullanici_id: int) -> tuple:
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('SELECT COALESCE(butce_hedefi, 2000.0) FROM kullanicilar WHERE id = ?', (kullanici_id,))
            satir = cursor.fetchone()
            if satir is None:
                return (False, "Kullanıcı bulunamadı.")
            return (True, float(satir[0]))
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()


class AbonelikIslemleri(VeritabaniTabani):
    """Abonelik ekleme, silme, güncelleme ve getirme islemlerini yoneten sinif."""
    
    def __init__(self, db_adi: str = 'subtrack.db'):
        super().__init__(db_adi)
    
    def ekle(self, servis_adi: str, tutar: float, tarih: str, 
             kategori: str, kullanici_id: int) -> tuple:
        conn = None
        try:
            if not isinstance(tutar, (int, float)):
                return (False, f"Tutar sayı olmalıdır, '{tutar}' tipi alındı.")
            if tutar < 0:
                return (False, "Tutar negatif olamaz.")
            
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO abonelikler (servis_adi, tutar, odeme_tarihi, kategori, kullanici_id) VALUES (?, ?, ?, ?, ?)',
                (servis_adi, tutar, tarih, kategori, kullanici_id)
            )
            conn.commit()
            return (True, cursor.lastrowid)
        
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    # ── YENİ: Abonelik güncelleme ──────────────────────────────────
    def guncelle(self, abonelik_id: int, servis_adi: str, tutar: float,
                 tarih: str, kategori: str) -> tuple:
        """
        Mevcut bir aboneliğin tüm alanlarını günceller.
        
        Dönüş: (başarı: bool, mesaj: str)
        """
        conn = None
        try:
            if not isinstance(tutar, (int, float)) or tutar <= 0:
                return (False, "Geçerli bir tutar girin.")
            
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE abonelikler
                SET servis_adi = ?, tutar = ?, odeme_tarihi = ?, kategori = ?
                WHERE id = ?
            ''', (servis_adi, float(tutar), tarih, kategori, abonelik_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                return (False, "Güncellenecek abonelik bulunamadı.")
            return (True, "Abonelik başarıyla güncellendi.")
        
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()
    
    def sil(self, abone_id: int) -> tuple:
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM abonelikler WHERE id = ?', (abone_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return (True, "Abonelik başarıyla silindi.")
            return (False, "Silinecek abonelik bulunamadı.")
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()
    
    def listele_hepsi(self, kullanici_id: int) -> tuple:
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, servis_adi, tutar, odeme_tarihi, kategori,
                       COALESCE(odendi_mi, 0)
                FROM abonelikler 
                WHERE kullanici_id = ?
                ORDER BY odeme_tarihi DESC
            ''', (kullanici_id,))
            
            abonelikler = []
            for satir in cursor.fetchall():
                abonelikler.append({
                    'id': satir[0],
                    'servis_adi': satir[1],
                    'tutar': satir[2],
                    'odeme_tarihi': satir[3],
                    'kategori': satir[4],
                    'odendi_mi': bool(satir[5])
                })
            return (True, abonelikler)
        
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()
    
    def toplam_maliyet_hesapla(self, kullanici_id: int) -> tuple:
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(tutar) FROM abonelikler WHERE kullanici_id = ?', (kullanici_id,))
            sonuc = cursor.fetchone()[0]
            return (True, sonuc if sonuc is not None else 0.0)
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()
    
    def kategori_bazli_dagilim(self, kullanici_id: int) -> tuple:
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
            
            dagilim = {}
            for satir in cursor.fetchall():
                dagilim[satir[0]] = satir[1]
            return (True, dagilim)
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()
    
    def yaklasan_odemeler(self, kullanici_id: int, limit: int = 3) -> tuple:
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, servis_adi, tutar, odeme_tarihi, kategori,
                       COALESCE(odendi_mi, 0)
                FROM abonelikler
                WHERE kullanici_id = ?
                ORDER BY odeme_tarihi ASC
                LIMIT ?
            ''', (kullanici_id, limit))
            
            odemeler = []
            for satir in cursor.fetchall():
                odemeler.append({
                    'id': satir[0],
                    'servis_adi': satir[1],
                    'tutar': satir[2],
                    'odeme_tarihi': satir[3],
                    'kategori': satir[4],
                    'odendi_mi': bool(satir[5])
                })
            return (True, odemeler)
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    # ── YENİ: Ödeme durumunu güncelle ──────────────────────────────
    def odeme_durumu_guncelle(self, abonelik_id: int, odendi: bool) -> tuple:
        """
        Belirli bir aboneliğin ödendi_mi alanını günceller.

        Parametreler:
            abonelik_id (int): Güncellenecek aboneliğin ID'si
            odendi (bool): True = ödendi, False = ödenmedi

        Dönüş: (başarı: bool, mesaj: str)
        """
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE abonelikler SET odendi_mi = ? WHERE id = ?',
                (1 if odendi else 0, abonelik_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                return (False, "Abonelik bulunamadı.")
            return (True, "Ödeme durumu güncellendi.")
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    # ── YENİ: Ayın 1'inde otomatik sıfırlama ──────────────────────
    def aylik_odeme_sifirla(self, kullanici_id: int) -> tuple:
        """
        Kullanıcının tüm aboneliklerinin ödendi_mi değerini 0'a sıfırlar.
        Her ayın 1'inde çağrılmak üzere tasarlanmıştır.

        Dönüş: (başarı: bool, sifirlanan_adet: int veya hata_mesaji: str)
        """
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE abonelikler SET odendi_mi = 0 WHERE kullanici_id = ?',
                (kullanici_id,)
            )
            conn.commit()
            return (True, cursor.rowcount)
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()
    def yarin_odemeleri_bul(self, kullanici_id: int) -> tuple:
        """
        Yarın ödeme tarihi olan ve henüz ödenmemiş abonelikleri bulur.
        win10toast bildirimleri için kullanılır.

        Dönüş: (başarı: bool, liste: List[Dict])
        """
        conn = None
        try:
            yarin = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, servis_adi, tutar, odeme_tarihi, kategori,
                       COALESCE(odendi_mi, 0)
                FROM abonelikler
                WHERE kullanici_id = ?
                AND DATE(odeme_tarihi) = DATE(?)
                AND COALESCE(odendi_mi, 0) = 0
                ORDER BY odeme_tarihi ASC
            ''', (kullanici_id, yarin))

            odemeler = []
            for satir in cursor.fetchall():
                odemeler.append({
                    'id': satir[0],
                    'servis_adi': satir[1],
                    'tutar': satir[2],
                    'odeme_tarihi': satir[3],
                    'kategori': satir[4],
                    'odendi_mi': bool(satir[5])
                })
            return (True, odemeler)
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()


class AnalizMerkezi(VeritabaniTabani):
    """Abone maliyetleri ve kategorilere göre analiz yapan sinif."""
    
    def __init__(self, db_adi: str = 'subtrack.db'):
        super().__init__(db_adi)
    
    def aylik_toplam_hesapla(self, kullanici_id: int, yil: int = None, ay: int = None) -> tuple:
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
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    def butce_durumu_getir(self, kullanici_id: int) -> tuple:
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
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()
    
    def kategori_ozeti_getir(self, kullanici_id: int) -> tuple:
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
            
            kategoriler = []
            for satir in cursor.fetchall():
                kategoriler.append({
                    'kategori': satir[0],
                    'toplam_tutar': satir[1],
                    'abone_sayisi': satir[2]
                })
            return (True, kategoriler)
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    # ── YENİ: Yıllık Projeksiyon ───────────────────────────────────
    def yillik_projeksiyon_hesapla(self, kullanici_id: int) -> tuple:
        """
        Mevcut aboneliklerin 12 aylık toplam maliyetini ve gelecek yıl
        beklenen yükü hesaplar (%10 fiyat artışı varsayımıyla).
        
        Dönüş:
            tuple: (başarı: bool, {
                'aylik_toplam': float,
                'yillik_toplam': float,
                'gelecek_yil_tahmini': float,
                'aylik_ortalama': float,
                'en_pahali': dict veya None
            })
        """
        conn = None
        try:
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, servis_adi, tutar, kategori
                FROM abonelikler
                WHERE kullanici_id = ?
                ORDER BY tutar DESC
            ''', (kullanici_id,))
            
            satirlar = cursor.fetchall()
            
            if not satirlar:
                return (True, {
                    'aylik_toplam': 0.0,
                    'yillik_toplam': 0.0,
                    'gelecek_yil_tahmini': 0.0,
                    'aylik_ortalama': 0.0,
                    'en_pahali': None
                })
            
            aylik_toplam = sum(s[2] for s in satirlar)
            yillik_toplam = aylik_toplam * 12
            # %10 enflasyon/zam tahmini
            gelecek_yil = yillik_toplam * 1.10
            aylik_ort = aylik_toplam / len(satirlar)
            
            en_pahali = {
                'id': satirlar[0][0],
                'servis_adi': satirlar[0][1],
                'tutar': satirlar[0][2],
                'kategori': satirlar[0][3]
            }
            
            return (True, {
                'aylik_toplam': aylik_toplam,
                'yillik_toplam': yillik_toplam,
                'gelecek_yil_tahmini': gelecek_yil,
                'aylik_ortalama': aylik_ort,
                'en_pahali': en_pahali,
                'abone_sayisi': len(satirlar)
            })
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    # ── YENİ: İptal Önerisi Mantığı ────────────────────────────────
    def iptal_onerisi_getir(self, kullanici_id: int) -> tuple:
        """
        Bütçe aşıldığında iptal edilmesi önerilen aboneliği belirler.
        
        Mantık:
          1. Bütçe aşılmadıysa öneri yok.
          2. Aşıldıysa; kategori yoğunluğu en yüksek kategorideki
             en pahalı aboneliği önerir. 
             Yoğunluk eşitse en pahalı abonelik seçilir.
        
        Dönüş:
            tuple: (başarı: bool, {
                'oneri_var': bool,
                'abonelik': dict veya None,
                'sebep': str
            })
        """
        conn = None
        try:
            # Önce bütçe durumunu kontrol et
            bas, butce = self.butce_durumu_getir(kullanici_id)
            if not bas:
                return (False, "Bütçe bilgisi alınamadı.")
            
            if butce['butce_orani'] <= 100:
                return (True, {
                    'oneri_var': False,
                    'abonelik': None,
                    'sebep': 'Bütçe hedefi içindesiniz.'
                })
            
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            
            # Kategori yoğunluğunu bul
            cursor.execute('''
                SELECT kategori, COUNT(*) as sayi, SUM(tutar) as toplam
                FROM abonelikler
                WHERE kullanici_id = ?
                GROUP BY kategori
                ORDER BY sayi DESC, toplam DESC
            ''', (kullanici_id,))
            
            kat_satirlar = cursor.fetchall()
            if not kat_satirlar:
                return (True, {'oneri_var': False, 'abonelik': None, 'sebep': 'Abonelik yok.'})
            
            # En yoğun kategori
            hedef_kat = kat_satirlar[0][0]
            
            # O kategorideki en pahalı abonelik
            cursor.execute('''
                SELECT id, servis_adi, tutar, odeme_tarihi, kategori
                FROM abonelikler
                WHERE kullanici_id = ? AND kategori = ?
                ORDER BY tutar DESC
                LIMIT 1
            ''', (kullanici_id, hedef_kat))
            
            satir = cursor.fetchone()
            if not satir:
                return (True, {'oneri_var': False, 'abonelik': None, 'sebep': 'Öneri bulunamadı.'})
            
            asim = butce['toplam_harcama'] - butce['butce_hedefi']
            sebep = (
                f"Bütçenizi ₺{asim:,.2f} aşıyorsunuz. "
                f"'{hedef_kat}' kategorisinde {kat_satirlar[0][1]} aboneliğiniz var. "
                f"'{satir[1]}' (₺{satir[2]:,.2f}/ay) aboneliğini iptal etmeyi düşünebilirsiniz."
            )
            
            return (True, {
                'oneri_var': True,
                'abonelik': {
                    'id': satir[0],
                    'servis_adi': satir[1],
                    'tutar': satir[2],
                    'odeme_tarihi': satir[3],
                    'kategori': satir[4]
                },
                'sebep': sebep
            })
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()

    def yaklasan_odemeleri_bul(self, kullanici_id: int, gun_sayisi: int = 3) -> tuple:
        """Belirtilen gün içinde ödeme tarihi olan abonelikleri bulur."""
        conn = None
        try:
            bugun = datetime.now()
            limit_tarihi = bugun + timedelta(days=gun_sayisi)
            conn = self.baglanti_ac()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, servis_adi, tutar, odeme_tarihi, kategori
                FROM abonelikler
                WHERE kullanici_id = ?
                AND DATE(odeme_tarihi) BETWEEN DATE(?) AND DATE(?)
                ORDER BY odeme_tarihi ASC
            ''', (kullanici_id, bugun.strftime('%Y-%m-%d'), limit_tarihi.strftime('%Y-%m-%d')))
            
            odemeler = []
            for satir in cursor.fetchall():
                odemeler.append({
                    'id': satir[0],
                    'servis_adi': satir[1],
                    'tutar': satir[2],
                    'odeme_tarihi': satir[3],
                    'kategori': satir[4]
                })
            return (True, odemeler)
        except Exception as e:
            return (False, str(e))
        finally:
            if conn is not None:
                conn.close()