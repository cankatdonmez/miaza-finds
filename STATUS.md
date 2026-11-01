# STATUS

Stand: 02.11.2026 · v0.1.0 · SPEC 0.5 · Dal `dilim-1/grundgeruest` (push yok, main'e birleştirilmedi)

## Aktueller Stand
- **Dilim 1 (Kütüphane ve kayıt) bitti**, 148 test yeşil. Kararlar D-001–D-013. Ayrıntılar: `git log`.
- İçerik: kategori/filtre ayarları · tek kayıt (fotoğraf, filtre değerleri, fiyat, renk, silme) · kütüphane (arama,
  filtreler, ızgara/liste, detay paneli) · toplu düzenleme · telefonda seri kayıt + adları listede tamamlama ·
  etiket sayfası + A4 PDF · Systembereich (yönetici, güvenlik anahtarı, yedek, geri yükleme, veri taşıma, toplu silme).
- Adım 11 (Tekrar bak): metinlerde tek ad („Option“ filtre seçeneği, „Auswahl“ yalnız seçim), du-hitap, tekil
  biçimler (`_eins`); dokunma alanları ≥ 44 px; kontrast açık/koyu ≥ 5,2:1; 375 px'te yana kayma yok.
- Denenmedi: Docker, `start.bat` ilk kurulum (Cankat'ın bilgisayarında 8090 çalışıyor görünüyor), gerçek telefonda kamera.
- Dev: sunucu PowerShell Start-Process ile 8091'de (preview_start eski klasörü görüyor); kapatırken portu dinleyen
  işlemi ve alt işlemini bul. Dev verisi `%USERPROFILE%\miaza-local\finds\data\dev.db`.

## Sıradaki
1. Cankat: beta'yı (`start.bat`) dene, geri bildirimi tek liste halinde ver; Systembereich'i kendisi kursun.
2. Dal `dilim-1/grundgeruest` → `main` birleştirme (Cankat onaylayınca).
3. Dilim 2 (Ofis): plan düzenleyici, üniteler, bölmeler, bölme etiketleri, bölme QR'ıyla toplu yerleştirme.

## Offene Fragen
1. Etiket QR'ının kalıcı adresi (mini PC'nin ofis adresi veya HTTPS alan adı) → `MF_BASIS_URL`. Basılı etiketler buna bağlı.
2. Etiket kâğıdının düzen PDF'i → `app/etikett_bogen.json` (şimdilik geçici 20'li, 48 × 52 mm).
3. SPEC 11: HTTPS yolu, Drive uygulaması mini PC'de mi, de-AT terimleri („Bibliothek“ adı), vurgu renkleri.
