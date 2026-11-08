# TEST_RAPORU — miaza finds

Denetçi yazar. Her PLAN adımı için bir bölüm; en yenisi üstte. Kod değiştirilmez, yalnız rapor.
**Çalıştırılan** ile **yalnız okunarak incelenen** ve **hiç denenmeyen** ayrı yazılır. Denenmeyen şey „denendi“ diye yazılmaz.

Başlangıç durumu (07.11.2026, `pre-multiagent` etiketi): 219 test yeşil. Önceki elle denemeler ve hiç denenmeyenler: `DURUM.md` §3.

---

## Adım 3 — Koyu temada plan altlığı · 09.11.2026 · dilim-4/unterlage-dunkel @ f8da8d9 · deneme 1
**Sonuç:** GEÇTİ (K1–K3 karşılandı; gözlemler aşağıda)

**pytest (çalıştırıldı, tüm takım):** `230 passed in 32.50s`.
**Fark (okundu):** 3 dosya: `app/static/css/app.css` (token `--unterlage-filter/-deckkraft/-deckkraft-aktiv`, `.unterlage` kuralı), `tests/test_stil.py` (yeni test), `PLAN.md` (durum). Kapsam dışı değişiklik yok; JS/şablon/metin değişmedi (`texte.py` ilgisiz); yeni ham renk yok (filtre ve opaklık tokenlarda).

**Hazırlık (çalıştırıldı):** dev.db planında altlık vardı (`unterlage` dolu) ama `unterlage_im_buero=false`; plan düzenleyicide „Unterlage im Büro zeigen“ açılıp kaydedildi (yalnız dev.db). Beta/finds.db'ye dokunulmadı.

| Kriter | Sonuç | Kanıt |
|---|---|---|
| K1 koyu: ters çevrilmiş, soluk (Büro + editör) | geçti | Çalıştırıldı. Hesaplanan stil: Sistem+koyu, elle Dunkel (sistem koyu ve açık), `filter: invert(1) hue-rotate(180deg)`, opaklık 0,30 (normal) / 0,55 (Unterlage aracı seçili, sınıf `unterlage aktiv`). Hem `/buero` hem `/plan` ekran görüntüsü alındı. |
| K2 açık değişmez | geçti | Çalıştırıldı: Sistem hell, elle Hell (sistem koyu iken de) → `filter: none`, 0,35 / 0,6 = main'deki eski değerler (diff'te de okundu). Ekran görüntüleri açık görünümü gösteriyor. |
| K3 token/tema seçicisi, yenilemesiz | geçti | Okundu + çalıştırıldı: kural `:root`, `[data-theme="dark"]` ve `prefers-color-scheme` bloklarında token; `.unterlage` yalnız `var()` kullanır; yeni test bunu kontrol eder. Aynı sayfada `data-theme` özniteliği JS ile değiştirilince (einstellungen.js'in yaptığı aynı işlem) sayfa yenilenmeden filtre/opaklık değişti (dark→light→sistem). Sistem koyu/açık geçişi `resize_window colorScheme` ile sayfa yenilemeden de denendi (hesaplanan değerler izlendi). |
| Ortak: konsol, 375/masaüstü | geçti | Konsolda hata/uyarı yok. 375 px: `/buero` koyu ve açık görüntülendi; `/plan` telefonda yalnız „am Desktop gezeichnet“ notu gösterir (tasarım gereği), altlık orada yok. |

**Denenen kombinasyonlar (çalıştırıldı, ekran görüntüsü):** Büro: Sistem hell, elle Dunkel + sistem hell, Sistem koyu, elle Hell + sistem koyu; 375 koyu ve açık. Editör (Auswahl ve Unterlage aktiv): Sistem koyu, elle Hell + sistem koyu, elle Dunkel + sistem hell, Sistem hell, elle Dunkel + sistem koyu.

**Gözlemler (tasarım tahmini):**
- Koyu temada altlık, beyaz zemini siyaha dönen koyu bir dikdörtgen olarak yüzeyin biraz altında kalıyor; içindeki çizim (pembe/yeşil odalar, duvarlar) soluk ama seçilebiliyor. Odaların (renkli dolgu, etiketler) üstünde okunur kalıyor, etiket metinleri altlıktan etkilenmiyor.
- Aktif araçta (0,55) çizim belirgin biçimde daha okunur; turuncu kesikli çerçeve görünür.
- Dev.db'deki altlık küçük (planın sol üst kısmı) ve koyuda çok düşük kontrastlı; ayrıntılı duvar çizgileri 375'te güçlükle seçiliyor. Gereksinimi (soluk) karşılıyor; yalnız zevk meselesi.
- Hue-rotate ile renk tonları korunuyor (pembe/yeşil odalar koyuda da pembe/yeşil).

**Denenmeyenler:** Einstellungen'deki gerçek tema düğmesine tıklama (öznitelik elle değiştirildi, `einstellungen.js` yalnız okundu); gerçek cihaz; yazdırma/etiket PDF'i (ilgisiz); PDF'den yeni altlık yükleme (mevcut altlık kullanıldı); Safari/Firefox (yalnız Chromium'da `filter` denendi).

---

## Adım 2 — Kartta konum kodu (masaüstü) · 09.11.2026 · dilim-4/karte-platz @ c7c38e9 · deneme 1
**Sonuç:** GEÇTİ (K1–K3 karşılandı; gözlemler aşağıda, hiçbiri kriteri kırmıyor)

**pytest (tüm takım, çalıştırıldı):** `229 passed` (main'de 226; +3 test: `test_karte_platz_in_liste`, `test_karte_platz_nach_umzug_und_ohne_raum`, `test_karte_platz_frontend_nur_hover`).
**Dijital ürün testi:** koşullu (`if dig.status_code == 201`) ama dal gerçekten çalışıyor: geçici olarak print ekleyip denedim, POST `art=digital` 201 döndü; kontrol çalışıyor (değişiklik geri alındı, repo temiz). Çalıştırıldı.
**Sunucu:** 8091'de önceden çalışan süreç eski koddu (`/api/bibliothek` yanıtında `platz` yoktu); durdurulup yeniden başlatıldı. Yeni süreçte `platz` var (24 → `{id:7, code:"1.6.4"}`, dijital 4 → `None`). dev.db, 8090/finds.db'ye dokunulmadı. Sunucu sonda durduruldu.

| Kriter | Sonuç | Nasıl doğrulandı | Kanıt |
|---|---|---|---|
| K1 kod yalnız üstüne gelince, konumsuzda hiçbir şey | ✔ | Çalıştırıldı: tarayıcı (826 px geniş, `hover:hover` eşleşiyor), açık ve koyu tema | 25 karttan yalnız 4'ünde `.karte-platz` var (24, 9, 6, 3 = konumlu olanlar); konumsuz ve dijital kartlarda DOM'da eleman yok (rozet yok). Fareyle gelmeden `visibility:hidden`, gelince görünür (kart 24, "1.6.4", pin ikonu); ekran görüntüleri alındı (koyu ve açık, kontrast okunaklı). Renkler token (`--card`, `--ink`, `--line`, `--accent`, `--accent-ink`); diff'te ham renk yok |
| K2 koda tıklama → Büro bölme+ürün | ✔ | Çalıştırıldı: gerçek tıklama + klavye | Tıklama → `/buero?einheit=22&fach=7&produkt=24`; Büro sayfasında `1.6.4` bölmesi vurgulu, "Verano Tarçın FL-021-024" ve "Alle Fächer / 1.6.4" gösteriyor. Tab ile karttan sonra koda odak geliyor (odak çerçevesi var, kod görünür kalıyor), Enter aynı adrese gidiyor |
| K2b kartın kendisi | ✔ | Çalıştırıldı | Konumsuz kart (23) tıklama → `/produkt/23`; konumlu kartın resmine tıklama (olay gönderimi) → `/produkt/24`. Koda tıklama `stopPropagation`/`preventDefault` ile ürün detayına gitmiyor |
| K3 telefon değişmez | ✔ | Çalıştırıldı: 375x812 emülasyon (`hover:none`) | Eleman DOM'da ama `display:none` (görünmez, odaklanamaz); kart dokunuşu → `/produkt/24`; konsol hatası yok. Not: emülasyon `maxTouchPoints=0` bildirdi, yani gerçek dokunuş değil fare tıklaması (araç sınırı); karar `hover` medya sorgusuna dayanıyor |
| Veri | ✔ | Çalıştırıldı: pytest | Liste N+1 yapmıyor (benzersiz `fach_id` başına bir `plan.fach`; en çok 120 satır); taşınınca yeni kod (`test_karte_platz_nach_umzug_und_ohne_raum`); dijital → None; metin `texte.py`'den (`produkt.im_buero_zeigen`, yeni sabit metin yok) |
| D-045 görüntü kirliliği | ✔ | Çalıştırıldı + diff okundu | konumsuzda hiçbir eleman/rozet yok; konumlu kartta kod yalnız hover/odakta |

**Gözlemler (kriter dışı, bilgi):**
1. Seçim modu (Auswählen): liste satırlarına (`.zeile`) geçiyor, `.karte` hiç yok; bu yüzden orada kod yok ve koda tıklama sorunu doğmuyor (çalıştırıldı: 0 `.karte-platz`, 25 `.zeile`). Aynı şekilde kullanıcı "liste" görünümünü seçerse kod gösterilmiyor (yalnız okundu, `karte()` yalnız kart ızgarasında kullanılıyor).
2. Kod kartta `<span role="link" tabindex="0">`; kart `<a>` içinde olduğu için `<a>` iç içe yok. Klavye Enter/Space destekli (Enter denendi, Space yalnız okundu).
3. Kart yüksekliği/diğer rozetler: kod sol altta, rozetler sol üstte; çakışma yok (ekran görüntülerinde).
4. Araç sınırı: bir gerçek tıklama denemesinde (resim üzerine) sayfa değişmedi, ekran görüntüsü o sırada bozuk boyutlu geldi; aynı eylem olay gönderimiyle doğru çalıştı. Kod sorunu değil gibi görünüyor ama gerçek fare tıklamasıyla tekrar denenmedi.
   **Yönetici ek denemesi (09.11.2026, gerçek fare, dal kodu):** karta gelince „1.1.3“ göründü; kart resmine tıklama → `/produkt/3`; koda tıklama → `/buero?einheit=1&fach=1&produkt=9` (olay hedefi `SPAN.karte-platz`), Büro 1.1.3'ü vurguladı. Önceki sapma ekran görüntüsü ile CSS koordinatları arasındaki ölçek farkından (826 → 800 px); kod sorunu yok.
5. Dar-masaüstü: pane 826 px ve alt gezinme çubuğu açık (genişlik eşiği altında); gerçek >1024 px masaüstü düzeni denenmedi, kural `hover`'a bağlı olduğundan fark beklenmiyor.

**Hiç denenmeyenler:** gerçek dokunmatik cihaz; Space tuşu; >1024 px masaüstü düzeni; liste görünümü (`ansicht=liste`) ekranda; sayfa 2+ (120'den fazla ürün) kartları; ekran okuyucu.

---

## Adım 1 — Aramada bölme kodu · 07.11.2026 · dilim-4/suche-fachcode @ 0d9f4f4
**Sonuç:** GEÇTİ (deneme 2; K1–K10 karşılandı; bulgular aşağıda, hiçbiri kriteri kırmıyor)

| Kriter | Sonuç | Nasıl doğrulandı | Kanıt |
|---|---|---|---|
| K1 bölme kodu bulunur | ✔ | Çalıştırıldı: pytest + tarayıcı | `test_fachcode_ganz_und_einheit_als_praefix`; dev.db'de arayüzden `1.6.4` → Verano Tarçın, `1.6` → 2 ürün, `1.1.3` → 2 ürün (masaüstü), `1.6 basalt` → yalnız Basalt anthrazit (375 px) |
| K2 taşıma | ✔ (kısmen yalnız okundu) | Çalıştırıldı: `test_umziehen_und_umnummerieren` (Platz ändern: yeni kod bulunur, eskisi bulunmaz; konumsuz yapınca bulunmaz). Kod okundu: kod artık sorgu anında `fach→einheit→raum` ile hesaplanıyor (`suche.py:22-27`), suchtext'e yazılmıyor; bu yüzden Zurücklegen/Einordnen/toplu yolları yapısal olarak kapsanıyor | Zurücklegen+yeni yer, Einordnen, toplu düzenleme için ayrı test yok (denenmedi) |
| K3 yeniden numaralama / kod değişimi | ✔ | Çalıştırıldı: pytest | aynı test: bölme nr 1→5, 2→6 sonrası `2.1.6` bulunur, `2.1.2` bulunmaz. Raum nr / ünite nr değişimi için test yok; canlı hesap olduğundan yapısal olarak kapsanıyor (yalnız okundu) |
| K4 konumsuzda değişmez, eski testler | ✔ | Çalıştırıldı: tüm pytest | `produkte.suchtext_erneuern` bu dalda değişmemiş (diff'te yok) |
| K5 tam kod | ✔ | Çalıştırıldı: pytest | `test_fachcode_ganz_und_einheit_als_praefix`: 2.1.1/2.1.3/2.1.30/2.10.1/12.1.1 verisiyle `2.1.3`→yalnız 2.1.3, `2.1.1`→yalnız 2.1.1, `12.1.1`, `2.10` |
| K6 ünite öneki | ✔ | Çalıştırıldı: pytest | aynı test: `2.1` → tam olarak 2.1.1, 2.1.3, 2.1.30 |
| K7 diğer alanlar yok | ✔ (ünite 2.2 şartı kısmen) | Çalıştırıldı: pytest | `test_nur_fachcode_keine_ausmasse`: ölçüsü „120x60x2.2 cm“ konumsuz ürün `2.2`'de dönmez; `.1.3`, `1.`, `2.1.3.4` boş; `test_einzelne_zahl_ist_kein_fachcode`: `2` boş. Eksik: K7 „ünite `2.2`'deki ürün döner“ olumlu kısmı testte yok (testte 2.2 ünitesi yok, yalnız `== []`); olumlu ünite öneki K6'da `2.1` ile gösteriliyor |
| K8 çok kelime | ✔ | Çalıştırıldı: pytest + tarayıcı | `test_mehrere_woerter_und` (`Eiche 2.1` ve `2.1 eiche` → yalnız 2.1.3'teki Eiche; Buche ve 12.1.1'deki Eiche dönmez); dev.db'de `1.6 basalt` |
| K9 odasız ünite | ✔ | Çalıştırıldı: pytest | `test_einheit_ohne_raum`: `1.3`, `1.1.3`, `–.1.3` dönmez, hata yok, ad aramasıyla bulunur |
| K10 plan silme / yedek geri yükleme | ✔ | Çalıştırıldı: pytest | `test_plan_loeschen_und_geladene_sicherung_sofort`: aynı TestClient'ta plan silinince `2.1.1` boş, ad aramasıyla bulunur; bölmeli yedek yüklenince `2.1.1` hemen bulunur; bölmesiz yedek yüklenince boş. Canlı hesap sayesinde ek kod gerekmiyor |
| Ortak: yeni test | ✔ | Çalıştırıldı | `tests/test_suche_fach.py` 6 test |
| Ortak: metin/renk | ✔ | Yalnız okundu | diff'te arayüz metni ve CSS yok |
| Ortak: telefon + masaüstü | ✔ | Çalıştırıldı | 375x812 ve masaüstü, dev.db; konsolda mesaj yok |

- pytest: hata yok, 226 nokta (72+72+72+10; özet satırı çıktıda görünmedi, nokta sayısı sayıldı). `test_suche_fach.py` ayrıca çalıştırıldı, yeşil.
- Arama süresi (çalıştırıldı; scratchpad `perf.py`, dev.db kopyası + 5000 sahte ürün = 5025, `bibliothek.suchen`, 5 deneme, medyan): `1.6.4` 11 ms, `1.6` 15 ms, `1.1.3` 19 ms, `eiche` 8 ms, `eiche 1.6` 30 ms, `2.2` 18 ms, `platte 2.2` 24 ms. Hedef < 200 ms karşılanıyor. (Sonuç listesi 120 ile sınırlı.) 20 bin ürün denenmedi.
- Tarayıcı: **`preview_start "dev"` hâlâ eski koda açtı** (launch.json düzeltmesi etkili olmadı). Kanıt (çalıştırıldı): dal kodu doğrudan çağrılınca (`scratchpad/chk.py`, dev.db) `6.4` → boş, ama `preview_start` sunucusunda `?q=6.4` → 1 ürün (eski `instr` davranışı); süreç komut satırında launch.json'daki `os.chdir`/`sys.path.insert` parçaları yoktu. Bu ilk sunucuyla alınan tarayıcı sonuçları geçersiz sayıldı. Sunucuyu elle başlattım (uvicorn, çalışma kopyası, dal kodu, 8091, dev.db) ve yeniden denedim: curl `6.4`→0, `1.6`→2, `1.6.4`→1, `1.1.3`→2, `1.6+basalt`→1; tarayıcıda 375 px `1.6 basalt` → yalnız Basalt anthrazit, masaüstü `1.6` → Verano Tarçın + Basalt anthrazit, konsolda mesaj yok. Sunucu durduruldu, dal main'e döndürüldü; 8090 / finds.db'ye dokunulmadı.
- Hiç denenmedi: Zurücklegen/Einordnen/toplu düzenleme yolları (ne test ne elle); Raum/Einheit numarası değişimi testi; K7 olumlu „ünite 2.2“ testi; 20 bin ürün; arayüzden elle taşıma; Etiketten sayfasında tarayıcı; gerçek cihaz.
- Bulgular (gözlem, karar verilmedi):
  1. `.claude/launch.json` düzeltmesi çalışmıyor: `preview_start "dev"` dal kodunu değil eski kodu çalıştırdı. Beklenen: çalışma kopyası. Görülen: `?q=6.4` → 1 sonuç (dal kodunda 0). Nedeni araştırılmadı.
  2. Kapsam: diff PLAN'da adı geçmeyen `app/services/etiketten.py`'yi değiştiriyor (`liste`, Etiketten sayfası araması da `wort_bedingung` kullanıyor). PLAN yalnız Kütüphane aramasını söylüyor. Bu sayfa için test yok, tarayıcıda denenmedi (kod yalnız okundu). Diğer değişenler: PLAN.md (durum satırı), `suche.py`, `bibliothek.py`, test dosyası.
  3. dev.db'de (yalnız dev verisi) önceki denemeden kalma suchtext'ler duruyor, ör. ürün 24: `… fl-021-024 24 1.6.4 braun` (çalıştırıldı, sqlite okuma). Yeni kod bunu kullanmıyor ama koda benzemeyen kelimeler suchtext'te aranır; D-050 „diğer kelimeler bölme koduyla eşleşmez“ diyor, bu veride tek sayı/parça sorguları (ör. `4`) eski koda takılabilir. Temiz bir veritabanında (main'den gelen) bu sorun yok; beta'ya eski suchtext hiç yazılmadı (7933568 main'de değil).
  4. Önceki denemenin eklediği `suchtexte_alle_erneuern`, `_mit_platz`, `_suchtexte_nach_plan` ve `main.py` açılış çağrısı dalda yok (grep ile çalıştırıldı); gereksiz kalan kod görülmedi.
  5. Test boşlukları: K2 için yalnız Platz ändern; K3 için Raum/Einheit nr değişimi; K7 olumlu ünite `2.2` durumu testte yok.

---

## Adım 1 — Aramada bölme kodu · 06.11.2026 · dilim-4/suche-fachcode @ 7933568
**Sonuç:** GEÇTİ (deneme 1)

| Kriter | Sonuç | Nasıl doğrulandı | Kanıt |
|---|---|---|---|
| K1 bölme kodu bulunur | ✔ | Çalıştırıldı: pytest + tarayıcı (dev.db, dal kodu) | `test_fachcode_und_einheitscode_finden_produkt`; dev.db'de `1.1.3` → 2 ürün (Leinen natur, Feinsteinzeug Grau), `1.6.6` → 1 ürün; 375 ve masaüstünde ekran görüntüsü, konsol hatası yok |
| K2 taşıma (Platz ändern, Zurücklegen+yeni yer, Einordnen, toplu, toplu geri al, yerden alma) | ✔ | Çalıştırıldı: pytest | `test_umziehen_ueber_platz_einordnen_zuruecklegen_sammel` (yeni kod bulunur, eskisi bulunmaz; `sammel/rueckgaengig` dahil). Kod okundu: `platz_setzen` (plan.py:420) ve `sammel.py:102` suchtext'i yeniliyor |
| K3 yeniden numaralama / kod değişimi | ✔ | Çalıştırıldı: pytest | `test_umnummerieren_erneuert_suchtext` (Fach nr, Raum nr, Fach silme) |
| K4 konumsuzda değişmez, eski testler | ✔ | Çalıştırıldı: pytest | `test_ohne_platz_und_alter_suchtext` (konumsuz suchtext aynı kalır; eski suchtext açılışta onarılır) |
| Ortak: testler yeşil, yeni test | ✔ | Çalıştırıldı | 4 yeni test (`tests/test_suche_fach.py`) |
| Ortak: metin/renk | ✔ | Yalnız okundu | diff'te yeni arayüz metni ve CSS yok |
| Ortak: kapsam | ✔ | Yalnız okundu | değişen: PLAN.md (durum satırı), main.py, services/plan.py, services/produkte.py, yeni test dosyası. Kapsam dışı yok |
| Ortak: telefon + masaüstü | ✔ | Çalıştırıldı | 375x812 ve masaüstü, Bibliothek `?q=1.1.3`, iki kart görünür |

- pytest: tamamı yeşil (223 nokta, hata yok; özet satırı çıktıda görünmedi, `-p no:warnings` ile nokta sayısına bakıldı). Başlangıç 219 + 4 yeni.
- Açılışta toplu yenileme (main.py:51-53, `suchtexte_alle_erneuern`) — ölçüm (geçici DB, scratchpad `perf.py`, 5000 ürün, %90'ı bölmeli): `create_app` toplam 0,39 s, yalnız yenileme 0,23 s. Her açılışta yazma işlemi yapılıyor ama makul. 20 binde doğrusal ~1 s beklenir (çalıştırılmadı). Arama (5000 ürün): ilk çağrı 122 ms (ısınma), sonrakiler 25-26 ms; sonuç listesi 120 ile sınırlı.
- Tarayıcı: dev sunucusu önce eski süreç durduruldu. NOT: `preview_start "dev"` süreci bu çalışma kopyasından değil Drive klasöründeki (eski, dal öncesi) kodla açtı: dev.db'de suchtext'te kod yoktu ve `1.1.3` "Keine Treffer" verdi. Bunun üzerine onu durdurup aynı ortam değişkenleriyle sunucuyu çalışma kopyasından (dal kodu) elle başlattım (uvicorn, 8091, dev.db); denemeler onunla. Sonra sunucu durduruldu, dal main'e geri alındı. dev.db'de açılış yenilemesi suchtext'leri güncelledi (dev verisi).
- Hiç denenmedi: Systembereich'ten yedek geri yükleme sonrası arama (yalnız okundu: açılış yenilemesi onarır, geri yüklemede sunucu yeniden başlamazsa eski suchtext kalabilir); 20 bin ürünle süre; gerçek cihaz; arayüzden elle taşıma akışı (Büro yer seçme modu) — yalnız API testleri.
- Bulgular (gözlem, karar verilmedi):
  1. Eşleşme düz alt dize (`bibliothek.py:43` `instr`). `2.1.1` araması `12.1.1` kodlu bölmeyi de bulur (kod okundu; aynı mekanizma dev.db'de `.1.3` → 1.1.3 ürünleri, `1.6` → ürün 24 + 6 gösterdi: çalıştırıldı). Ölçülerde `2.2` geçince (ör. "120x60x2.2 cm") `2.2` araması bu ürünleri de getirir (5000 ürünlük geçici DB'de çalıştırıldı: 120 sonuç, çoğu ölçü eşleşmesi). Büronun `Raum.Einheit` numaraları küçükse çakışma olasılığı düşük, kayıtlarda ölçü alanı doluysa yüksek.
  2. Raumsuz bir ünitede kod `–.1.3` biçiminde (`plan.py:35`); aranan metin `1.1.3` değil `–.1.3` olur ve suchtext normalizasyonunda `–` kalır. dev.db'de ürünlerin raumu vardı, bu yol çalıştırılmadı (yalnız okundu).
  3. Systembereich "plan" silmesi (`sicherung.py:197-198`) ürünleri FK ile konumsuz yapar ama suchtext yenilenmez; eski kod bir sonraki açılışa kadar aranabilir kalır. Test yok, çalıştırılmadı (yalnız okundu).
  4. `suchtexte_alle_erneuern` yalnız `plan.py` içinde, `produkte`'ye lazy import ediliyor (döngüsel import çözümü); işlevsel sorun yok.

---

<!-- Bölüm şablonu
## Adım N — <ad> · <tarih> · <dal> @ <commit>
**Sonuç:** GEÇTİ / KALDI (deneme 1/2/3)

| Kriter | Sonuç | Nasıl doğrulandı (çalıştırıldı / okundu) | Kanıt |
|---|---|---|---|
| K1 | ✔/✘ | | test adı, komut çıktısı, ekran görüntüsü |

- pytest: <geçen>/<toplam>, süre
- Tarayıcı (8091, dev.db): ne yapıldı, hangi boyutta
- Hiç denenmedi: …
- Bulgular (Kodlayıcı için, düzeltme önerisi değil, gözlem): …
-->
