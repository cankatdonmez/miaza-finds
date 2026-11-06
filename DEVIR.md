# DEVIR — miaza finds (devir paketi, 06.11.2026; D-049'dan sonra güncellendi)

Bu paket, projeyi bu sohbeti görmeden devralacak oturum içindir. Dört dosya birlikte okunur:
**DEVIR.md** (bu dosya: ne var, nerede, ne kadar bitti) · **KARARLAR.md** (verilen bütün kararlar, özellikle dosyalarda
yazmayanlar) · **DURUM.md** (hatalar, açık sorular, testler, borç, sıradaki adımlar) · **CALISMA-TARZI.md** (Cankat nasıl
çalışmak istiyor). Ayrıca her oturumun başında `CLAUDE.md` ve `STATUS.md` okunur (CLAUDE.md'nin kuralı).

Kaynak önceliği: kararlar için `DECISIONS.md` (D-001 … D-048), ne yapılacağı için `SPEC.md` (0.5), anlık durum için
`STATUS.md`. Bu paket onları özetler ve aralarındaki çelişkileri gösterir; onların yerini almaz.

---

## 1. Amaç ve kapsam

- **miaza finds**, mimarlık bürosu „miaza“nın malzeme kütüphanesi ve ofis düzeni uygulamasıdır (fayans, ahşap, metal,
  kumaş, taş numuneleri; fiziki ve yalnız dijital ürünler).
- İki eşit ana işlev (SPEC 1): **Kütüphane** (hızlı arama/filtre) ve **Ofis organizasyonu** (her fiziki ürünün yeri,
  bulma, alma, yerine koyma).
- 4–5 kişilik büro, **kullanıcı girişi yok** (yalnız şifreli Systembereich, SPEC 6.13). Büronun mini PC'sinde çalışır,
  yalnız ofis ağından erişilir. Telefon (okutma, fotoğraf, alma/koyma) ve masaüstü (arama, plan çizimi, ayarlar, etiket).
- Arayüz **Almanca**, kullanıcıyla konuşma **Türkçe**. Para birimi Euro, saat dilimi Europe/Vienna.
- Aile uygulaması: **miaza counts** (Zeiterfassung, `C:\Users\canka\Documents\Zeiterfassung`) ile aynı altyapı,
  yazı sistemi ve görünüm. Portlar: counts 8080/8081, finds **8090 (beta) / 8091 (geliştirme)**.
- Sürüm planı: v1 dört „dilim“de (CLAUDE.md): 1 Kütüphane+kayıt, 2 Ofis, 3 Hareket, 4 Kalanlar. v2 listesi SPEC 10'da.
- Depo dışı bir şey yoktur: bulut servisi yok (SPEC 8.5); tek istisna en sona bırakılan „Linkten doldurma“ (D-048).

---

## 2. Dosya haritası

### Proje klasörü: `C:\Users\canka\Documents\miaza-finds` (GitHub: `cankatdonmez/miaza-finds`, private)

Google Drive artık kullanılmıyor (D-049). Eski Drive klasörü (`G:\.shortcut-targets-by-id\…\Miaza Apps\miaza finds`)
yalnız yedek; orada çalışılmaz.

| Yol | Ne |
|---|---|
| `CLAUDE.md` | Çalışma notları ve kurallar. Her oturumda ilk okunur. |
| `STATUS.md` | Anlık durum, < 40 satır (06.11.2026'da güncellendi). |
| `SPEC.md` | Ürün spesifikasyonu 0.5 (Türkçe). Ne yapılacağının tek kaynağı. 12 bölüm. |
| `DECISIONS.md` | Karar günlüğü D-001…D-048. D-046 ve D-047 Almanca yazılmış (başka oturum), diğerleri Türkçe. |
| `DESIGN-PRINCIPLES.md` | Tasarım ilkeleri, kontrol listesi, karar tablosu. |
| `THEMA.md` | Renk tokenları (açık: beyaz, koyu: antrasit, vurgu amber), durum renkleri, oda renkleri; counts için yol. |
| `DEGERLENDIRME-0.3.md` | SPEC 0.4'ü doğuran dört aşamalı değerlendirme (tarihî). |
| `DEVIR.md`, `KARARLAR.md`, `DURUM.md`, `CALISMA-TARZI.md` | Bu devir paketi. |
| `start.bat` | Windows'ta beta sunucusu: `.venv`'i kurar/günceller, 8090'da başlatır; `start.bat netz` ağa açar (0.0.0.0, QR'da ağ adresi). Eski 8090 sürecini kapatır. |
| `Dockerfile`, `docker-compose.yml` | Docker yolu (D-003). **Hiç denenmedi.** Dockerfile `python:3.13-slim`. |
| `requirements.txt`, `requirements-dev.txt` | Sabit sürümlü bağımlılıklar (aşağıda). |
| `pytest.ini` | `-p no:cacheprovider` (Drive'a önbellek yazmasın), `testpaths = tests`. |
| `.claude/launch.json` | Geliştirme sunucusu „dev“: 127.0.0.1:8091, `dev.db`, `media-dev`, `--reload` yok. |
| `.git` | Normal git klasörü (06.11.2026'da yerel depodan klonlandı). `origin` = GitHub. |
| `_oturum/oturum-2026-11-01.zip` | 01.11 oturumunun arşivi (`.gitignore`'da, yalnız yerelde; Drive'dan kopyalandı). İçeriği incelenmedi (BİLİNMİYOR). |
| `demo/` | Tıklanabilir demo (`*.dc.html`, SPEC 0.3 düzeyinde), ofis planı PDF'i, `test-harness.html`. |
| `demo/EKRANLAR.md`, `demo/ekranlar/*.png` | Demo ekran görüntüleri (33 PNG) ve açıklaması. **Git'e eklenmemiş** (untracked); Drive'dan kopyalandı. Kim/ne zaman ekledi BİLİNMİYOR (dosya 02.11.2026 tarihli olduğunu söylüyor). |

### Uygulama kodu: `app/`

| Yol | Ne |
|---|---|
| `main.py` | FastAPI fabrikası `create_app(db_path, media_dir, sicherung_dir)`: migration, router'lar, güvenlik başlıkları, köken kontrolü (D-007), `app.state` (bearbeitung, sammel_vorher). |
| `config.py` | Ortam değişkenleri `MF_*`: `MF_DB_PATH`, `MF_MEDIA_DIR`, `MF_BACKUP_DIR`, `MF_TIMEZONE`, `MF_BASIS_URL`, `MF_NETZ`, `MF_SECURE_COOKIES`, `MF_LOKAL_DIR`. |
| `db.py` | SQLite (WAL, foreign_keys), migration çalıştırıcı, `transaction`. |
| `texte.py` | Bütün arayüz metinleri (Almanca sözlük `DE`), `t(anahtar, **değerler)`. |
| `zeit.py` | `heute()`, `jetzt()` (Viyana saati). |
| `fehler.py` | `Fehler(text, feld, status)` → `{"fehler": {...}}`. |
| `version.py` | `VERSION = "0.3.0"` (0.\<biten dilim\>.\<düzeltme\>; 06.11.2026'da 0.1.0'dan güncellendi). |
| `etikett_bogen.json` / `etikett_rolle.json` | Etiket kâğıdı tanımları: A4 3×8 (69,5×36,84 mm) ve rulo 70×38 mm (QL-570). |
| `migrations/001…011.sql` | Şema: 001 kütüphane, 002 system, 003 büro, 004 fach.name, 005 raum.farbe, 006 farben, 007 artikelnummer, 008 personen, 009 entnahme, 010 einstellung, 011 sammlungen. Yalnız eklenir, yayımlanmış dosya değişmez (`migrations/README.md`). |
| `routes/pages.py` | HTML sayfaları, menüler (`MENUE_DESKTOP`, `MENUE_TELEFON`), `/p/<nr>` → ürün, `/f/<id>` → büro. |
| `routes/api_*.py` | JSON API: bibliothek, produkte, kategorien, plan, etiketten, system, personen, entnahme, einstellungen, bearbeitung, sammlungen. |
| `services/*.py` | İş kuralları: `produkte`, `bibliothek` (arama/filtre/sayaçlar), `suche` (normalleştirme), `kategorien`, `plan` (plan, ünite, fach, yer), `etiketten` (PDF/PNG etiket), `fotos`, `sammel` (toplu düzenleme), `sicherung` (yedek/geri yükleme/taşıma/silme), `verwalter` (Systembereich girişi), `nummern` (ürün kodu), `personen`, `entnahme` (al/koy/yerleştir), `einstellungen` (büro ayarları), `bearbeitung` („Wird bearbeitet“, bellekte), `sammlungen`. |
| `templates/*.html` | Jinja2: `base`, `shell` (menüler), sayfalar (bibliothek, detail, produkt, buero, plan, fach, etiketten, einstellungen, system, scannen, statistik, mehr, sammlungen, 404), `_icons.html` (SVG semboller), `_macros.html`. |
| `static/css/app.css` | Tek CSS; tokenlar üstte, `/* ---------- Ende der Token ---------- */` sonrasında ham renk yasak (test_stil). |
| `static/js/*.js` | Düz JS, build yok. `common.js` (MF: api, toast, t, icon, einordnen modu, geraetPerson), `scan.js` (QR kuralları, jsQR tembel yükleme, foto yolu), `bearbeitung.js`, `entnahme.js`, `detail.js`, `bibliothek.js`, `produkt.js`, `serie.js`, `zuschnitt.js`, `buero.js`, `plan-editor.js`, `fach-editor.js`, `zeichnen.js`, `etiketten.js`, `scannen.js`, `kategorien.js`, `personen.js`, `einstellungen.js`, `sammel.js`, `sammlungen.js`, `system.js`, `theme.js`, `detail-seite.js`. |
| `static/vendor/jsQR.js` | jsQR 1.4.0 (Apache-2.0, `jsQR-LICENSE.txt`), npm'den, bütünlüğü doğrulandı (D-040). |
| `assets/fonts/` | Figtree, IBM Plex Mono, Comfortaa SemiBold (etiketteki „miaza“), OFL lisansları. |

### Testler: `tests/` (pytest, 21 dosya, **219 test**, hepsi geçiyor — 06.11.2026)
`conftest.py` (geçici veritabanıyla `client`), `test_grundgeruest` (başlıklar, köken), `test_bibliothek`, `test_produkte`,
`test_serie`, `test_sammel`, `test_kategorien`, `test_farben`, `test_plan`, `test_etiketten`, `test_system`,
`test_personen`, `test_entnahme`, `test_bearbeitung`, `test_sammlungen`, `test_seiten`, `test_stil` (CSS/ikon kuralları),
`test_migration_001/003/004/005`. Migration 006–011'in testleri ilgili konu dosyalarında.

### Drive dışındaki yerel klasör: `C:\Users\canka\miaza-local\finds\` (D-008)

| Yol | Ne |
|---|---|
| `.venv\` | Python ortamı (3.14.5). |
| `data\finds.db` | **Gerçek/beta veritabanı** (8090). İçinde 17 Verano ürünü + önceki ürünler var (bkz. KARARLAR.md). |
| `data\dev.db` | Geliştirme veritabanı (8091): deneme verisi, Verano kopyası, kişiler Cankat/Murat Y./Selin. |
| `media\`, `media-dev\` | Fotoğraflar ve plan altlığı (beta / dev). |
| `backups\` | Systembereich yedekleri (.zip). |
| `import\verano\` | Ege Seramik'ten indirilen Verano fotoğrafları (içe aktarma kaynağı). |
| `git\` | **Eski** git deposu (Drive dönemi, 04–06.11). Yedek olarak duruyor; artık kullanılmıyor. |
| `wt-sammlungen\` | Başka bir oturumun açtığı worktree (eski depoya bağlı, dal `sammlungen`, main'e birleşmiş). Cankat „kalsın“ dedi. |

---

## 3. Teknik ortam

- **Python:** venv'de 3.14.5. SPEC 8.1 „3.12+“ diyor; Dockerfile 3.13. `start.bat` sistemde `py -3`/`python` arar.
- **Bağımlılıklar (requirements.txt, sabit):** fastapi 0.142.2, uvicorn 0.53.0, jinja2 3.1.6, python-multipart 0.0.32,
  argon2-cffi 25.1.0, openpyxl 3.1.5 (**şu an kullanılmıyor**, v2 Excel için), reportlab 5.0.1, pypdf 5.9.0,
  pypdfium2 5.14.0, pillow 13.0.0, segno 1.6.6, tzdata 2026.5. Geliştirme: pytest 9.2.0, httpx 0.28.1.
- **Ön yüz:** düz JS + tek CSS; build yok; dış CDN yok; jsQR 1.4.0 uygulamayla gelir.
- **Testler:**
  ```
  %USERPROFILE%\miaza-local\finds\.venv\Scripts\python -m pytest -q
  ```
  (Bash'te: `"$USERPROFILE/miaza-local/finds/.venv/Scripts/python" -m pytest -q`. ~30–45 sn.)
- **Geliştirme sunucusu:** Claude masaüstünde `preview_start "dev"` (8091, `dev.db`). `--reload` yok: **her kod
  değişikliğinden sonra sunucu yeniden başlatılır**, yoksa tarayıcı eski JS/CSS'i görür (asset sürüm karması başlangıçta
  hesaplanır).
- **Beta sunucusu:** `start.bat` (127.0.0.1:8090) ya da `start.bat netz` (ağa açık). Cankat kendisi başlatır/kapatır.
- **Mini PC (henüz kurulmadı):** Windows. Teknisyen belgesi (Almanca) Claude Docs'ta:
  https://claude.ai/artifact/KtCQDEkSQeHfcE4NGtbAoW — sabit IP, `MF_BASIS_URL`, güvenlik duvarı, Görev Zamanlayıcı ile
  `start.bat netz`, QL-570 sürücüsü (38×70 mm, her etiketten sonra kes), yedek. **Hiç denenmedi.**
- **Git:** depo `C:\Users\canka\Documents\miaza-finds\.git`, `origin` = https://github.com/cankatdonmez/miaza-finds
  (private). `main` GitHub'dan önde (push yapılmadı). Push ve main'e birleştirme yalnız Cankat isteyince. Commit yazarı
  `Cankat Dönmez <cankatdonmez@gmail.com>`, sonuna `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Etiket yazıcısı:** Brother QL-570, rulo DK-22225 (38 mm). Uygulama her etiketi bir PDF sayfası (70×38) üretir.
- **Bash ortamında** `gh` ve `node` yok. Claude'un geçici klasörünün yolu uzun: Windows 260 karakter sınırına dikkat.

---

## 4. SPEC ile kod karşılaştırması

### 4a. SPEC'te olup kodda olmayanlar (v1 kapsamında)

| SPEC | Eksik | Kanıt |
|---|---|---|
| 4.1, 10 | **Açılış ekranı** (soğuk açılışta ≤ 700 ms, dokununca geçer) | `app/static/js`, `templates` içinde yok (aranan: splash/700/açılış). |
| 4.3 | Kat planı **altlığı koyu temada ters çevrilmiş ve soluk** | `app.css` `.unterlage{opacity:.35}`; `invert` yok. |
| 4.7 | **Kart yayı** (ünite çevresinde) ve **yelpaze** (bölme kartları), deste/+N; **fareyle önizleme** (ünite üstünde küçük önizleme, ~300 ms) | `buero.js`'te yok; D-017 bilerek ertelendi („Tekrar bak“ adımında gerçek veriyle). |
| 6.1 | Aramada **bölme kodu** („2.2“) ve „seri“ | `produkte.suchtext_erneuern` ad, marka, Artikelnummer, ölçü, kategori, kod, envanter no ve filtre değerlerini alıyor; **fach kodu yok**. |
| 6.1 | Masaüstünde **karta gelince konum kodu**, tıklayınca planda göster | `bibliothek.js` kart şablonunda yok. |
| 6.9, 10 | **Dokümanlar** (kök klasör, göreli yol, aç, „bulunamadı“) | Servis/route/migration yok (D-004: dilim 4'te). |
| 8.4, 10 | **Gece yedeği** — **bilerek bekletiliyor** (D-049: uygulama belli bir noktaya gelince konuşulacak) | Zamanlayıcı yok. Elle yedek Systembereich'te var (`api_system` `/sicherung`). |
| 6.11 | Ayarlar › Genel: **doküman kök klasörü**, **yedek durumu** | `einstellungen.html`'de yok. |
| 10 | **Almanca son okuma** (terimler, de-AT biçimleri) | Yapılmadı; SPEC 11.5 açık. |

### 4b. Kodda olup SPEC'te olmayan (ya da yalnız DECISIONS'ta olan)

- Rulo etiket 70×38 (D-035), etiket düzeni ayrıntıları (D-033/34/36/37): SPEC 6.6'da var, ama SPEC 10 hâlâ „A4 etiket PDF'i (20'li)“ diyor.
- Büro geneli ayar tablosu `einstellung` (Migration 010) ve `/api/einstellungen` (D-042) — SPEC 7 „Ayarlar“ satırı genel.
- Cihaz kimliği `localStorage mf-geraet` („Wird bearbeitet“, D-044) ve `mf-person`, `mf-kamera`, `mf-etikett-format`, `mf-einordnen`, `mf-theme`.
- Einordnen ekranı `/scannen?fach=<id>` (D-043), Scannen foto geri bildirim katmanı (D-041).
- `/api/produkte/{nr}/einordnen` (alınmış ürünü yerleştirince geri konmuş sayar, D-043/D-045).
- Kişi „gizleme“ (`person.entfernt_am`) ve koleksiyon gizleme (`sammlung.entfernt_am`).
- Etiket önizlemesi PNG (`/api/etiketten/vorschau/...`), pdfium kilidi (paralel çizim hatası için).

### 4c. Çelişenler

**D-049 ile giderilenler (06.11.2026):** SPEC 10 „20'li etiket“ → A4 24'lü + 38 mm rulo; SPEC 11.3 kapatıldı;
SPEC 12 „oda renkleri yok“ kaldırıldı; SPEC 8.3/8.4 ve DESIGN-PRINCIPLES klasör yolları Windows'a göre; `version.py` 0.3.0;
STATUS.md güncel. Kalanlar:

| Konu | SPEC | Gerçek | Not |
|---|---|---|---|
| Telefon menüsü | 4.5'in ilk cümlesi Koleksiyonlar'ı alt menüde sayıyor | Aynı maddenin sonu (D-047) ve kod: Bibliothek · Büro · Scannen · Mehr; Sammlungen „Mehr“ içinde | Madde kendi içinde iki hâli anlatıyor; geçerli olan D-047. |
| Python | 8.1: 3.12+ | venv 3.14.5, Dockerfile 3.13 | Çalışıyor; Docker ile venv aynı değil. |
| Fach etiketi alt metni | D-020: „bölmenin adı, yoksa ünitenin adı“ | D-036/37: oda/ünite/bölme ağaç | D-036 D-020'yi değiştirdi; SPEC 6.6 güncel. Etiketten listesindeki alt satır hâlâ D-020 kuralıyla. |

---

## 5. Adım durumu

„PLAN“ adında ayrı bir dosya yok. Plan = CLAUDE.md'deki 4 dilim + SPEC 10'daki v1 listesi. Aşağıda SPEC 10 v1
maddeleri (13 madde) ve dilim 4'ün kendi sırası (D-046). Kanıt: dosya / fonksiyon / test.

### SPEC 10, v1

| # | Madde | Durum | Kanıt |
|---|---|---|---|
| 1 | Marka, kısa açılış ekranı, açık/koyu tema | **KISMEN** | Marka: `_macros.html marke()`; tema: `theme.js`, `einstellungen.js` (Sistem/Hell/Dunkel), `THEMA.md`, `test_stil.test_dunkles_thema_definiert_jedes_farbtoken`. Açılış ekranı yok. |
| 2 | Kütüphane: arama, ortak + kategoriye özel filtreler, durum filtresi, ızgara/liste, durum satırı | **KISMEN** | `services/bibliothek.py` (`_bedingungen`, `_status_bedingung`, `zaehler`), `bibliothek.js`, `test_bibliothek` (11), `test_entnahme` durum filtreleri. Eksik: aramada fach kodu, kartta hover'da konum kodu. |
| 3 | Ürün kaydı: tek + seri kayıt, kod şeması, fiyat+tarih, elle renk, dokümanlar, foto çek/seç, silme | **KISMEN** | `services/produkte.py` (`anlegen`, `aendern`, `_preis_speichern`, `loeschen`), `nummern.py`, `fotos.py`, `zuschnitt.js` (D-027/D-045), `serie.js`, `test_produkte` (17), `test_serie` (4). **Dokümanlar yok.** |
| 4 | Kategori ve filtre yönetimi | **TAMAM** | `services/kategorien.py`, `kategorien.js` (Farbkasten D-031/32), `test_kategorien` (13), `test_farben` (5). |
| 5 | Kat planı düzenleyici (oda, ünite, bölme, taslak, geri al, kaydet, altlık, kaydırma/yakınlaştırma) | **KISMEN** | `services/plan.py`, `plan-editor.js`, `fach-editor.js`, `zeichnen.js`, `test_plan` (18). Eksik: koyu temada altlığın ters gösterimi (SPEC 4.3). Gerçek ofis planıyla uzun çizim denenmedi. |
| 6 | Ofis görünümü ve dört konum senaryosu | **KISMEN** | `buero.js` (plan → ünite → bölme spotu → ürünler; `?fach=&produkt=`; D-045 rafı önce gösterir), `/f/<id>`. Kart yayı/yelpaze ve fareyle önizleme yok (D-017 erteledi). |
| 7 | Ürün ve bölme QR'ları; etiket PDF'i | **TAMAM** | `services/etiketten.py` (`pdf`, `fach_pdf`, `_etikett`, `_fach_zeichnen`, `_ort_satz`), `etiketten.js`, `test_etiketten` (16). Gerçek QL-570'te uygulamadan basılmadı (Cankat'ın PDF ile deneme baskısı çalıştı, D-035). |
| 8 | Okut (telefon ana menü, masaüstü ikon) | **TAMAM** (gerçek telefonda denenmedi) | `scan.js` (`ziel`, `lesen`, `foto`, `kamera`), `scannen.js`, `templates/scannen.html`, `test_seiten.test_scannen_mit_eigenem_qr_leser`. |
| 9 | Alma / yerine koyma, bölme onayı, toplu yerleştirme | **TAMAM** (gerçek telefonda denenmedi) | `services/entnahme.py` (`nehmen`, `zuruecklegen`, `einordnen`, geri alma), `entnahme.js`, `scannen.js` einordnen modu, `test_entnahme` (9). |
| 10 | „Düzenleniyor“ uyarısı ve sürüm kontrolü | **TAMAM** (iki gerçek cihazla denenmedi) | `services/bearbeitung.py`, `bearbeitung.js` (ürün formu, plan, fach, kategori), `test_bearbeitung` (4); sürüm kontrolü dilim 1/2'den. |
| 11 | Koleksiyonlar (miktarsız) | **TAMAM** (başka oturum yaptı; bu oturumda gözden geçirilmedi) | `services/sammlungen.py`, `api_sammlungen.py`, `sammlungen.js`, Migration 011, `test_sammlungen` (7). |
| 12 | İstatistik, kişiler, gece yedeği (gece yedeği D-049 ile bekletiliyor) | **KISMEN** | İstatistik: `pages.py` `/statistik`, `templates/statistik.html`, `test_seiten` (başka oturum, gözden geçirilmedi). Kişiler: `services/personen.py`, `personen.js`, `test_personen` (4). **Gece yedeği yok.** |
| 13 | Almanca arayüz | **KISMEN** | Bütün metinler `texte.py`'de Almanca. Son okuma ve de-AT kararı yapılmadı (SPEC 11.5). |

**Sayım:** 13 maddenin **6'sı TAMAM** (4, 7, 8, 9, 10, 11), **7'si KISMEN** (1, 2, 3, 5, 6, 12, 13), **0'ı BAŞLANMADI**.
TAMAM olanların 3'ü (8, 9, 10) gerçek cihazda hiç denenmedi.

### Dilimler (CLAUDE.md)

| Dilim | Durum | Kanıt |
|---|---|---|
| 1 Kütüphane ve kayıt, Systembereich | **TAMAM** (açılış ekranı ve dokümanlar hariç; dokümanlar D-004 ile dilim 4'e alındı) | `main`, `test_system` (15) yedek/geri yükleme/taşıma/seçerek silme. |
| 2 Ofis | **TAMAM** (kart yayı/yelpaze D-017 ile ertelendi) | Birleştirme commit'i `de712fb` (04.11.2026). |
| 3 Hareket | **TAMAM** | Birleştirme commit'i `307ebb7` (04.11.2026); D-038…D-045. |
| 4 Kalanlar (sıra D-046: Statistik → Sammlungen → Dokumente → Nachtsicherung → Almanca son okuma) | **KISMEN**: 5 adımdan 2'si bitti | Statistik `6a147d7`, Sammlungen `bdd2921`. Dokumente, Nachtsicherung, Almanca son okuma **BAŞLANMADI**. |

### v2 (SPEC 10) — hepsi BAŞLANMADI
Sipariş listesi; fotoğraftan otomatik renk; QL-570'e uygulamadan doğrudan baskı; fiyat geçmişi; „Klasörde göster“;
en son „Linkten doldurma“ (D-048).

---

## 6. Dürüst ilerleme tahmini (sayarak)

- v1'in 13 maddesinden 6'sı tamam, 7'si kısmen. Kısmen olanlarda kalan iş: açılış ekranı (1), aramada fach kodu ve
  kartta konum kodu (2), dokümanlar (3), koyu temada altlık (5), kart yayı/yelpaze + fareyle önizleme (6),
  gece yedeği (12), Almanca son okuma (13). Yani **v1'e 9 somut iş parçası** kalmış görünüyor (dokümanlar ve gece yedeği
  büyük, açılış ekranı ve koyu altlık küçük).
- Dilim 4'ün 5 adımından 2'si bitti.
- Bunlara ek olarak v1'i gerçek hayata çıkarmak için yapılmamış **kurulum işleri**: mini PC kurulumu, kalıcı QR adresi
  (`MF_BASIS_URL`) ve HTTPS kararı, gerçek telefonda uçtan uca deneme. Cankat'ın kararı (D-049): bunlar ve gece yedeği
  uygulama tamamlanıp sunucuya kurulurken konuşulur; o zamana kadarki bütün veri ve QR'lar demo.
