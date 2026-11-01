# STATUS

Stand: 01.11.2026 · v0.1.0 · SPEC 0.5 · Dal `dilim-1/grundgeruest`

## Aktueller Stand
- Dilim 1 (Kütüphane ve kayıt) başladı. Kararlar D-001–D-012.
- Adım 1–3 bitti (25 test yeşil): iskelet; token'lar (açık/koyu), Figtree/Plex Mono, kabuk (telefonda alt
  leiste, ≥ 900 px'te kenar çubuğu), logo, Einstellungen › Darstellung; sözlük `app/texte.py` + `t()`.
  Ekranda denendi: açık, koyu, 375 px, yatay kayma yok. Docker ve start.bat henüz denenmedi.
- Adım 4 bitti (40 test): migration 001 (kategori + sabit „Sonstiges“/XX, filtre ve seçenekleri, ürün, filtre
  değerleri, renk, fiyat, fotoğraf, envanter sayacı) ve `services/nummern.py` (kod KK-KKK-EEE, numara tekrar verilmez).
- Sıradaki: adım 5 (kategori ve filtre ayarları: API + masaüstü ekranı).
- Not: preview_start eski çalışma klasörünü görüyor; dev sunucusu şimdilik Bash ile 8091'de açılıyor.

## Dilim 1: adımlar
1. İskelet · 2. Görsel temel (token'lar, kabuk, logo) · 3. Sözlük (de) · 4. Migration 001 (kategori, filtre, ürün …)
5. Kategori ve filtre ayarları · 6. Tek kayıt · 7. Kütüphane (arama, filtreler) · 7b. Toplu düzenleme (D-012)
8. Seri kayıt · 9. Etiket PDF'i · 10. Systembereich (giriş, yedek, geri yükleme, toplu silme) · 11. Tekrar bak

## Offene Fragen
1. SPEC 11'deki açıklar: HTTPS yolu, etiket kâğıdı PDF'i, Drive uygulaması mini PC'de mi, de-AT terimleri, vurgu renkleri.
