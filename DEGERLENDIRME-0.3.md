# miaza finds — Dört aşamalı değerlendirme (SPEC 0.3 + demo v24)

Tarih: 01.11.2026
Yöntem: "İyi tasarımın ilkeleri" yol haritası: Çıkar → Sağlamlaştır → Ekle → Tekrar bak.
Bu belge sadece değerlendirmedir. SPEC'e ve demoya henüz hiçbir şey işlenmedi; kararını bekliyor.

**Uygulamanın tek cümlesi (ölçüt):** *Büronun malzemesini birkaç saniyede bul: kütüphanede arayarak, ofiste rafında.*
Her parça bu cümleye hizmet ediyor mu, buna bakıldı.

---

## 1. Çıkar (Musk · Rams)

Her parça için iki soru soruldu: **"Bunu kim istedi?"** ve **"Olmasa ne bozulur?"**
Sahip sütununda "Sen" senin isteğin demek; "Ben" ise benim önerimdir ve kanıtı yoktur.

| # | Parça | Sahip | Olmasa ne bozulur? | Öneri |
|---|---|---|---|---|
| 1.1 | Raf onayında **"Zorunlu"** modu | Ben | Hiçbir şey. "Zorunlu" iken de "Okutmadan onayla" var; yani aslında "isteğe bağlı"dan farkı yok. | **Sil.** Ayar iki seçenekli kalsın: Açık / Kapalı. |
| 1.2 | Kategori ve filtre düzenleme **telefonda da** var | Ben | Hiçbir şey. SPEC'e göre ayarlar masaüstünün işi. Aynı ekran iki kez yazılıyor. | **Telefondan sil.** Telefonda sadece kişiler ve bu cihaz kalsın. |
| 1.3 | Filtre tiplerinden **"Serbest metin"** | Ben | Hiçbir şey. Arama kutusu zaten seri ve marka içinde arıyor. | **Sil.** |
| 1.4 | ~~"Tekli" ve "çoklu özellik" ayrı tip~~ | Sen | Anlamı farklı: tekli değerler birbirini dışlar (bir fayans hem R9 hem R10 olamaz), çoklu değerler bağımsızdır (hem rektifiye hem parlak olabilir). | **Geri alındı.** İkisi ayrı tip olarak kalır. Filtre tipleri: Ölçü · Tekli seçim · Çoklu seçim · Var/Yok. Kurulum ekranında her tipin yanında örnek yazar ("R9 ya da R10" / "rektifiye ve parlak"). |
| 1.5 | **Kategori rengi** ve **oda rengi** seçimi | Ben | Hiçbir şey. Bunlar süs; durum renkleriyle yarışıyorlar. Apple: "her rengin tek anlamı". | **Sil.** Odalar nötr ve adlı; vurgu rengi sadece seçili ünitede. Ayarlarda iki seçim azalır. |
| 1.6 | Altlık ayarları: **saydamlık (3 kademe)** ve **"koyu temada ters çevir"** düğmesi | Ben | Hiçbir şey. Tek bir sabit soluk görünüm yeter. | **Sil.** Kalanlar: göster/gizle, ofiste göster, hizala. |
| 1.7 | **Kategori ayarlarında** geri al/yinele çubuğu | Ben | Hiçbir şey. Seyrek yapılan, basit bir form. Kaydet/Vazgeç yeter. | **Sil.** Geri al çubuğu sadece çizimde (plan, raf fotoğrafı) kalsın. |
| 1.8 | **Taslağı kaza sonrası geri getirme** | Ben | Çok nadir bir durum. Ayrılma uyarısı ve sürüm kontrolü zaten var. | **v1'den çıkar.** |
| 1.9 | **40'lı** etiket düzeni | Ben | Sen "20'li" dedin. 40'lıda QR çok küçük kalır. | **Sil.** |
| 1.10 | Birden fazla **doküman klasörü** | Ben | Şu an tek klasör var (Bibliothek). | **Tek kök klasör.** Gerçekten gerekince çoğalır. |
| 1.11 | ~~Ofiste fareyle önizleme~~ | Sen | Tıklamadan, hızlıca göz gezdirmeye yarıyor. | **Geri alındı, kalıyor.** Teknik koşulları: sadece fareli cihazda çalışır (tablette dokunma zaten tıklamadır); yaklaşık 300 ms gecikmeyle açılır, böylece fare geçerken titremez; tıklanacak hedefin üstünü örtmez. |
| 1.12 | **Linkten doldurma** ve **fotoğraftan otomatik renk** | Ben | v1'de bozulan bir şey yok. Musk: otomasyon en sona. Linkten doldurma ayrıca kırılgan (her site farklı). | **v2'ye taşı.** Renk elle seçilsin (tek dokunuş). |
| 1.13 | **Kategori değişince kod sorusu** | Sen (kod şeması) | Soru kalksa basılı etiketin yazısı habersizce eskir. | **Tut.** Gerekçesi var. |
| 1.14 | **Açılış ekranı** | Sen | İşlevsel olarak hiçbir şey; markayı taşıyor. | **Tut.** Sahibi ve sınırı (≤ 700 ms) belli. |
| 1.15 | **"Bu cihazı kullanan"** ayarı | Ben (son turda ekledim) | "Düzenleniyor" uyarısı kişi adı yerine "başka bir cihaz" der. | **Tut ama isteğe bağlı.** Uyarıyı işe yarar yapan tek şey "Ayşe'ye sor" diyebilmek. Gereksiz bulursan silinir. |

Toplam: **12 silme veya taşıma önerisinden 2'si geri alındı (1.4, 1.11), 10'u kalıyor.** Bu, yöntemin beklediği orana uyuyor: silinenlerin bir kısmı geri gelir. Musk'ın ölçütüne göre bunların yaklaşık biri sonradan geri gelebilir; normaldir.

**Bitiş ölçütü:** Kalan her parçanın bir sahibi ve tek cümlelik bir gerekçesi var. Ölçüt, yukarıdaki silmeler yapılınca sağlanıyor.

---

## 2. Sağlamlaştır (Jobs · Norman · Nielsen)

Ana işleri kullanıcının gözüyle yürüdüm:

- **A. Tasarım yaparken ürün bul:** ara → filtrele → detay.
- **B. Ürünü yerine koy:** QR → plan → bölme → yerine koy → raf onayı.
- **C. Yeni ürün kaydet:** fotoğraf → ad → kaydet.
- **D. Planı düzenle.**

Bulunan sorunlar 0–4 arasında puanlandı (4 en ağır). Önce 3–4'ler düzeltilmeli.

| # | Sorun | İlke | Puan | Öneri |
|---|---|---|---|---|
| 2.1 | **"Kullanımda" iki farklı şeyi anlatıyor:** ürünün büro içinde birinde olması, ve bir kaydın başka cihazda düzenlenmesi. | Tek ad, tek anlam | **4** | Düzenleme uyarısının adı **"Düzenleniyor"** olsun: "Ayşe düzenliyor". "Kullanımda" sadece ürün durumu için kalsın. |
| 2.2 | **Aynı durumun üç adı var:** "Dışarıda", "Büro dışında", filtrede "Dışarıda / kullanımda". | Tek ad | **3** | Durumlar **Yerinde · Kullanımda · Büro dışında**. Filtre seçenekleri de birebir aynı adları kullanır. |
| 2.3 | **Mekân terimleri karışık:** SPEC'te ünite ve bölme, etikette "raf etiketi", onayda "raf onayı", verilerde "göz" ve "çekmece". Kullanıcının kafasındaki model ile sistem aynı değil. | Kavramsal model | **3** | Tek sabit ad olmaz: ünite açık raf, dolap, çekmeceli eleman, tekerlekli dolap (Rollcontainer) veya kutu olabilir. Bkz. aşağıdaki **2.3 terim modeli**. |
| 2.4 | **Konumsuz ürünlerin yeri belirsiz.** SPEC "ayrı bir listede görünür" diyor ama yerini söylemiyor. İstatistikte de geçiyor. | Sistem durumunu göster, tek yer | **3** | Yeni ekran açılmasın. Kütüphanedeki durum filtresine **"Konumsuz"** seçeneği eklensin. İstatistikteki sayı bu filtreye götürsün. |
| 2.5 | **Açıklama metni fazla.** Demoda 24 açıklama cümlesi var (telefon 11, masaüstü 13). Örnekler: plan düzenleyicideki "Düzenle'ye bas…" kartı, raf onayının altındaki not, "sana haber veririz" cümlesi. | Norman: açıklama bir yamadır | **2** | Her biri için önce tasarım düzeltilsin. Örneğin görüntüleme modunda çizim araçları gri ama görünür olsun; o zaman kart gereksizleşir. Hedef: ekran başına en fazla 1 açıklama. |
| 2.6 | **Yazı boyutu çok fazla:** telefonda 19, masaüstünde 20 farklı boyut. | Apple: az boyut | **2** | Gerçek tasarımda 5–6 kademelik bir ölçek: 12 / 13 / 15 / 18 / 24 / 34. |
| 2.7 | Masaüstünde **İstatistik yok**, telefonda var. | Tutarlılık | **1** | Masaüstünde Kütüphane başlığının yanında bir sayı satırı yeter (28 kayıt · 2 dışarıda · 3 konumsuz). Tıklanınca filtre olur. Yeni sayfa açılmaz. |
| 2.8 | Ad farkları: telefonda "Koleksiyon", masaüstünde "Koleksiyonlar"; menüde "Okut", masaüstünde "QR okut". | Tek ad | **1** | Hepsi tek ada indirilsin. |
| 2.9 | Ofiste kartlar **"karışık açılarla"** açılıyor. Açıların bir anlamı yok, süs gibi. | Apple: hareket anlam taşısın | **1** | Senin fikrin, o yüzden tutuldu. Ama açılar rastgele değil düzenli olsun; öne çıkan ürün tek farklı olan olsun. |
| 2.10 | **Demo ile SPEC kapsamı çelişiyor.** Koleksiyonda miktar, KDV ve dışa aktarma gösteriliyor; SPEC'e göre bunlar v2. Masaüstünde ise asıl masaüstü işi olan **Etiketler** ekranı yok. | Dürüstlük (Rams) | **2** | Demoda v2 parçaları açıkça "sonraki sürüm" diye işaretlensin. Masaüstüne etiket ekranı eklensin. |

### 2.3 terim kararı (01.11.2026)

- **Einheit** (Türkçe demoda: Ünite): 2.1 gibi her mobilya ve saklama birimi. Karşılığı tüm türleri kapsıyor: açık raf, dolap, çekmeceli eleman, tekerlekli dolap, kutu.
- **Fach** (Türkçe demoda: Bölme): 2.1.5 gibi alt alanlar. Etiketin adı "Fach-Etikett", onayın adı "Fach bestätigen".
- **Tür listesi gerekmez** (1. aşama, Çıkar). Ünitenin isteğe bağlı bir adı olur: "2.1 · Schrank links". Türü bu ad söyler; ayarlarda ayrı bir tür listesi yönetilmez.
- **Çakışma:** "Einheit" Almancada fiyat birimi anlamına da gelir (Preis pro Einheit). Tek ad kuralı gereği fiyat tarafında bu kelime kullanılmaz:
  - Ürün formunda fiyat "Preis" olarak yazar, birim seçimi "/ m²" biçiminde görünür.
  - Sipariş listesi dışa aktarımında sütunun adı **ME** (Mengeneinheit), Almanca sipariş listelerinde alışılmış kısaltma.

### 2.3 terim modeli (ilk öneri, yerini yukarıdaki karar aldı)

Ünitelere sabit bir ad vermek yerine, adı ünitenin **türünden** gelsin. Böylece ekranda kullanıcının kendi söylediği söz görünür: "Schrank 2.1 · Schublade 3".

| Tür (ayarlardan eklenip düzenlenebilir) | Alt alanın adı |
|---|---|
| Offenes Regal | Fach |
| Schrank | Fach |
| Schubladenelement | Schublade |
| Rollcontainer | Schublade |
| Box | Fach (veya hiç alt alan yok) |

- **Kod her türde aynıdır** (`2.1.5`) ve ortak, değişmeyen addır. Ekranda bölme hep kodla gösterilir; tür adı onun yanında yardımcı bilgidir.
- Türden bağımsız **genel bir kelime** sadece birkaç sistem yerinde gerekir: çizim aracı ("… çiz"), etiket türü, raf onayı ayarı. Buraya geniş anlamlı iki kelime öneriyorum, seçim senin:
  - Ünite için: **Möbel** veya **Stauraum**
  - Bölme için: **Lagerplatz** (etiket: "Lagerplatz-Etikett", onay: "Lagerplatz bestätigen") veya **Fach**
- En iyi ölçüt: ofiste insanlar bunu nasıl söylüyor? "Wo ist das?" sorusuna verilen cevaptaki kelimeler seçilmeli.

Sağlam bulunanlar (dokunulmayacak):
- Hızlı işlemlerde bildirimdeki "Geri al".
- Yanlış raf okununca açılan pencere: hatayı önlüyor ve tek adımda düzeltiyor.
- Plan düzenleyicide kaydetmeden önce gösterilen etki özeti.
- Ürün kodunun sadece numarasıyla aranabilmesi ("265"): ezber değil tanıma.
- QR'ın sadece kalıcı kimliği taşıması.

**Bitiş ölçütü:** A–D işleri açıklamasız yapılabiliyor ve 3–4 puanlı sorun kalmıyor. Şu an sağlanmıyor; 2.1–2.4 düzeltilince sağlanır.

---

## 3. Ekle (Christensen · Kano · Gall · Shape Up)

Her öneri için soruldu: **"Bu eksik yüzünden kullanıcı bugün ne yapıyor?"** Somut cevabı olmayan eklenmedi.

### Eklenmeli

| # | Eksik | Kanıt (bugün ne oluyor) | İş cümlesi | En küçük çalışan hali | Kano |
|---|---|---|---|---|---|
| 3.1 | **Hızlı toplu kayıt** | Başlangıçta 200–300 ürünün tek tek girilmesi gerekiyor. Sen "veri girişi üşendirirse uygulama ölür" dedin. Bu, uygulamanın ilk haftasındaki en büyük engel. | "Rafın önünde durup ürünleri art arda fotoğraflayabilmek için." | Kamera açık kalır; her fotoğraf kodu verilmiş bir taslak ürün olur. Bölme önceden seçilir, konum da birlikte kaydolur. Ad ve ayrıntılar sonra, masaüstünde "Eksik bilgisi olanlar" filtresinden tamamlanır. Yeni ekran yok: mevcut kamera ve mevcut filtre. | Temel |
| 3.2 | **Ürün silme** | Numuneler eskiyor, atılıyor. SPEC'te ürünü silmenin kuralı yok. Bugün olsa kayıt sonsuza kadar kalırdı. | "Atılan numuneyi listeden kaldırabilmek için." | Ürün detayında "Sil" ve onay. Envanter numarası boş kalır; etiketi baskı listesinden düşer. | Temel |
| 3.3 | **Masaüstünde etiket ekranı** (demoda) | Etiket PDF'i masaüstünden yazdırılıyor; demoda bu ekran yok. | "Seçtiğim etiketleri A4'e dizip yazdırabilmek için." | Telefondaki ekranın masaüstü düzeni: solda arama ve seçim, sağda A4 önizleme. | Temel |

### Kanıt bekleyenler (şimdilik eklenmiyor)

| Fikir | Neden bekliyor |
|---|---|
| Aynı ürün iki kez girilince uyarı | Olası ama henüz gözlenmedi. 3.1 kullanılmaya başlanınca tekrar bakılır. |
| Dışarıdaki ürün için dönüş tarihi ve hatırlatma | Sen sadece "nerede olduğunu bilelim" dedin; hatırlatma istemedin. |
| Bir ürünün birden fazla yerde durması | Gözlenmedi. "Adet" alanı şimdilik yeter. |
| Kurulum sihirbazı | Bir kerelik iş; ekran değil, kurulum belgesi yeter. |

### "Hayır listesi" (Jobs) — bilerek yapılmayanlar

SPEC'te bu liste yoktu; eklenmeli:
- Kullanıcı hesabı ve yetki.
- Stok, sipariş takibi, muhasebe.
- "Numune istendi" gibi ara durumlar.
- Fiyat geçmişi (v1).
- Ofis dışından erişim.
- Kilit yönetimi ekranı.
- Birden fazla vurgu rengi.

**Bitiş ölçütü:** 3.1 ve 3.2 en küçük halleriyle tanımlandı. SPEC'e girince 2. aşamanın testleri bu yeni parçalar için de tekrarlanır.

---

## 4. Tekrar bak (Rams · Musk · Apple)

**Tek cümle testi.** Demo bugün cümlenin ikinci yarısına ("ofiste rafında") ağırlık veriyor. Plan düzenleyicide araç, altlık, kaydırma, hizalama ve kısayol var; masaüstündeki en büyük ekran bu. Cümlenin ilk yarısı olan **kütüphanede arama** ise demoda ilk günkü halinde. İki eşit ana işlevden biri, ilgide geride kalmış.

→ Gerçek tasarımda önce **kütüphane ve arama** cilalanmalı:
- Arama sonuçlarının hızı ve sıralaması.
- Seçili filtrelerin görünüşü.
- Ürün detayının ilk bakışta yeterli olması.

**Sayaçlar** (bugünkü durum → hedef):

| Ölçü | Telefon | Masaüstü | Hedef |
|---|---|---|---|
| Farklı yazı boyutu | 19 | 20 | 5–6 |
| Açıklama cümlesi | 11 | 13 | ekran başına ≤ 1 |
| Renk anlamı | vurgu + 4 durum + 7 kategori + 7 oda | aynı | vurgu + 4 durum |
| Ayar sayısı | — | — | 1. aşamadaki silmelerle yaklaşık 8 ayar azalır |

**Squint testi:**
- Telefon kütüphanesinde ilk göze çarpan arama kutusu ve görseller. Doğru.
- Masaüstü ofis ekranında ilk göze çarpan renkli oda zeminleri; ürün kartları ve seçili ünite değil. Yanlış. 1.5'teki nötr odalar bunu düzeltir.

**Hızlandır / otomatikleştir (en son):**
- Linkten doldurma ve otomatik renk v2'ye (1.12).
- 3.1'deki toplu kayıt aslında bir hızlandırma. Ama yanlış bir şeyi değil, ana işi hızlandırıyor; temel beklenti olduğu için v1'de kalır.

**Döngü:** Fazla bulundu (12 madde), 1. aşamaya dönülecek. Yeni eksik gözlenirse 3. aşamaya.

---

## Önerilen sıra

1. **Senin kararın gereken iki konu:**
   - Mekân terimleri (2.3).
   - Silme listesinde itiraz ettiğin satırlar (1.x).
2. Kararlarına göre **SPEC 0.4:** silmeler, 2.1–2.4 düzeltmeleri, 3.1–3.2 eklemeleri, hayır listesi.
3. **Demo:** terimler ve adlar, kullanımda → düzenleniyor, durum adları, konumsuz filtresi, masaüstü etiket ekranı, v2 işaretleri.
4. **Gerçek tasarım:** yazı ölçeği ve renk sayısı, önce kütüphane.
