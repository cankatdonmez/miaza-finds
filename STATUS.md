# STATUS

Stand: 04.11.2026 · v0.1.0 · SPEC 0.5 · Dal `dilim-3/bewegung` (Dilim 2 main'de; push yok)

## Aktueller Stand
- **Dilim 1** `main`de. Beta geri bildirimi 1 (D-014, D-015): masaüstü kamera + kamera seçimi, Option „+“, QR önizleme,
  `start.bat netz` ile QR ağ adresi, görsel boyutları ekrana göre.
- **Dilim 2 (Büro)** main'de; 212 test yeşil. Kararlar D-016 (Hier einordnen), D-017 (kapsam).
  - Migration 003: plan, raum, einheit, fach (kimlik asla yeniden kullanılmaz), `produkt.fach_id`.
  - `/plan` (Einstellungen › Büroplan): altlık (PDF/PNG/JPG, taşı/ölçekle/90°), oda ve ünite çizimi (sürükle = dikdörtgen,
    tıkla = poligon), oda ataması, geri al/yinele, kaydetmeden önce etki özeti.
  - `/plan/einheit/<id>`: ünite fotoğrafı, bölme çizimi, „Neu nummerieren“.
  - `/buero`: plan → ünite → bölme (spot ışığı) → ürünler; ünite listesi; telefonda ünite fotoğrafı.
  - Ürün detayı: Platz, „Im Büro zeigen“; „Hier einordnen“ modu (30 dk) + ürün sayfasında „In … einordnen“.
  - Fach-Etiketten (Etiketten › Fächer, QR `/f/<id>`), toplu düzenlemede „Platz“, durum filtresi Am Platz / Ohne Platz.
  - Geri bildirim (D-018): oda ve ünite yazıları şeklin içinde, okunur boyda; odalar 5 pastel tonda (numaradan).
  - D-019: dikdörtgen ünite sürüklenince duvara / komşuya yapışır, uzun kenarıyla döner, komşunun içine giremez (Alt: serbest).
  - D-020: bölmenin isteğe bağlı adı (Migration 004); Büro, ürün detayı, toplu düzenleme ve bölme etiketinde görünür.
  - D-021/D-022: ürün detayında „Platz ändern“ → Büro yer seçme modunda: plan → ünite → bölme → „Hier ablegen“, geri al.
  - D-023 tema (beyaz / antrasit, amber; `THEMA.md`), D-024 oda rengi seçilir, üniteler odanın tonunda (Migration 005),
    D-025 seçerek silme (Produkte · Kategorien · Büroplan · Nummern).
  - D-026: ünite fotoğrafında bölmeler demodaki gibi (etiket „kod · sayı“, kayan spot, nabız, önizleme).
  - D-027/28: foto eklenince kırpma; düzenlemede fotoğraflar „Speichern“e kadar taslak; seri sonrası „Speichern“.
  - D-029/D-030 (tasarım denetimi): kısa ürün formu, 44 px hedefler, geri al, tek ad „Verwerfen“, telefonda Einstellungen.
  - D-031: 14 ana renk (Mehrfarbig dahil) + kategoriye özel „Farbton“ filtresi; ayarlarda Farbkasten (sürükle-bırak).
  - D-033–35: etiket A4 3 × 8 ya da rulo 70 × 38 mm (QL-570, sayfa başına bir etiket); 3 mm kenar içinde sabit ızgara:
    „miaza“ | QR 26 mm (dikey orta) | geniş metin sütunu; Artikelnummer. D-036/37: Fach etiketinde oda/ünite/bölme ağaç gibi, alanı dolduruyor.
- Denenmedi: gerçek telefonda kamera, Docker, gerçek ofis planıyla uzun çizim.
- Dev: „dev“ `--reload`suz (Drive'da takılıyor); kod değişince sunucu yeniden başlatılır. Dev verisi `%USERPROFILE%\miaza-local\finds\data\dev.db`.

## Sıradaki
1. Dilim 3 (D-038): ~~kişiler + Bu cihaz~~ (Migration 008) → ~~Al/Yerine koy~~ (D-039) → ~~Okut~~ (D-040, D-041: HTTPS yokken kamera doğrudan) → ~~bölme onayı~~ (D-042, Migration 010 ayar) → ~~toplu yerleştirme~~ (D-043) → ~~„Wird bearbeitet“~~ (D-044). Dilim 3 tamam; D-045: bekleyen öneriler karara bağlandı. Gerçek telefon + canlı kamera denenmedi.
2. Cankat: gerçek dünya testi (etiket bas, telefonla okut); geri bildirim tek liste.
3. Kart yayı / yelpaze (D-017) Dilim 3'ten sonra, gerçek veriyle.

## Offene Fragen
1. QR'ın kalıcı adresi + HTTPS (Cankat bilgi verecek): öneri, bir alt alan adı (ör. `finds.miaza.design`) şimdiden
   `MF_BASIS_URL` olsun; DNS Wix ya da World4You'da kalabilir, sertifika „DNS alias mode“ ile. Sonra teknisyen belgesi güncellenir.
2. Mini PC kurulumu: teknisyen belgesi https://claude.ai/artifact/KtCQDEkSQeHfcE4NGtbAoW (denenmedi).
3. SPEC 11: Drive uygulaması mini PC'de mi, de-AT terimleri („Bibliothek“ adı); counts'un vurgu rengi (finds: amber).
