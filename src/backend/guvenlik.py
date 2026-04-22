import hashlib

def sifreyi_ozetle(sifre: str) -> str:
    """
    Kullanıcının girdiği şifreyi SHA256 algoritmasıyla hashler.
    
    Parametreler:
        sifre (str): Hashlenecek metin halindeki şifre
    
    Dönüş:
        str: SHA256 algoritmasıyla üretilen 64 karakterlik hex string
    """
    # Şifreyi byte formatına dönüştür (SHA256 byte gerektirir)
    sifre_byte = sifre.encode('utf-8')
    
    # SHA256 hash nesnesi oluştur
    hash_nesnesi = hashlib.sha256(sifre_byte)
    
    # Hash sonucunu hexadecimal string formatına çevir
    sifre_ozeti = hash_nesnesi.hexdigest()
    
    return sifre_ozeti


def sifreyi_dogrula(kayitli_ozet: str, girilen_sifre: str) -> bool:
    """
    Kullanıcının giriş yaparken girdiği şifreyi veritabanındaki özetle karşılaştırır.
    
    Parametreler:
        kayitli_ozet (str): Veritabanında saklanan şifre özeti
        girilen_sifre (str): Giriş ekranında kullanıcı tarafından girilen metin şifre
    
    Dönüş:
        bool: Şifreler eşleşiyorsa True, eşleşmiyorsa False
    """
    # Girilen şifreyi hashle
    girilen_ozet = sifreyi_ozetle(girilen_sifre)
    
    # Hashlenmiş şifreyi veritabanındaki özetle karşılaştır
    sifreler_eslesme = kayitli_ozet == girilen_ozet
    
    return sifreler_eslesme


# Test için kullanım örneği
if __name__ == "__main__":
    # Örnek şifre
    ornek_sifre = "GucluSifre123!"
    
    # 1. Şifreyi özet halinde kayıt et
    print("=== ŞİFRE KAYDI ===")
    sifre_ozeti = sifreyi_ozetle(ornek_sifre)
    print(f"Girilen şifre: {ornek_sifre}")
    print(f"Oluşturulan özet: {sifre_ozeti}")
    
    # 2. Giriş yaparken şifreyi doğrula (doğru şifre)
    print("\n=== DOĞRU ŞİFRE GİRİŞİ ===")
    dogru_sifre = "GucluSifre123!"
    sonuc = sifreyi_dogrula(sifre_ozeti, dogru_sifre)
    print(f"Girilen şifre: {dogru_sifre}")
    print(f"Doğrulama sonucu: {sonuc}")
    
    # 3. Yanlış şifre ile giriş denemesi
    print("\n=== YANLIŞ ŞİFRE GİRİŞİ ===")
    yanlis_sifre = "YanlisSifre123!"
    sonuc = sifreyi_dogrula(sifre_ozeti, yanlis_sifre)
    print(f"Girilen şifre: {yanlis_sifre}")
    print(f"Doğrulama sonucu: {sonuc}")