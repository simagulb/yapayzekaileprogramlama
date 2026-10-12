import json
import os
from google import genai
from google.genai import errors

DOSYA_ADI = "urunler.json"

# --- YARDIMCI FONKSİYONLAR ---

def veri_yukle():
    if not os.path.exists(DOSYA_ADI):
        return []
    try:
        with open(DOSYA_ADI, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def veri_kaydet(urunler):
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(urunler, f, ensure_ascii=False, indent=4)

def yeni_urun_kodu(urunler):
    if not urunler:
        return "URN-0001"
    
    kodlar = []
    for u in urunler:
        try:
            kod_numarasi = int(u["urun_kodu"].split("-")[1])
            kodlar.append(kod_numarasi)
        except (ValueError, IndexError):
            continue
            
    max_kod = max(kodlar) if kodlar else 0
    return f"URN-{max_kod + 1:04d}"

def sayi_al(mesaj, float_mi=False):
    while True:
        deger = input(mesaj)
        try:
            sayi = float(deger) if float_mi else int(deger)
            if sayi < 0:
                print("[HATA] Değer negatif olamaz. Lütfen tekrar girin.")
            else:
                return sayi
        except ValueError:
            print("[HATA] Lütfen geçerli bir sayı girin.")

def stok_durumu_yazdir(stok):
    if stok == 0:
        return "[UYARI] STOKTA YOK!"
    elif 1 <= stok <= 4:
        return f"[UYARI] KRİTİK STOK! Yalnızca {stok} adet kaldı."
    return ""

def e_ticaret_api_simulasyonu(urun_talebi):
    api_anahtari = "AQ.Ab8RN6KKdiSiZ9HqKh6noiNs38uwUztbrDXvZ0HJJE1MRMsYmw"
    
    try:
        client = genai.Client(api_key=api_anahtari)
    except Exception as e:
        print(f"\n[SİSTEM HATASI] İstemci oluşturulamadı: {e}")
        return None

    sistem_mesaji = """
    Sen kurumsal bir e-ticaret sisteminin arka planında çalışan
    bir veri yapılandırma asistanısın.

    Kullanıcının girdiği ham ürün bilgilerini analiz edip,
    veritabanına kaydedilebilmesi için SADECE JSON formatında
    yanıt vermelisin. Ekstra hiçbir metin (markdown vb.) ekleme.

    JSON nesnesi kesinlikle şu anahtarları içermelidir:
    {
        "urun_adi": "Kısa ve optimize edilmiş ürün adı",
        "kategori": "Uygun e-ticaret kategorisi",
        "seo_etiketleri": "3 adet virgülle ayrılmış SEO etiketi",
        "satis_aciklamasi": "Müşteriyi ikna edecek profesyonel 2 cümle"
    }
    """
    
    print("\n[API] Ürün bilgileri oluşturuluyor...")
    
    try:
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=f"{sistem_mesaji}\nKullanıcının ürün talebi:\n{urun_talebi}"
        )
        
        yapilandirilmis_veri = interaction.output_text.strip()
        
        # Markdown kod bloklarını temizleme garantisi
        if yapilandirilmis_veri.startswith("```json"):
            yapilandirilmis_veri = yapilandirilmis_veri[7:]
        if yapilandirilmis_veri.startswith("```"):
            yapilandirilmis_veri = yapilandirilmis_veri[3:]
        if yapilandirilmis_veri.endswith("```"):
            yapilandirilmis_veri = yapilandirilmis_veri[:-3]
            
        return json.loads(yapilandirilmis_veri.strip())
        
    except errors.APIError as e:
        print(f"\n[API HATASI] Açıklama: {e}")
        return None
    except json.JSONDecodeError:
        print("\n[HATA] API'den dönen veri geçerli bir JSON formatında değil.")
        return None
    except Exception as e:
        print(f"\n[SİSTEM HATASI] Beklenmeyen bir istisna oluştu: {e}")
        return None

# --- ANA MENÜ İŞLEMLERİ ---

def urun_ekle(urunler):
    aciklama = input("Ürün açıklaması: ")
    fiyat = sayi_al("Ürün fiyatı: ", float_mi=True)
    stok = sayi_al("Stok miktarı: ")
    
    api_yaniti = e_ticaret_api_simulasyonu(aciklama)
    
    if not api_yaniti or not all(k in api_yaniti for k in ["urun_adi", "kategori", "seo_etiketleri", "satis_aciklamasi"]):
        print("[HATA] Ürün bilgileri API'den eksik veya hatalı döndü. Kayıt iptal edildi.")
        return

    yeni_kod = yeni_urun_kodu(urunler)
    yeni_urun = {
        "urun_kodu": yeni_kod,
        "urun_adi": api_yaniti["urun_adi"],
        "kategori": api_yaniti["kategori"],
        "seo_etiketleri": api_yaniti["seo_etiketleri"],
        "satis_aciklamasi": api_yaniti["satis_aciklamasi"],
        "fiyat": fiyat,
        "stok": stok
    }
    
    urunler.append(yeni_urun)
    veri_kaydet(urunler)
    
    print("\n[BAŞARILI] Ürün kaydedildi.")
    print(f"Ürün Kodu: {yeni_urun['urun_kodu']}")
    print(f"Ürün Adı : {yeni_urun['urun_adi']}")
    print(f"Kategori : {yeni_urun['kategori']}")
    print(f"Fiyat    : {yeni_urun['fiyat']} TL")
    print(f"Stok     : {yeni_urun['stok']}")
    print(f"SEO      : {yeni_urun['seo_etiketleri']}")
    
    uyari = stok_durumu_yazdir(yeni_urun["stok"])
    if uyari:
        print(uyari)

def urun_listele(urunler):
    if not urunler:
        print("\n[BİLGİ] Sistemde kayıtlı ürün bulunmamaktadır.")
        return
        
    print("\n--- MEVCUT ÜRÜNLER ---")
    for u in urunler:
        print(f"{u['urun_kodu']} | {u['urun_adi']} | {u['kategori']} | {u['fiyat']} TL | Stok: {u['stok']}")
        uyari = stok_durumu_yazdir(u["stok"])
        if uyari:
            print(f"  -> {uyari}")

def urun_ara(urunler):
    aranan = input("Aranacak ürün (Ad veya Kod): ").lower()
    bulunanlar = [u for u in urunler if aranan in u["urun_adi"].lower() or aranan in u["urun_kodu"].lower()]
    
    if bulunanlar:
        print(f"\n[SONUÇ] {len(bulunanlar)} ürün bulundu:")
        for u in bulunanlar:
            print(f"- {u['urun_kodu']}: {u['urun_adi']} ({u['stok']} adet)")
    else:
        print("\n[SONUÇ] Aradığınız kriterlere uygun ürün bulunamadı.")

def stok_guncelle(urunler):
    kod = input("Stok güncellenecek ürün kodu (Örn: URN-0001): ").upper()
    for u in urunler:
        if u["urun_kodu"] == kod:
            print(f"Bulunan Ürün: {u['urun_adi']} (Mevcut Stok: {u['stok']})")
            yeni_stok = sayi_al("Yeni stok miktarı: ")
            eski_stok = u["stok"]
            u["stok"] = yeni_stok
            veri_kaydet(urunler)
            
            print(f"\n[BAŞARILI] Stok {eski_stok} -> {yeni_stok} olarak güncellendi.")
            uyari = stok_durumu_yazdir(yeni_stok)
            if uyari:
                print(uyari)
            return
            
    print("[HATA] Belirtilen koda sahip ürün bulunamadı.")

def ana_menu():
    urunler = veri_yukle()
    
    while True:
        print("\n=== E-TİCARET YÖNETİM PANELİ ===")
        print("1 - Yeni Ürün Ekle")
        print("2 - Ürünleri Listele")
        print("3 - Ürün Ara")
        print("4 - Stok Güncelle")
        print("5 - Çıkış")
        
        secim = input("Seçiminiz: ").strip()
        
        if secim == '1':
            urun_ekle(urunler)
        elif secim == '2':
            urun_listele(urunler)
        elif secim == '3':
            urun_ara(urunler)
        elif secim == '4':
            stok_guncelle(urunler)
        elif secim == '5':
            print("Çıkış yapılıyor. İyi çalışmalar!")
            break
        else:
            print("[HATA] Lütfen 1 ile 5 arasında geçerli bir seçim yapın.")

if __name__ == "__main__":
    ana_menu()