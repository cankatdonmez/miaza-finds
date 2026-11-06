# TEST_RAPORU — miaza finds

Denetçi yazar. Her PLAN adımı için bir bölüm; en yenisi üstte. Kod değiştirilmez, yalnız rapor.
**Çalıştırılan** ile **yalnız okunarak incelenen** ve **hiç denenmeyen** ayrı yazılır. Denenmeyen şey „denendi“ diye yazılmaz.

Başlangıç durumu (07.11.2026, `pre-multiagent` etiketi): 219 test yeşil. Önceki elle denemeler ve hiç denenmeyenler: `DURUM.md` §3.

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
