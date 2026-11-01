# STATUS

Stand: 01.11.2026 · v0.1.0 · SPEC 0.5 · Dal `dilim-1/grundgeruest`

## Aktueller Stand
- Dilim 1 (Kütüphane ve kayıt) başladı. Kararlar D-001–D-012.
- Adım 1–3 bitti (25 test yeşil): iskelet; token'lar (açık/koyu), Figtree/Plex Mono, kabuk (telefonda alt
  leiste, ≥ 900 px'te kenar çubuğu), logo, Einstellungen › Darstellung; sözlük `app/texte.py` + `t()`.
  Ekranda denendi: açık, koyu, 375 px, yatay kayma yok. Docker ve start.bat henüz denenmedi.
- Adım 4 bitti (40 test): migration 001 (kategori + sabit „Sonstiges“/XX, filtre ve seçenekleri, ürün, filtre
  değerleri, renk, fiyat, fotoğraf, envanter sayacı) ve `services/nummern.py` (kod KK-KKK-EEE, numara tekrar verilmez).
- Adım 5 bitti (61 test): `/api/kategorien` + Einstellungen › Kategorien & Filter (masaüstü; telefonda yalnız
  Allgemein). Önek önerisi, dört filtre tipi, sıralama, kullanım sayıları ve kaydetmeden önce etki notu, sürüm
  kontrolü (409), yalnız boş kategori silinir + „Rückgängig“. Ekranda denendi (oluştur, kaydet, sil, geri al).
- Adım 6 bitti (89 test): `/api/produkte` + `/produkt/neu`, `/produkt/{nr}`, `/p/{nr}` (QR linki). Ürün formu:
  fotoğraf (çek/seç, masaüstünde sürükle/yapıştır; sunucu 320/960 webp + 2400 jpg üretir), tür, ad, kategori
  (değişince kod sorusu + filtre değerleri uyarısı), filtre değerleri, marka, ebat, fiyat (Almanca yazım, tarih),
  adet, link, renk paleti, not, silme (onaylı). Son kategori cihazda hatırlanır. Ekranda denendi.
- Adım 7 bitti (109 test): `/api/bibliothek` (her kelime eşleşmeli, ä/ae duyarsız, numara önce; tür, renk,
  marka, fiyat, durum, kategori + kategoriye özel filtreler; kategori sayıları; 120'lik sayfalar; 3.000 üründe
  < 200 ms). Ekran: arama, Alle/Physisch/Digital, çıkarılabilir filtre etiketleri, masaüstünde filtre sütunu +
  durum satırı + sağ detay paneli, telefonda alttan filtre paneli + detay sayfası, ızgara/liste. Filtreler adreste.
  `/produkt/{nr}` artık detay, düzenleme `/produkt/{nr}/bearbeiten`. Dilim 1'de her fiziki ürün „Ohne Platz“.
- Sıradaki: adım 7b (toplu düzenleme, D-012).
- Not: preview_start eski çalışma klasörünü görüyor. Dev sunucusu PowerShell Start-Process ile 8091'de; kapatırken
  portu dinleyen işlemi bul (venv python bir alt işlem açıyor).

## Dilim 1: adımlar
1. İskelet · 2. Görsel temel (token'lar, kabuk, logo) · 3. Sözlük (de) · 4. Migration 001 (kategori, filtre, ürün …)
5. Kategori ve filtre ayarları · 6. Tek kayıt · 7. Kütüphane (arama, filtreler) · 7b. Toplu düzenleme (D-012)
8. Seri kayıt · 9. Etiket PDF'i · 10. Systembereich (giriş, yedek, geri yükleme, toplu silme) · 11. Tekrar bak

## Offene Fragen
1. SPEC 11'deki açıklar: HTTPS yolu, etiket kâğıdı PDF'i, Drive uygulaması mini PC'de mi, de-AT terimleri, vurgu renkleri.
