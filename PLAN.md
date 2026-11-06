# PLAN — miaza finds, v1'in kalanı

Çok ajanlı akışın iş listesi (07.11.2026, Cankat onayı). Kaynak: SPEC 10 v1 listesi ve DEVIR.md §4a.
Bir adım ancak **kabul kriterlerinin hepsi** Denetçi tarafından doğrulanınca `TAMAM` olur. Karar gerektiren adımda
önce D-numarası ve belge commit'i yazılır, sonra kod (CLAUDE.md).

Durumlar: `SIRADA` · `KARAR BEKLİYOR` · `KODLANIYOR` · `DENETİMDE` · `TAMAM` · `BEKLEMEDE`

Her adım için ortak kriterler (ayrıca yazılmaz):
- Bütün testler yeşil (`…\.venv\Scripts\python -m pytest -q`); yeni davranış için en az bir yeni test.
- Yeni arayüz metni yalnız `app/texte.py`'de, Almanca; ham renk yok (`test_stil`).
- Değişiklik adımın kapsamında kalır; ilgisiz dosyaya dokunulmaz.
- Görünen bir değişiklikse dev sunucusu (8091, `dev.db`) yeniden başlatılıp tarayıcıda telefon ve masaüstü boyutunda denenir.
- Dal: `dilim-4/<kisa-ad>`; main'e birleştirme ve push yalnız Cankat isteyince.

---

## 1. Aramada bölme kodu — `DENETİMDE`
SPEC 6.1, D-050. Dal: `dilim-4/suche-fachcode` (K1–K4 denetlendi; K5–K10 D-050 ile eklendi, aynı dalda).
- K1: Kütüphane aramasında bir bölme kodu (ör. `2.2`) yazılınca o bölmedeki ürünler sonuçta çıkar.
- K2: Ürün başka bölmeye taşınınca (Platz ändern, Zurücklegen + yeni yer, Einordnen, toplu düzenleme) arama yeni kodu bulur, eskisini bulmaz.
- K3: Plan yeniden numaralanınca ya da bölme/ünite kodu değişince etkilenen ürünlerin arama metni yenilenir.
- K4: Konumsuz ürünlerde arama metni değişmez; mevcut arama testleri bozulmaz.
- K5 (tam kod): Bölmeler `2.1.1`, `2.1.3`, `12.1.1`, `2.1.30`, `2.10.1`'de birer ürün varken `2.1.3` araması yalnız
  `2.1.3`'teki ürünü, `2.1.1` araması yalnız `2.1.1`'deki ürünü döndürür (test).
- K6 (ünite öneki): Aynı veriyle `2.1` araması tam olarak `2.1.1`, `2.1.3`, `2.1.30` ürünlerini döndürür; `12.1.1` ve
  `2.10.1` dönmez (test).
- K7 (diğer alanlar yok): Konumsuz bir ürünün adında/ölçüsünde „120x60x2.2 cm“ varken `2.2` araması onu döndürmez;
  ünite `2.2`'deki ürün döner (test). `.1.3` ve tek `2` araması hiçbir ürünü yalnız bölme kodu yüzünden döndürmez (test).
- K8 (birden çok kelime): `Eiche 2.1` yalnız adında „Eiche“ geçen ve `2.1.x` bölmesindeki ürünleri döndürür; `2.1`'deki
  başka ürün ve başka bölmedeki „Eiche“ dönmez (test).
- K9 (odasız ünite): Odasız bir ünitedeki (`–.1.3`) ürün `1.3` ve `1.1.3` aramasıyla dönmez; arama hata vermez (test).
- K10 (hata düzeltmesi): Ürün `2.1.3`'teyken Systembereich'te „Büroplan“ silinince (`sicherung.loeschen`, `plan`) ve
  ayrıca bölmesiz bir yedek geri yüklenince (`sicherung.einspielen`), uygulama yeniden başlatılmadan `2.1.3` araması
  boş döner ve ürün ad aramasıyla hâlâ bulunur; tersine, bölmeli bir yedek geri yüklenince yedekteki kod hemen
  aranabilir (test, aynı `TestClient`/bağlantı içinde, `create_app` yeniden çağrılmadan).

## 2. Kartta konum kodu (masaüstü) — `SIRADA`
SPEC 6.1. Dal: `dilim-4/karte-platz`.
- K1: Masaüstünde kütüphane kartının üstüne gelince ürünün konum kodu görünür; konumsuz üründe hiçbir şey görünmez (rozet yok, D-045 ruhu).
- K2: Koda tıklanınca Büro görünümü o bölmeyi ve ürünü gösterir (`/buero?fach=&produkt=`).
- K3: Telefonda (dokunmatik) davranış değişmez.

## 3. Koyu temada plan altlığı — `SIRADA`
SPEC 4.3. Dal: `dilim-4/unterlage-dunkel`.
- K1: Koyu temada kat planı altlığı renkleri ters çevrilmiş ve soluk görünür (Büro ve plan düzenleyici).
- K2: Açık temada görünüm değişmez.
- K3: Kural CSS'te tokenlarla/tema seçicisiyle yazılır; tema değişince sayfa yenilenmeden uygulanır.

## 4. Açılış ekranı — `SIRADA`
SPEC 4.1. Dal: `dilim-4/auftakt`.
- K1: Soğuk açılışta marka ekranı en fazla 700 ms görünür; dokununca hemen geçer.
- K2: Aynı oturumda sayfa geçişlerinde yeniden görünmez.
- K3: Anlamsız efekt yok; `prefers-reduced-motion`'da hareket yok.

## 5. Dokumente — `KARAR BEKLİYOR`
SPEC 6.9, D-004. Önce Mimar: kök klasörün yeri ve kapsamı Cankat'la → D-numarası → SPEC → belge commit'i.
Kabul kriterleri karar sonrası yazılır.

## 6. Kart yayı / yelpaze ve fareyle önizleme — `KARAR BEKLİYOR`
SPEC 4.7, D-017 („Tekrar bak“ adımında gerçek veriyle). Önce Mimar: gerçek veriyle tasarım önerisi.

## 7. Almanca son okuma — `KARAR BEKLİYOR`
SPEC 10, 11.5. Önce Cankat: de-AT biçimleri, „Bibliothek“ adı çakışması.

---

## Beklemede (D-049)
Gece yedeği (SPEC 8.4), HTTPS ve canlı kamera (8.2), kalıcı QR adresi, „Linkten doldurma“ (D-048, en son).
