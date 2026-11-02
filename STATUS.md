# STATUS

Stand: 02.11.2026 · v0.1.0 · SPEC 0.5 · Dal `dilim-2/buero` (main'e birleştirilmedi, push yok)

## Aktueller Stand
- **Dilim 1** `main`de. Beta geri bildirimi 1 (D-014, D-015): masaüstü kamera + kamera seçimi, Option „+“, QR önizleme,
  `start.bat netz` ile QR ağ adresi, görsel boyutları ekrana göre.
- **Dilim 2 (Büro)** dalda, 179 test yeşil. Kararlar D-016 (Hier einordnen), D-017 (kapsam).
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
  - D-027: tek fotoğraf eklenince kırpma ekranı (tek ve seri kayıt); yüklenmemiş fotoğrafta kırpma düğmesi.
  - D-028: düzenlemede fotoğraflar „Speichern“e kadar taslak; seri sonrası ad listesinde „Speichern“; kartlar hep kare.
  - D-029 (tasarım denetimi): kısa ürün formu („Weitere Angaben“), çipler 44 px, onay penceresi yerine geri al /
    „Wirklich verwerfen?“, her yerde „Verwerfen“, telefonda „Mehr“ yerine Einstellungen.
- Denenmedi: gerçek telefonda kamera, Docker, gerçek ofis planıyla uzun çizim.
- Dev: `.claude/launch.json` „dev“ artık `--reload`suz (Drive klasöründe yeniden yükleme takılıyordu); kod değişince
  sunucu yeniden başlatılır. Dev verisi `%USERPROFILE%\miaza-local\finds\data\dev.db`.

## Sıradaki
1. Cankat: Dilim 2'yi dev'de ya da birleştirdikten sonra beta'da dene; geri bildirim tek liste.
2. Kart yayı / yelpaze animasyonları (D-017) gerçek veriyle.
3. Dilim 3 (Hareket): uygulama içi tarayıcı, alma / yerine koyma, „Düzenleniyor“.

## Offene Fragen
1. Etiket QR'ının kalıcı adresi → `MF_BASIS_URL`. Basılı etiketler buna bağlı.
2. Etiket kâğıdının düzen PDF'i → `app/etikett_bogen.json` (şimdilik geçici 20'li, 48 × 52 mm).
3. HTTPS: alan adı `miaza.design`, DNS Wix'te (API yok) → yol A için alt alan API'li bir DNS servisine devredilmeli.
4. SPEC 11: Drive uygulaması mini PC'de mi, de-AT terimleri („Bibliothek“ adı); counts'un vurgu rengi (finds: amber).
