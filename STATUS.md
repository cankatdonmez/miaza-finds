# STATUS

Stand: 01.11.2026 · v0.1.0 · SPEC 0.5 · Dal `dilim-1/grundgeruest`

## Aktueller Stand
- Dilim 1 (Kütüphane ve kayıt) başladı. Kararlar D-001–D-008.
- Adım 1 (iskelet) bitti: create_app, db/migrate (yedekli), Origin koruması, config (MF_), 13 test yeşil,
  Docker + start.bat (8090), launch.json (8091). Docker henüz denenmedi. Sıradaki: adım 2 (görsel temel).

## Dilim 1: adımlar
1. İskelet · 2. Görsel temel (token'lar, kabuk, logo) · 3. Sözlük (de) · 4. Migration 001 (kategori, filtre, ürün …)
5. Kategori ve filtre ayarları · 6. Tek kayıt · 7. Kütüphane (arama, filtreler) · 8. Seri kayıt
9. Etiket PDF'i · 10. Systembereich (giriş, yedek, geri yükleme, toplu silme) · 11. Tekrar bak

## Offene Fragen
1. Systembereich: şifre unutulursa? (öneri: counts gibi Recovery Key)
2. Systembereich: "yeni veri kümesi" hangi biçimde gelir? (öneri: finds'in kendi yedek dosyası; Excel ancak ihtiyaç olursa)
3. SPEC 11'deki açıklar: HTTPS yolu, etiket kâğıdı PDF'i, Drive uygulaması mini PC'de mi, de-AT terimleri, vurgu renkleri.
