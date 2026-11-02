# miaza finds — Ürün Spesifikasyonu (SPEC)

Sürüm: 0.5 · 01.11.2026 · Durum: uygulamada (dilim 1)
Kaynak: tıklanabilir demo (telefon, masaüstü, A4 etiket), demo üzerinde verilen kararlar ve [DEGERLENDIRME-0.3.md](DEGERLENDIRME-0.3.md).

**Yol gösterici:**
- Yöntem: "İyi tasarımın ilkeleri" yol haritası (Çıkar → Sağlamlaştır → Ekle → Tekrar bak).
- Uygulaması: [DESIGN-PRINCIPLES.md](DESIGN-PRINCIPLES.md).
- Bu SPEC'teki her parçanın bir sahibi ve gerekçesi vardır. Yeni bir parça ancak 6.12'deki ölçüte uyarsa girer.

**Sürüm geçmişi:**
- **0.5:** uygulamaya başlarken verilen kararlar (DECISIONS.md D-001–D-008): aile port düzeni, counts'un yazı sistemi, Docker ve start.bat birlikte, dokümanlar dilim 4'te, şifreli Systembereich (6.13), istek koruması.
- **0.4:** dört aşamalı değerlendirmenin sonucu.
  - **Çıkarılanlar:** "zorunlu" bölme onayı; telefonda kategori düzenleme; serbest metin filtresi; kategori ve oda renkleri; altlığın saydamlık ve ters çevirme ayarları; kategori ayarlarındaki geri al çubuğu; taslağı kaza sonrası geri getirme; 40'lı etiket; birden fazla doküman klasörü.
  - **v2'ye taşınanlar:** linkten doldurma, otomatik renk.
  - **Düzeltilenler:** terimler (Ünite/Einheit, Bölme/Fach), durum adları, "kullanımda" ile "düzenleniyor" ayrımı, konumsuz ürünlerin yeri, yazı ölçeği.
  - **Eklenenler:** seri kayıt, ürün silme, terim sözlüğü, hayır listesi.
- **0.3:** tema seçimi Ayarlar'a taşındı; masaüstünde ikincil QR okutma; aynı anda düzenleme uyarısı.
- **0.2:** marka, tema, taslak ve geri al düzeni, vektör plan ve altlık ayrımı, plan kaydırma, bölme QR'ıyla onay, etiketlerden konumun kaldırılması, ürün kodu, isteğe bağlı vergi, teknik altyapı.

---

## 1. Amaç

Büronun malzeme kütüphanesini (fayans, ahşap, metal, kumaş, taş ve diğer numuneler) tek yerde toplamak.

**Tek cümle:** *Büronun malzemesini birkaç saniyede bul: kütüphanede arayarak, ofiste yerinde.*

Uygulamanın **iki eşit ağırlıkta ana işlevi** var:

1. **Kütüphane (tasarım aracı):** Fiziki ve sadece dijital ürünler arasında hızlı arama ve filtreleme. Tasarım yaparken "R11, mat, 60 cm üstü, terracotta tonlu fayans" gibi bir arama birkaç saniyede sonuç vermeli.
2. **Ofis organizasyonu (düzen aracı):** Her fiziki ürünün ofiste nerede olması gerektiğini bilmek, bulmak ve yerine koymak. Dışarıdaki ürünü takip etmek.

Uygulama bir depo yönetim sistemi değildir (bkz. 12, hayır listesi). Sipariş **listesi** oluşturmak kapsamdadır (6.8).

## 2. Kullanıcılar ve ortam

- 4–5 kişilik büro. Herkes her şeyi yapabilir; rol ve yetki yok.
- **Kullanıcı girişi yok.** "Kim aldı" bilgisi ayarlardaki **isim etiketlerinden** seçilir; bunlar hesap değildir.
- Büronun mini PC sunucusunda çalışır, sadece ofis ağından erişilir.
- **Cihazlar:**
  - **Telefon:** fotoğraf, QR okutma, ürün alma ve yerine koyma, seri kayıt.
  - **Masaüstü:** arama, ürün bilgilerini tamamlama, plan ve bölme çizimi, kategori ve filtre yönetimi, etiket basma, koleksiyonlar, ayarlar.
  - **Tablet:** masaüstü düzenini kullanır. Kamerası olduğu için QR okutma ve fotoğraf da çalışır.
- **Ölçek:** başlangıçta 200–300 ürün; birkaç bin ürüne kadar yavaşlamadan çalışmalı.
- **Dil:** demo Türkçe, gerçek sürüm **Almanca** (terimler için bkz. 4.10). Para birimi **Euro**.

## 3. Ürün ilkeleri

1. **Kayıt girmek zahmetsiz olmalı.** Veri girişi üşendirdiği an uygulama ölür. Tek ürün için yol: fotoğraf, ad, kaydet. Çok ürün için seri kayıt (6.2). Ayrıntılar sonra tamamlanır.
2. **Her şey arayüzden yönetilir.** Kategori, filtre, oda, ünite, bölme, kişi ve plan kod yazmadan eklenir, düzenlenir, silinir.
3. **Fiziki ve dijital ürün net ayrılır ama birlikte aranır.** Ürünün türü her yerde bir bakışta anlaşılır. Dijital bir ürün tek adımda fiziki kayda çevrilebilir.
4. **Konum görsel gösterilir, yazıyla anlatılmaz.** Ünite planda, bölme fotoğrafta vurgulanır; yanında kısa bir kod durur (ör. **2.2.5**).
5. **Basılı etiketler kalıcıdır.** QR yalnızca değişmeyen bir kimlik taşır, konum taşımaz.
6. **Veri kaybı sessiz olmaz.** Ürünü konumsuz bırakan veya silen her işlem, kaydetmeden önce etkisini söyler.
7. **Çizim önce taslakta yapılır.** Kat planında ve ünite fotoğrafında yapılan değişiklikler "Kaydet" denene kadar kimseyi etkilemez. Her adım geri alınabilir (4.6).
8. **Asıl veri uygulamanın kendi çizimidir.** Odalar, üniteler ve bölmeler vektör veridir. Yüklenen PDF ya da görsel sadece altlıktır; kaldırılsa da hiçbir şey bozulmaz.
9. **Dosyalar kopyalanmaz.** Dokümanlar sunucudaki yerinde kalır; uygulama sadece yolunu bağlar.
10. **Sade ve hızlı.** Her ekranın tek bir ana işi olur. Yer, kullanım sıklığına göre verilir. Kontrol adımları atlanabilir.

## 4. Tasarım ilkeleri

Temel: **sade, kullanışlı, modern, minimal** (Zeiterfassung ile ortak). Kurallar ve kontrol listesi [DESIGN-PRINCIPLES.md](DESIGN-PRINCIPLES.md) dosyasında; bu bölüm onların miaza finds'e uygulanışıdır.

### 4.1 Marka: miaza iç sistemleri
Ailenin her uygulaması **"miaza" + tek bir İngilizce fiil** adını taşır:
- **miaza finds:** bu uygulama
- **miaza counts:** Zeiterfassung

**Logo yazısı:**
- **"miaza":** Figtree SemiBold (600), metin renginde. Her uygulamada aynıdır (D-002).
- **Fiil ("finds"):** "miaza"nın yaklaşık %60'ı boyutunda, Figtree Medium (500), uygulamanın vurgu renginde.
- İki kelime aynı taban çizgisinde durur. Dar yerlerde sadece "m" harfi ve vurgu renginde bir nokta kullanılır.

**Açılış ekranı:**
- Sadece soğuk açılışta (tarayıcı oturumunda ilk kez) görünür ve **en fazla 700 ms** sürer.
- Bir dokunuş ekranı hemen geçer. Veriyi beklemez; veri arkada yüklenir.
- Sayfa geçişlerinde görünmez. "Hareketi azalt" açıksa animasyonsuzdur.

### 4.2 Genel dil
- Telefon ve masaüstü aynı dili konuşur; ikisi de **mobil uygulama hissi** verir. Masaüstü sadece fazla alanı akıllıca kullanır: kalıcı filtre sütunu, yandan açılan ürün paneli.
- Ekranlar kart tabanlıdır. Görseller büyüktür; ürünler varsayılan olarak ızgarada gösterilir.
- **Gerçek tasarımda önce kütüphane cilalanır** (arama hızı, sonuç sıralaması, seçili filtrelerin görünüşü, ürün detayı). Ofis tarafı demoda daha çok ilerlemişti; iki ana işlev eşit ilgi görmeli.

### 4.3 Tema: açık ve koyu
- Seçenekler: **Sistem (varsayılan) · Açık · Koyu.** Seçim her cihazda ayrı saklanır.
- Yeri: **Ayarlar › Bu cihaz › Görünüm.** Kenar çubuğunda, üst çubukta veya ekranların başında durmaz.
- Bütün renkler değişken (token) olarak tanımlanır. İki tema baştan birlikte tasarlanır.
- Fotoğraflar iki temada da filtrelenmeden gösterilir.
- **Kat planı altlığı** koyu temada her zaman ters çevrilmiş ve soluk gösterilir; bunun bir ayarı yoktur.
- Etiketler ve dışa aktarılan PDF/Excel dosyaları her zaman açık renklidir.

### 4.4 Temel değerler (tasarımda kesinleşecek)

| Öğe | Açık | Koyu |
|---|---|---|
| Arayüz yazı tipi | Figtree (400, 500, 600); sayılar ve kodlar IBM Plex Mono (400, 500) — miaza counts ile aynı (D-002) | aynı |
| **Yazı ölçeği** | **11 · 12,5 · 13,5 · 15 · 19 · 28 · 52 px** (`--fs-mini … --fs-hero`, counts ile aynı; başka boyut kullanılmaz) | aynı |
| Zemin | `#F3F4F6` | `#0F1115` |
| Kart | `#FFFFFF`, kenar `#E7E9EE` | `#181B21`, kenar `#2A2F38` |
| Kart köşesi | 14–20 px | aynı |
| Metin / ikincil metin (≥ 4.5:1) | `#16181D` / `#5F6672` | `#ECEEF2` / `#A0A7B4` |
| Vurgu (tek renk) | `#2F5BEA` | `#6E8BFF` |
| Durum: Yerinde | `#DCFCE7` / `#166534` | `#14351F` / `#86EFAC` |
| Durum: Kullanımda | `#DBEAFE` / `#1E40AF` | `#172A4D` / `#93C5FD` |
| Durum: Büro dışında | `#FEF3C7` / `#92400E` | `#3A2A0B` / `#FCD34D` |
| Tür: Dijital | `#EDE9FE` / `#5B21B6` | `#2A1F4A` / `#C4B5FD` |
| Plan: odalar | nötr gri zemin, adı üzerinde | aynı, koyu tonda |
| Plan: ünite | yarı saydam, tek ton; seçili ünite vurgu renginde | aynı |

**Renk kuralı:** arayüzde renk sadece şu anlamları taşır: vurgu, üç durum, dijital tür. Kategori ve oda renkleri yoktur. Malzemenin kendi renkleri (fotoğraf, renk etiketleri) bu kuralın dışındadır.

- Renkler yalnızca tonla değil açıklıkla da ayrışır (renk körlüğü).
- Yazı tipleri sunucudan verilir; dış servisten çekilmez.

### 4.5 Bileşen kuralları
- **Dokunma hedefi:** en az 44 × 44 px.
- **Telefonda alt menü:** Kütüphane · Ofis · **Okut** (ortada, vurgulu) · Koleksiyonlar · Daha.
- **Masaüstünde sol menü:** Kütüphane · Ofis · Koleksiyonlar · Etiketler · Ayarlar; altta "Yeni ürün". Kenar çubuğunda başka seçenek durmaz.
- **Masaüstünde Okut:** üst çubukta, arama kutusunun yanında küçük bir QR ikonu. Kameralı cihazda kamerayı açar ve telefonla aynı sonuca gider. Kamera yoksa ikon gizlenir; kod arama kutusuna yazılabilir ("265" yeterli).
- **Filtreler:** telefonda alttan açılan panelde, masaüstünde her zaman açık sol sütunda. Seçili filtreler arama alanının altında, çarpıyla kaldırılabilen etiketler olarak durur.
- **Bildirimler:** kısa ve olguyu söyler ("Yerine konuldu · 2.2.5"); ekranın kenarında belirir. Hızlı işlemlerin bildiriminde birkaç saniye **"Geri al"** bulunur.
- **Görsel ekleme her yerde iki yolludur:** "Fotoğraf çek" ve "Görsel seç". Masaüstünde ayrıca sürükle-bırak ve yapıştırma çalışır.
- **Açıklama metni son çaredir.** Ekran başına en fazla bir kısa açıklama olur. Bir şeyin nasıl kullanılacağı ancak yazıyla anlatılabiliyorsa önce tasarım düzeltilir. Örneğin plan görüntüleme modunda çizim araçları gri ama görünürdür; bu yüzden "Düzenle'ye bas" yazısına gerek kalmaz.
- **Tek ad kuralı:** aynı şeyin her ekranda tek bir adı vardır (4.10).
- İkonlar çizgi ikondur; emoji yok. Telefonda yatay sayfa kaydırması olmaz.

### 4.6 Çizim düzenleme: taslak, geri al, kaydet, vazgeç
Bu düzen **sadece çizimde** kullanılır: kat planı (odalar, üniteler, altlık hizalama) ve ünite fotoğrafı (bölmeler). Formlar (ürün, kategori, filtre, kişi, ayarlar) basit **Kaydet / Vazgeç** ile çalışır.

- **"Düzenle" ile girilir.** Üstte sabit bir çubuk bulunur: **Geri al · Yinele · [n değişiklik] · Vazgeç · Kaydet**.
- **Taslak:** her şey önce taslakta tutulur. "Kaydet"e kadar başkaları eski hali görür.
- **Geri al / Yinele:** her adım ayrıdır; en az 50 adım. Kısayollar: Ctrl+Z, Ctrl+Shift+Z / Ctrl+Y. Silme de geri alınabilir bir adımdır; bu yüzden düzenleme içindeki silmelerde ayrıca onay sorulmaz.
- **Kaydet:** değişiklik ürünleri etkiliyorsa önce kısa bir özet gösterilir, ör. *"2 bölme silinecek; 3 ürün konumsuz kalacak · 1 ünite yeniden numaralandı; 6 bölme etiketi yeniden basılmalı."* Hepsi tek seferde kaydedilir; yarım kayıt olmaz.
- **Vazgeç:** değişiklik varsa "n değişiklik kaybolacak" diye sorar.
- **Kaydetmeden çıkış:** başka sayfaya geçmeye veya sekmeyi kapatmaya çalışınca uyarır.
- **Aynı anda iki kişi:** bkz. 4.9.

### 4.7 Hareket ve etkileşim
Efektler uygulamayı **anlaşılır ve canlı** yapar; süs olmaz, kullanımı zorlaştırmaz.

**Kullanılanlar:**
- **Plan yakınlaşması:** üniteye dokununca plan o üniteye yumuşakça yaklaşır.
- **Ürün kartları:** ünitenin etrafında düzenli bir yay üzerinde açılır. Aranan ürün öne çıkar ve tek farklı duran kart odur.
- **Bölme kartları:** bölme seçilince içindeki ürünler yelpaze gibi açılır.
- **Spot ışığı:** fotoğrafta seçili bölme dışında her yer kararır.
- **Fareyle önizleme (masaüstü):**
  - Üniteye gelince küçük önizleme: ürün sayısı ve küçük resimler.
  - Bölmeye gelince spot ışığı önizlemesi.
  - Karta gelince kart hafifçe yükselir.
  - Koşullar: sadece fareli cihazda çalışır; yaklaşık 300 ms gecikmeyle açılır; tıklanacak hedefin üstünü örtmez.

**Kurallar:**
- Geçişler 150–800 ms arasıdır; animasyon sürerken de tıklanabilir.
- Hedefler fareyi takip ederek yer değiştirmez.
- "Hareketi azalt" açıksa animasyonlar kısalır veya kapanır.

**Çok ürünlü durumlar:**
- Ünite çevresinde tek tek ürün yerine dolu bölmeler kart destesi olarak gösterilir (en fazla 18 deste).
- Yelpaze 7 karttan sonra yana kaydırılan bir şeride dönüşür.
- Sığmayan kısım için "+N" kartı gösterilir.

### 4.8 Plan ve fotoğrafta gezinme

| | Görüntüleme | Düzenleme modu |
|---|---|---|
| Kaydırma, fare | boş alanda sol tuşla veya orta tuşla sürükle | orta tuşla sürükle veya Boşluk + sol tuş |
| Yakınlaştırma, fare | tekerlek, imlecin olduğu noktaya doğru | aynı |
| Dokunmatik | tek parmakla kaydır, iki parmakla yakınlaştır | iki parmakla kaydır ve yakınlaştır (tek parmak çizer) |
| Sıfırla | "Sığdır" düğmesi, çift dokunuş | "Sığdır" düğmesi |

- Yakınlaştırma planın tamamı ile yaklaşık 8× arasında sınırlıdır. Plan ekran dışına kaçamaz.

### 4.9 Aynı anda düzenleme: "Düzenleniyor" uyarısı
Amaç: iki kişinin aynı kaydı habersizce düzenleyip birbirinin işini ezmemesi. Hesap ve kilit yönetimi olmadan, kendiliğinden kalkan bir işaretle yapılır.

> Not: Bu uyarının adı **"Düzenleniyor"**dur. "Kullanımda" kelimesi sadece ürün durumu için kullanılır (6.7).

**Kapsadığı kayıtlar:**
- Ürün formu
- Koleksiyon (ad, ürünler, miktarlar, vergi)
- Kat planı ve ünite fotoğrafı düzenleyicisi
- Kategori ve filtre ayarları

**Kapsamadıkları:**
- Görüntüleme her zaman serbesttir.
- Tek dokunuşluk hızlı işlemler engellenmez: ürünü al, yerine koy, koleksiyona ekle.

**Akış:**
1. Düzenlemeye girilince sunucu o kayda bir işaret koyar: kim ve ne zamandan beri. "Kim" bilgisi bu cihazın kişisidir (Ayarlar › Bu cihaz); seçilmemişse "başka bir cihaz" yazar.
2. Başka biri aynı kaydı düzenlemek isterse kısa bir uyarı görür: *"Düzenleniyor · Selin bu ürünü düzenliyor (4 dk)."* Kayıt salt okunur açılır; görüntüleme, alma ve dışa aktarma çalışır.
3. Koleksiyonda uyarı üstte ince bir şerit olarak durur; düzenlenebilir alanlar kilitlidir.
4. Kayıt serbest kalınca bekleyen kişiye bildirim gelir: *"Artık düzenleyebilirsin."*

**İşaret kendiliğinden kalkar:**
- Kaydet, Vazgeç veya sayfadan çıkışta.
- Cihaz 2 dakika sinyal göndermezse.
- 15 dakika hiç değişiklik yapılmazsa.

Bu yüzden elle kaldırılması gereken bir kilit yoktur.

**Yedek güvenlik:** Yine de çakışma olursa sürüm kontrolü ikinci kaydı reddeder: *"Bu kayıt bu arada değişti; güncel hali yükle."*

### 4.10 Terim sözlüğü (tek ad kuralı)
Her kavramın tek bir adı vardır; ekranlarda, bildirimlerde ve belgelerde aynı ad kullanılır. Almanca karşılıklar öneridir; kesin hali çeviride belirlenir (11, açık sorular).

| Kavram | Türkçe (demo) | Almanca (öneri) | Not |
|---|---|---|---|
| Raf, dolap, çekmeceli eleman, tekerlekli dolap, kutu (2.1) | **Ünite** | **Einheit** | Türünü ünitenin isteğe bağlı adı söyler: "2.1 · Schrank links". Ayrı bir tür listesi yoktur. |
| Ünitenin alt alanı (2.1.5) | **Bölme** | **Fach** | Çekmece de bölmedir. |
| Bölmenin etiketi | Bölme etiketi | Fach-Etikett | |
| Yerine koyarken bölme QR'ını okutma | Bölme onayı | Fach bestätigen | |
| Ürün durumları | Yerinde · Kullanımda · Büro dışında | Am Platz · In Benutzung · Außer Haus | Filtrede de aynı adlar. |
| Konumu olmayan fiziki ürün | Konumsuz | Ohne Platz | |
| Başka cihazda düzenlenen kayıt | Düzenleniyor | Wird bearbeitet | |
| Proje listesi / moodboard | Koleksiyonlar | Sammlungen | Telefon menüsünde de aynı ad. |
| QR okutma | Okut | Scannen | |
| Fiyat birimi | "/ m²" biçiminde, kelimesiz | "/ m²"; dışa aktarımda sütun adı **ME** | "Einheit" kelimesi fiyatta kullanılmaz; ünite ile karışır. |

- **"Kütüphane" bölümünün Almanca adı** kesinleşirken dikkat: doküman klasörünün adı da "Bibliothek". İkisi karışmamalı (ör. bölüm "Bibliothek", klasör "Dokumente"; ya da tersi).

## 5. Bilgi mimarisi

```
Kütüphane ─ arama, filtreler, ızgara/liste ─▶ ürün detayı
Ofis ─ kat planı ─▶ ünite ─▶ fotoğraf ve bölmeler ─▶ ürün kartları
Okut ─ ürün QR'ı ─▶ ürünü al / yerine koy (─▶ bölme onayı)
     └ bölme QR'ı ─▶ bu bölmede ne olmalı / buraya yerleştir / buraya seri kayıt
     (telefonda alt menünün ortası; masaüstünde üst çubukta küçük ikon)
Koleksiyonlar ─ proje listeleri, moodboard ─▶ sipariş listesi (v2)
Daha (telefon) ─ istatistik
             └ Ayarlar ─ kişiler; bu cihaz: kullanan kişi, görünüm
```

**Masaüstü Ayarlar, üç sekme:**
- Kategoriler ve filtreler
- Ofis planı ve üniteler
- Genel: kişiler, bölme onayı, doküman klasörü, yedek, bu cihaz, görünüm
- En altta küçük bir bağlantı: **Systembereich** (şifreli, 6.13)

**Telefon ve masaüstü iş bölümü:**
- Kategori, filtre, plan ve etiket baskısı sadece masaüstündedir.
- Telefonda ürün detayındaki "Baskı listesine ekle" vardır; baskının kendisi masaüstünden yapılır.

## 6. Fonksiyonel gereksinimler

### 6.1 Kütüphane
- **Tek arama kutusu:** ad, marka, ürün kodu (tamamı veya sadece numarası, ör. "265"), seri, özellik değerleri (ör. "R11") ve bölme kodu (ör. "2.2") içinde arar. Büyük/küçük harf ve Almanca özel harfler (ä/ae, ß/ss) duyarsızdır.
- **Tür seçimi:** Tümü / Fiziki / Dijital.
- **Ortak filtreler:** kategori, renk, fiyat aralığı, marka, durum.
- **Durum filtresi:** Tümü · Yerinde · Kullanımda · Büro dışında · **Konumsuz** · **Eksik bilgi**.
  - *Konumsuz:* bölmesi olmayan fiziki ürün. Konumsuz ürünler için ayrı bir ekran yoktur; bu filtre o listedir.
  - *Eksik bilgi:* seri kayıttan kalan, adı veya kategorisi tamamlanmamış ürün (6.2).
- **Kategoriye özel filtreler:** kategori seçilince o kategorinin filtreleri görünür (6.3).
- Masaüstünde kategori sayıları diğer filtrelere göre güncellenir.
- **Durum satırı (masaüstü):** kütüphane başlığında tek satır, ör. "28 kayıt · 2 büro dışında · 3 konumsuz · 5 eksik". Her sayı tıklanınca ilgili filtreyi açar. Telefondaki İstatistik ekranının masaüstü karşılığıdır.
- **Kart:** görsel, ad, marka, kategori, fiyat; dijitalse veya yerinde değilse durum rozeti.
- Masaüstünde karta gelince konum kodu belirir; tıklanınca ofis planında gösterir.
- Ürün detayı telefonda tam ekran, masaüstünde sağdan açılan panelde açılır.

### 6.2 Ürün kaydı
- **Alanlar:** tür (fiziki/dijital), ad, marka, kategori, ebat, ürün linki, fotoğraf(lar), adet, renkler, not, kategoriye özel alanlar.
- **Zorunlu olan sadece ad.** Kategori son kullanılan kategoriyle gelir. Gerisi sonra tamamlanır.
- **Fotoğraf:** çekilir veya mevcut görsel seçilir (4.5). Sunucu önizleme boyutlarını kendisi üretir.
- **Fiyat:** değer (€), birim (m², m, adet, paket) ve girildiği tarih. Fiyat güncellenince tarih bugün olur.
- **Renkler:** sabit bir paletten elle seçilir (beyaz, bej, kahve, terracotta, altın, pembe, yeşil, mavi, gri, siyah); tek dokunuşla. Fotoğraftan otomatik çıkarma v2'dedir.
- **Konum (fiziki ürün):** ünite seçilir, sonra fotoğrafta bölmeye dokunulur.
- **Dijitalden fizikiye çevirme:** tek adımda yapılır. Kod, bilgiler, fiyat ve dokümanlar korunur; konum seçilir, etiket baskı listesine eklenir.

#### Seri kayıt (telefon)
Başlangıçta 200–300 ürün girileceği için ana iş budur: rafın önünde durup ürünleri art arda kaydetmek.

1. **Başlatma:** iki yoldan biri.
   - Bir bölmenin QR'ı okutulur → "Buraya seri kayıt".
   - "+" → "Seri kayıt" ve isteğe bağlı bölme seçimi.
   
   İlk adımda kategori seçilir; son kullanılan önceden gelir.
2. **Kamera açık kalır.** Her fotoğraf hemen bir ürün olur:
   - Kodu ve envanter numarası verilir.
   - Konumu seçili bölmedir.
   - Adı geçici olarak "Adsız · 265" yazar.
   
   Altta sayaç ("12 ürün") ve son çekilenin küçük resmi görünür. Son fotoğraf tek dokunuşla geri alınabilir.
3. **"Bitti":** "12 ürün eklendi · etiketleri baskı listesinde". Etiketler hemen basılabilir, çünkü QR sadece envanter numarasını taşır.
4. **Tamamlama:** adı veya kategorisi eksik ürünler kütüphanede **"Eksik bilgi"** filtresinde toplanır. Masaüstünde liste görünümünde art arda doldurulur: ad yaz, Enter, sıradaki.

Seri kayıt yeni bir ekran açmaz. Mevcut kamera, mevcut bölme seçimi ve mevcut filtre kullanılır.

#### Ürün silme
- Ürün detayı › "Sil". Bu işlem düzenleme modu dışında olduğu ve geri alınamadığı için onay sorar: *"FL-004-142 silinecek. Envanter numarası 142 bir daha kullanılmaz; basılı etiketi geçersiz olur."*
- Ürünün çıkış kayıtları ve dokümanlarla bağları birlikte silinir. Doküman dosyalarının kendisine dokunulmaz.
- Etiketi baskı listesindeyse listeden düşer.

#### Toplu düzenleme (masaüstü, D-012)
Amaç: onlarca ürünün kategorisini veya ortak bir özelliğini tek seferde değiştirmek (ör. "Diğer"deki ürünler kendi kategorisine taşınınca).

- **Yeri:** kütüphanenin liste görünümü › "Auswählen". Ürünler tek tek işaretlenir veya filtre sonucunun tamamı seçilir ("alle 24 auswählen"). Telefonda yoktur.
- **Değişebilen alanlar:** kategori, marka, tür (fiziki/dijital), renk ekle / renk kaldır. Seçilenlerin hepsi aynı kategorideyse kategoriye özel filtre değerleri de. Ad, link, not ve fiyat toplu değişmez.
- **Kategori değişince** iki sonuç panelde, uygulamadan önce yazar:
  - Kod sorusu (6.2) bir kez sorulur, hepsine uygulanır; yenilenen kodların etiketleri baskı listesine girer. Envanter numarası değişmez.
  - Eski kategorinin filtre değerleri kaldırılır. Örnek: *"24 Produkte nach Fliese verschieben · 24 Codes neu · 18 Filterwerte entfallen"*.
- **Onay penceresi yok:** etki panelde görünür, "Anwenden" ile uygulanır; ardından birkaç saniye "Rückgängig". Geri alma kaldırılan değerleri ve eski kodları da geri getirir; harcanan numaralar geri dönmez.

#### Ürün kodu
Biçim: **`KK-KKK-EEE`**, ör. **`ST-005-265`**.

| Parça | Anlamı | Örnek |
|---|---|---|
| `KK` | Kategori öneki, 2 harf | `FL` Fliese, `HO` Holz, `ME` Metall, `ST` Stoff |
| `KKK` | Kategorideki sıra numarası | `005`: 5. kumaş |
| `EEE` | **Envanter numarası:** tüm envanterde benzersiz, sırayla verilir | `265` |

- **Önek:** kategori ayarlarında girilir; zorunlu ve benzersizdir. Uygulama addan bir öneri getirir. "Diğer" kategorisi için `XX` önerilir.
- **Basamak:** numaralar 3 haneyle başlar, 999'dan sonra 4 haneye geçer.
- **Dijital ürünler** de aynı şemayla kod alır; fizikiye çevrilince kod değişmez.
- **Numaralar asla yeniden kullanılmaz.** Tek istisna: Systembereich › "Alles löschen (Neuanfang)" sayaçları 1'e döndürür (D-013); öncesinde basılmış etiketlerin geçersiz olacağı yazılır.
- **Envanter numarası ürünün kalıcı kimliğidir.** QR sadece bu numarayı taşır.
- **Kategori değişirse:** kod aynı mı kalsın, yeni önekle mi yenilensin diye sorulur. Envanter numarası her durumda aynı kalır; yenilenirse etiket baskı listesine eklenir.
- **Önek sonradan değişirse:** kaç kodun değişeceği ve kaç etiketin yeniden basılacağı söylenir.

### 6.3 Kategoriler ve filtreler (masaüstü › Ayarlar)
- **Kategori:** eklenir, adlandırılır, öneki girilir. **Sadece boş bir kategori silinebilir** (D-011). İçinde ürün olan kategori yalnız düzenlenir; silme yerine kaç ürün içerdiği gösterilir ("24 Produkte"), ürünler gerekirse önce toplu düzenlemeyle başka kategoriye taşınır. "Diğer" (Sonstiges) her zaman vardır ve silinemez.
- **Filtreler:** her kategorinin kendi filtre listesi vardır. Filtreler eklenir, silinir, sıralanır; bu sıra filtre panelindeki sıradır.
- **Kaydetme:** basit form, **Kaydet / Vazgeç**. Geri al çubuğu yoktur (4.6).
- **Filtre tipleri:**

| Tip | Anlamı | Ürün formunda | Filtrede | Örnek |
|---|---|---|---|---|
| Ölçü | sayı ve birim | sayı + birim (mm, cm, m, kg, adet) | en az – en çok | Kalınlık 8–12 mm |
| Tekli seçim | değerler birbirini dışlar | listeden **bir** değer | birden fazla seçenek işaretlenebilir | R değeri: R9 *ya da* R10 |
| Çoklu seçim | değerler birbirinden bağımsız | listeden **birden fazla** değer | seçeneklerden biri eşleşirse | Yüzey: Mat *ve* Yapılı |
| Var / yok | tek özellik | Var / Yok | Fark etmez / Var / Yok | Rektifiye: Var |

- **Filtre ekleme akışı:** kategori → tip (her tipin yanında yukarıdaki örnek yazar) → ad → seçenekler veya birim → kaydet.
- Mevcut filtrenin seçenekleri sonradan düzenlenebilir: eklenir, yeniden adlandırılır, silinir. Silinen bir seçenek kaç üründe kullanılıyorsa önce söylenir.

### 6.4 Ofis planı, odalar, üniteler, bölmeler

**Vektör veri ve altlık:**
- Planın asıl verisi uygulamada çizilen **odalar ve ünitelerdir**.
- **Altlık** (PDF, PNG veya JPG) isteğe bağlıdır ve sadece çizerken yol gösterir. PDF'in ilk sayfası sunucuda görsele çevrilir.
- Altlık **"Altlığı hizala"** aracıyla taşınır, ölçeklenir ve 90° döndürülür. Altlık değişse veya silinse de çizimlere dokunulmaz.
- **Görünürlük:**
  - Düzenleyicide: göster / gizle. Görünüm sabit ve soluktur; ayrı bir saydamlık ayarı yoktur.
  - Ofis görünümünde: Ayarlar › Ofis planı › "Altlığı ofis görünümünde göster".
  - Altlık gizliyken ofis görünümü nötr odaları (adlarıyla) ve üniteleri gösterir.
- Plan ölçekli değildir.

**Çizim öğeleri:**
- **Odalar:** dikdörtgen veya poligonla çizilir; adı verilir; taşınır, köşeleri düzenlenir, silinir. Rengi seçilmez. Odanın numarası ünite kodlarının ilk hanesidir. Oda ayrımı **sadece** bu çizimle yapılır.
- **Üniteler:**
  - Dikdörtgen veya poligonla çizilir.
  - Bulunduğu odaya otomatik bağlanır ve sıradaki kodu alır (ör. 4.1); kod elle değiştirilebilir.
  - **İsteğe bağlı bir adı** olur ("Schrank links", "Rollcontainer").
  - Hiçbir odanın içinde olmayan ünite uyarıyla işaretlenir.
- **Ünite fotoğrafı:** çekilir veya mevcut görsel seçilir.
- **Bölmeler:** fotoğraf üzerinde dikdörtgen veya poligonla çizilir. Raf gözü, kapaklı bölme veya çekmece fark etmez; hepsi bölmedir.
- **Kod şeması:** `Oda.Ünite.Bölme`, ör. **2.2.5**.

**Numaralama:**
- Yeni bölme **sona eklenir**; mevcut kodlar kendiliğinden değişmez.
- "Yeniden numarala" komutu bölmeleri soldan sağa, yukarıdan aşağı sıralar. Ürünler bölmeleriyle birlikte yeni koda geçer; o ünitenin bölme etiketleri baskı listesine eklenir.

**Silme:** ünite veya bölme silinince içindeki ürünler konumsuz kalır. Bu, kaydetmeden önce söylenir (4.6); ürünler "Konumsuz" filtresinde görünür.

**Düzenleme yeri:** çizim masaüstündedir. Telefonda sadece ünite fotoğrafı yüklenebilir.

### 6.5 Konum bulma senaryoları
1. **Ürünü bul:** kütüphanede ara → "Ofiste göster" → plan üniteye yaklaşır, kartlar açılır, ürün öne çıkar → "Fotoğrafta göster" → bölme spot ışığıyla vurgulanır.
2. **Bölme QR'ı okut:** ünitenin fotoğrafı açılır, bölme vurgulanır, içinde olması gereken ürünler gösterilir.
3. **Gezinme:** plan → oda → ünite → bölme → ürünler.
4. **Yerine koy:** ürün QR'ı → plan ünitesi → bölme → "Yerine koy" (6.7).

### 6.6 QR kodları ve etiketler
- **Ürün QR'ı** sadece envanter numarasına giden kalıcı linki içerir (ör. `…/p/265`).
- **Ürün etiketi:** ad, QR ve ürün kodu. **Konum yazmaz.**
- **Bölme etiketi:** QR (bölmenin değişmeyen iç kimliği) ve büyük yazılı bölme kodu (2.2.5). Yeniden numaralamada QR geçerli kalır, sadece yazı eskir.
- **Etiket yazdırma (masaüstü › Etiketler):**
  - Arama (kelimenin bir kısmıyla) ve hazır seçimler: "bulunanları seç", "basılmamışlar", "yeniden basılacaklar", "temizle".
  - Seçilenler A4'e otomatik dizilir; sağda önizleme görünür.
  - **Düzen, kullanılan etiket kâğıdından gelir.** Hazır kesim çizgili yapışkanlı A4 kâğıt kullanılır; etiketler çekip çıkarılır. Kâğıdın düzen PDF'i alınır ve etiket ölçüleri, kenar boşlukları ve aralıklar buna göre bir **düzen tanımı** olarak kaydedilir (yaklaşık 20'li, ≈ 48 × 52 mm). Kâğıt değişirse sadece bu tanım değişir; kod değişmez.
  - İlk sürümde tek bir düzen tanımı vardır. Birden fazla kâğıt türünü yöneten bir ekran yoktur.
  - Çıktı PDF olarak alınır; basılanlar "basıldı" olarak işaretlenir.
- **Brother etiket yazıcısı:** v2, model teyit edilince.

### 6.7 Ürün alma ve yerine koyma
- **Ürünü al:** kim (bu cihazın kişisi önceden seçili), nereye (büro içinde / büro dışına), not.
- **Durumlar:**
  - **Yerinde**
  - **Kullanımda:** büro içinde, kişi adıyla
  - **Büro dışında:** kişi adı ve tarihle
  
  Bu üç ad her yerde aynıdır (4.10).

**Yerine koy ve bölme onayı:**
Amaç: ürünün doğru bölmeye konduğunu, kullanıcıyı yormadan doğrulamak.

1. Ürün QR'ı okutulur (veya detaydan "Yerine koy"). Plan ve fotoğrafta bölme gösterilir.
2. **"Yerine koy"a basılınca kamera açılır:** *"Bölmenin etiketini okut · 2.2.5"*. Altta her zaman **"Okutmadan onayla"** vardır.
3. Sonuçlar:
   - **Doğru bölme:** kısa titreşim, yeşil onay, "Yerine konuldu · 2.2.5".
   - **Başka bölme:** *"Bu ürünün yeri 2.2.5. Okuttuğun bölme 2.3.1."* → "2.2.5'e götüreceğim" veya "Yeni yeri 2.3.1 olsun".
   - **Okutmadan onayla:** durum "Yerinde" olur; kayıtta "onaysız" diye işaretlenir. Kullanıcı sorgulanmaz.
4. **Toplu yerleştirme:** önce bölme QR'ı okutulur ("Buraya yerleştir"), sonra ürünler art arda okutulur. Yeri başka olan ürün için yukarıdaki soru sorulur.
5. **Ayar: Bölme onayı Açık (varsayılan) / Kapalı.** Kapalıyken "Yerine koy" kamerasız, tek dokunuşla biter.

### 6.8 Koleksiyonlar ve sipariş listesi
- Koleksiyon bir proje listesi veya moodboard'dur; fiziki ve dijital ürün karışık olabilir.
- Ürün detayından bir veya birden fazla koleksiyona eklenir.
- **Sipariş listesi (v2):**
  - Her ürün için miktar girilir; satır toplamı ve net toplam hesaplanır.
  - **Vergi isteğe bağlıdır:** "MwSt. ekle" anahtarı, varsayılan oran **%20**, liste bazında değiştirilebilir.
  - Her satırda fiyatın tarihi görünür; fiyatı olmayan ürün varsa uyarı verilir.
  - **Dışa aktarma:** PDF veya Excel.
    - **Fiyatlı:** birim fiyat, fiyat tarihi, satır toplamları, net, isteğe bağlı vergi ve brüt.
    - **Fiyatsız (miktar listesi):** kod, ad, marka, miktar ve ME.
  - Tutarlar Almanca biçimde yazılır: `1.234,56 €`.

### 6.9 Dokümanlar
- Ürüne PDF, JPG veya PNG doküman bağlanır. Dosya **kopyalanmaz**; ayarlarda tanımlı **tek doküman kök klasörünün** içinden seçilir.
- Yol bu klasöre göre göreli saklanır. Paylaşımın adı değişirse sadece ayardaki kök yol güncellenir.
- **Aç:** dosya tarayıcıda görüntülenir.
- **Klasörde göster (v2):** küçük bir yardımcı ile Windows Gezgini açılır. Yardımcı yoksa yol panoya kopyalanır.
- Taşınmış veya silinmiş dosya "bulunamadı" olarak işaretlenir.

### 6.10 İstatistik
- **Telefon (Daha › İstatistik):** toplam, fiziki, dijital, yerinde olmayan, konumsuz ve eksik bilgili ürün sayıları ve kategori dağılımı. Her sayı kütüphanede ilgili filtreyi açar.
- **Masaüstü:** kütüphane başlığındaki durum satırı (6.1).

### 6.11 Ayarlar (özet)

| Ayar | Yer | Kime ait |
|---|---|---|
| Kategoriler ve filtreler | Masaüstü | büro |
| Ofis planı, üniteler, altlığı ofiste göster | Masaüstü | büro |
| Kişiler | Masaüstü, telefon | büro |
| Bölme onayı (Açık/Kapalı) | Masaüstü › Genel | büro |
| Doküman kök klasörü | Masaüstü › Genel | büro |
| Yedek durumu | Masaüstü › Genel | büro |
| Yedek alma ve geri yükleme, toplu silme, veri kümesi değiştirme | Systembereich (şifreli, 6.13) | yönetici |
| Bu cihazı kullanan | Her cihazda | cihaz |
| Görünüm (tema) | Her cihazda | cihaz |

### 6.12 Yeni özellik ölçütü
Bir özellik ancak şu soruların cevabı somutsa eklenir:
1. **Kanıt:** Bu eksik yüzünden kullanıcı bugün ne yapıyor (kâğıt not, yan tablo, mesaj, arayıp durmak)?
2. **İş cümlesi:** "Kullanıcı ___ yapabilmek için bunu ister."
3. **En küçük hal:** Mevcut bir akışın içine sığıyor mu? Yeni ekran gerekiyor mu?
4. **Biri girerken biri çıkar mı?** Yeni parça eski bir parçayı gereksiz kılıyorsa o parça kaldırılır.

**Kanıt bekleyen fikirler** (şimdilik yok):
- Aynı ürün iki kez girilince uyarı.
- Dışarıdaki ürün için dönüş tarihi ve hatırlatma.
- Bir ürünün birden fazla yerde durması.
- Kurulum sihirbazı (yerine kurulum belgesi yazılır).

### 6.13 Systembereich (şifreli yönetim alanı, D-006)
Seyrek yapılan ama yanlışlıkla yapılınca ağır sonuç doğuran işlerin tek yeri. Uygulamanın geri kalanı girişsiz kalır.

- **Yeri:** Ayarlar sayfasının en altında küçük bir bağlantı. Menüde, kenar çubuğunda veya ana ekranda görünmez.
- **Giriş:** tek yönetici, kullanıcı adı ve şifreyle. İlk açılışta oluşturulur. Oturum sadece bu alan için geçerlidir ve kısa sürer.
- **Güvenlik anahtarı (D-010):** ilk kurulumda bir kez gösterilir. Yazdırılır veya indirilir ve güvenli bir yerde saklanır (ör. kasadaki çıktı, şifre yöneticisi). Şifre unutulursa bu anahtarla yeni şifre belirlenir. Anahtar bir kez kullanılınca geçersiz olur ve yenisi gösterilir. Sunucu anahtarın kendisini değil, yalnız özetini (hash) saklar.
- **İçindekiler:**
  - Yedek: şimdi yedek al, yedeği indir, yedekten geri yükle, son yedeğin zamanı.
  - **Veri taşıma (D-009):** sistem başka bir sunucuya taşınınca eski kurulumun verisi yenisine alınır.
    - Eski sunucuda: "Dışa aktar" tek bir dosya üretir (veritabanı + bütün fotoğraflar). Eski sunucu artık açılmıyorsa kopyalanmış veri klasörü de kabul edilir (`data/finds.db` + `media/`).
    - Yeni kurulumda: önce yönetici oluşturulur, sonra "Verileri al" ile dosya veya klasör seçilir. Mevcut veri kaldırılır, eskisi yüklenir (önce otomatik güvenlik yedeği alınır).
    - Eski bir sürümden gelen veri, açılışta güncel şemaya yükseltilir; daha yeni bir sürümden gelen veri reddedilir.
    - Yeni kurulumun yönetici şifresi ve güvenlik anahtarı geçerli kalır; eski kurulumunkiler alınmaz.
  - Toplu silme (D-013):
    - "Alle Produkte löschen": ürünler ve fotoğrafları; kategoriler, filtreler ve numara sayaçları kalır.
    - "Alles löschen (Neuanfang)": ürünler, kategoriler (Sonstiges hariç) ve filtreler; numaralar yeniden 1'den başlar (deneme verisinden sonra temiz başlangıç). Basılmış etiketler geçersiz olur.
  - Diğer güvenlik işleri (ör. şifre değiştirme, güvenlik anahtarını yenileme).
- Her işlem öncesinde etkisi yazılır ("280 ürün ve 1.140 fotoğraf silinecek"). Geri dönüşü olmayan her işlemden önce kendiliğinden yedek alınır.

## 7. Veri modeli (özet)

| Varlık | Ana alanlar |
|---|---|
| Kategori | id, ad, önek (2 harf, benzersiz), sabit mi, sıra, sonraki kategori no |
| Filtre | id, kategori, ad, tip (ölçü / tekli / çoklu / var-yok), seçenekler, birim, sıra |
| Ürün | **envanter no (kalıcı kimlik)**, kategori no, kod, tür, ad, marka, kategori, ebat, link, adet, not, özellik değerleri, renkler, bölme, etiket durumu, eksik bilgi mi, eklenme tarihi, sürüm |
| Fiyat | ürün, değer, birim, para birimi (€), tarih |
| Fotoğraf | ürün, dosya, sıra |
| Doküman | ürün, göreli yol, tür |
| Çıkış kaydı | ürün, kişi, büro içi/dışı, not, alınma tarihi, iade tarihi, bölme onaylı mı |
| Kişi | ad |
| Kat planı | sürüm no, altlık dosyası, altlık konumu/ölçeği/dönüşü, ofis görünümünde göster |
| Oda | numara, ad, poligon |
| Ünite | kod, ad (isteğe bağlı), oda, poligon, fotoğraf, fotoğraf oranı |
| Bölme | iç kimlik, ünite, sıra no, poligon (fotoğrafa göre %), etiket durumu |
| Koleksiyon | ad, not, sürüm; satırlar: ürün, miktar; vergi açık mı, vergi oranı |
| Ayarlar | bölme onayı, doküman kök klasörü, yedek hedefleri |
| Düzenleme işareti | kayıt türü, kayıt id, kişi veya cihaz, başlangıç, son sinyal. Kalıcı değildir. |

- **Cihaz ayarları** (tema, bu cihazı kullanan) o cihazın tarayıcısında saklanır.
- Ürünün konumu bölmeye iç kimlikle bağlanır. Görünen kod (2.2.5) bundan türetilir; yeniden numaralama ürünleri yanlış yere düşürmez.
- Plan, odalar, üniteler ve bölmeler tek bir **plan sürümü** olarak kaydedilir.
- Ürün, koleksiyon ve kategori kayıtları da sürüm numarası taşır (4.9).
- Envanter ve kategori numaraları sayaçtan verilir; silme sayaçları geri almaz.

## 8. Teknik yaklaşım

### 8.1 Altyapı (miaza counts ile aynı)
- **Sunucu:** Python 3.12+, FastAPI, uvicorn, Jinja2. İki çalıştırma yolu da hazır tutulur (D-003): Docker (`Dockerfile`, `docker-compose.yml`) ve Windows için `start.bat` + `.venv`. Mini PC kurulunca kullanılmayan yol kaldırılır.
- **Portlar (D-001):** ailenin her uygulaması kendi port çiftini kullanır, asla paylaşmaz: counts 8080/8081, **finds 8090/8091** (beta/geliştirme), sonraki uygulamalar 8100/8101, 8110/8111 …
- **İstek koruması (D-007):** veri değiştiren her istekte tarayıcının gönderdiği köken (Origin) uygulamanın kendi adresi olmalıdır; Systembereich'te ayrıca counts'taki gibi oturum ve CSRF anahtarı.
- **Veritabanı:** SQLite, tek dosya (`data/finds.db`), WAL modunda.
- **Arayüz:** düz JavaScript, framework ve build adımı yok. Tek CSS dosyası, açık/koyu tema değişkenleri.
- **Kütüphaneler:**
  - ReportLab: PDF
  - pypdf
  - openpyxl: Excel
  - Pillow: önizleme boyutları
  - pypdfium2: PDF altlığı görsele çevirme
  - segno: QR üretme
- **Tarayıcıda QR okuma:** varsa yerleşik okuyucu (BarcodeDetector), yoksa uygulamayla gelen küçük bir JS okuyucu (jsQR). Dış CDN yok.
- **Testler:** pytest; her değişiklikten sonra hepsi koşar. Paketler `requirements.txt` içinde sabit sürümlerle.
- **Dil:** bütün arayüz metinleri tek bir sözlük dosyasında; terimler 4.10'a uyar. Varsayılan dil Almanca. Tarih `01.11.2026`, sayı `1.234,56`.
- **Performans:** arama ve filtre sonuçları < 200 ms. Görseller önizleme boyutlarında sunulur. Seri kayıtta fotoğraf yüklemesi arkada sürer; kamera beklemez.

### 8.2 Kamera ve HTTPS
Tarayıcılar, sayfa içinde canlı kamera görüntüsünü sadece güvenli bağlantıda (HTTPS) açar. Ofis ağında düz `http://192.168…` adresiyle canlı kamera çalışmaz.

**HTTPS olmadan da çalışanlar:**
- Ürün QR'ı telefonun kendi kamera uygulamasıyla okunur. Link ürün sayfasını açar.
- **"Fotoğrafla okut":** düğme telefonun kamera uygulamasını açar, fotoğraf çekilir, QR fotoğraftan okunur. Her okutmada bir deklanşör ve bir "fotoğrafı kullan" dokunuşu fazladan gerekir.
- Fotoğraf çekme ve seçme, seri kayıt dahil. Her fotoğrafta kamera uygulaması yeniden açılır.
- **Masaüstü (D-014):** localhost güvenli sayıldığı için "Foto aufnehmen" canlı kamera penceresi açar. Kamera yoksa veya bağlantı güvenli değilse düğme gizlenir.
- **QR adresi (D-014):** `MF_BASIS_URL` yoksa ve sunucu ağa açıksa (`start.bat netz`), localhost yerine bilgisayarın ofis ağı adresi kullanılır.

Tek ürünlük işlerde bu yeterlidir. Ama toplu yerleştirmede ve seri kayıtta, yani art arda okutmada yavaştır. Canlı kamera bu yüzden istenir.

**HTTPS almanın yolları** (mini PC'de bir kez kurulur; miaza counts da aynı yoldan yararlanır):

| Yol | Nasıl çalışır | Telefonda kurulum | Not |
|---|---|---|---|
| **A. Büronun alan adıyla gerçek sertifika** (önerilen) | Büronun alan adının altına bir ad açılır, ör. `finds.buro.miaza.at`. Bu ad, alan adı sağlayıcısının ayarlarında mini PC'nin ofis içi adresini gösterir. Sertifika Let's Encrypt'ten, internete hiçbir şey açılmadan, DNS doğrulamasıyla alınır ve kendiliğinden yenilenir (Caddy gibi bir sunucu bunu yapar). | **Hiçbir şey.** Her cihazda düz çalışır. | Gerekenler: alan adının yönetim erişimi ve sağlayıcının bu işe izin veren bir arayüzü (API). Bazı modemler (ör. FritzBox) ofis içi adrese çözülen dış adları güvenlik gereği engeller; modemde bu ad için bir kez istisna tanımlanır. Yenileme için mini PC'nin ayda bir kısa süre internete çıkması gerekir. |
| **B. Büronun kendi sertifika yetkilisi** | Mini PC'de bir kök sertifika üretilir (ör. mkcert), uygulama onunla imzalı sertifika kullanır. | Her telefona ve bilgisayara bir kez kök sertifika kurulur. iPhone'da profil yüklenip "tam güven" açılır; Android'de ayarlardan sertifika yüklenir. Kişi başı yaklaşık 3 dakika. | İnternet gerekmez. Yeni gelen her cihaza kurulum gerekir. |
| **C. Hiç HTTPS yok** | Sadece "Fotoğrafla okut". | Hiçbir şey. | Yukarıda anlatıldığı gibi, art arda okutmada yavaş. |

- **Karar:** Büronun bir alan adı ve yönetim erişimi varsa **A**, yoksa **B** (11, açık sorular).
- **Geliştirme sırası:** uygulama C ile de tam çalışacak şekilde yazılır. Canlı kamera, HTTPS varsa kendiliğinden devreye giren bir iyileştirmedir. Böylece HTTPS kararı kodlamayı bekletmez.

### 8.3 Klasör düzeni (mini PC)
```
DATA/
├─ Apps/
│  ├─ miaza-finds/
│  │  ├─ app/        kod ve docker-compose.yml
│  │  ├─ data/       finds.db
│  │  ├─ media/      ürün ve ünite fotoğrafları, önizlemeler, plan altlığı
│  │  ├─ backups/    yerel gece yedekleri
│  │  └─ logs/
│  └─ miaza-counts/  Zeiterfassung, aynı düzen
└─ Bibliothek/       doküman kök klasörü (datasheet, katalog, sertifika)
```
- Uygulama kendi klasörlerini yazılabilir, doküman kök klasörünü **salt okunur** bağlar.

### 8.4 Yedek
- Her gece 02:00: veritabanının güvenli kopyası ve `media/` klasörü.
- **Yerel:** `DATA/Apps/miaza-finds/backups/`, son 30 gece ve 12 ay sonu.
- **Google Drive:** Drive masaüstü uygulamasının eşitlediği klasöre kopya, son 14 gece. Uygulama Google'a doğrudan bağlanmaz.
- Ayarlarda son başarılı yedeğin zamanı görünür; 2 günden eskiyse uyarı çıkar.
- Geri yükleme adımları belgelenir ve kurulumda bir kez denenir.

### 8.5 Dış bağımlılık
Bulut servisi yok; her şey ofis ağında çalışır. v1'de internete ihtiyaç yoktur. Drive eşitlemesi Drive uygulamasının işidir.

## 9. İstenmeyen davranışlar

**Etkileşim ve görsel**
- ✗ Anlamsız efektler: 3B eğme (warp), parallax, dekoratif animasyon, rastgele açılar.
- ✗ Fareyi takip ederek kayan hedefler. Animasyon bitmeden etkileşimi engellemek.
- ✗ Kullanıcıyı bekleten açılış ekranı.
- ✗ Konumu sadece "Oda › Ünite › Bölme" metniyle anlatmak.
- ✗ Emoji ikonlar, gradyan süsler, birden fazla vurgu rengi, süs amaçlı renk (kategori, oda).
- ✗ Yazı ölçeği dışında yazı boyutu kullanmak.
- ✗ Değişkene bağlanmamış renkler; koyu temada okunmayan metin.
- ✗ Telefonda küçük dokunma hedefleri, yatay sayfa kaydırması.
- ✗ Görsel eklemeyi sadece kamerayla sınırlamak.
- ✗ Planın ekran dışına kaybolabilmesi.
- ✗ Dijital ve fiziki ürünün bir bakışta ayırt edilememesi.
- ✗ Seyrek kullanılanı merkeze koymak: tema, masaüstünde QR.
- ✗ Tasarımın eksiğini açıklama metniyle kapatmak; ekran başına birden fazla açıklama.

**Adlandırma**
- ✗ Aynı şeye iki ad ("Dışarıda" / "Büro dışında") veya aynı ada iki anlam ("Kullanımda" / "Düzenleniyor").
- ✗ Üniteye tek bir mobilya türünün adını vermek (her ünite raf değildir).

**Düzenleme**
- ✗ Çizimde geri al olmaması; formlara gereksiz geri al çubuğu koymak.
- ✗ Çizim değişikliğinin kaydedilmeden herkese yansıması.
- ✗ Kaydedilmemiş değişikliği uyarmadan atmak; yarım kayıt.
- ✗ Altlığı veri kaynağı gibi kullanmak.
- ✗ Aynı kaydın habersizce iki kişi tarafından düzenlenmesi; elle kaldırılması gereken kilitler.

**Veri ve davranış**
- ✗ Basılı etiketleri geçersiz kılan kendiliğinden yeniden numaralama.
- ✗ Etikete konum yazmak; konumu QR'a gömmek.
- ✗ Envanter numarasını yeniden kullanmak veya değiştirmek.
- ✗ Sessiz veri kaybı; düzenleme dışındaki geri alınamaz silmede (ürün silme) onay istememek.
- ✗ Bölme onayını kaçışsız kılmak.
- ✗ Dokümanları kopyalamak, taşımak veya doküman klasörüne yazmak.
- ✗ Ayarları ve arayüz metinlerini koda gömmek.
- ✗ Fiyatı tarihsiz göstermek; vergiyi zorunlu hesaplamak.
- ✗ Dış servislere bağımlılık.
- ✗ Aynı işi iki cihazda iki kez yapmak (ör. kategori düzenleme hem telefonda hem masaüstünde).

## 10. Sürüm kapsamı

**v1 (ilk çalışan sürüm)**
- Marka, kısa açılış ekranı, açık/koyu tema
- **Kütüphane** (tasarımda önce bu cilalanır): arama, ortak ve kategoriye özel filtreler, durum filtresi (konumsuz, eksik bilgi), ızgara/liste, masaüstü durum satırı
- **Ürün kaydı:** tek kayıt ve **seri kayıt**, kod şeması, fiyat ve tarihi, elle renk, dokümanlar, fotoğraf çek / görsel seç, ürün silme
- Kategori ve filtre yönetimi (masaüstü)
- **Kat planı düzenleyicisi:** oda, ünite, bölme; taslak, geri al/yinele, kaydet/vazgeç; altlık hizalama ve gizleme; kaydırma/yakınlaştırma
- Ofis görünümü ve dört konum senaryosu
- Ürün ve bölme QR'ları; A4 etiket PDF'i (20'li)
- **Okut:** telefonda ana menüde, masaüstünde ikincil ikon
- **Ürün alma ve yerine koyma;** bölme onayı (Açık/Kapalı) ve toplu yerleştirme
- "Düzenleniyor" uyarısı ve sürüm kontrolü
- Koleksiyonlar (miktarsız)
- İstatistik, kişiler, gece yedeği
- Almanca arayüz

**v2 ve sonrası**
- Sipariş listesi: miktar, fiyat hesabı, isteğe bağlı vergi, fiyatlı/fiyatsız PDF ve Excel
- Linkten doldurma, fotoğraftan otomatik renk
- Brother etiket yazıcısı
- Fiyat geçmişi
- "Klasörde göster" yardımcısı
- Kanıt gelirse: 6.12'deki bekleyen fikirler

**Demo ile ilgili not:** Demo, koleksiyonda v2'nin sipariş listesini de gösteriyor. Bu kısım demoda "sonraki sürüm" olarak işaretlenmelidir.

## 11. Açık sorular

**Cevaplananlar:**
- **0.2:**
  - Altyapı (8.1)
  - Yedek (8.4)
  - Klasör düzeni (8.3)
  - Ürün kodu (6.2)
  - Para birimi, dil, vergi (6.8)
- **0.3:**
  - Tema Ayarlar'da
  - Masaüstünde QR ikincil
  - Aynı anda düzenleme uyarısı
- **0.4:**
  - Terimler: Ünite/Einheit ve Bölme/Fach (4.10)
  - Tekli ve çoklu filtre ayrı (6.3)
  - Fareyle önizleme kalıyor (4.7)
  - Etiket baskısı sadece masaüstünde; filtre seçeneklerini düzenleme v1'de (onaylandı)
  - Ofisin ışığı QR okuma için yeterli
  - Etiket düzeni kâğıdın PDF'inden alınacak (6.6)

**Açık kalanlar:**
1. Brother etiket yazıcısının modeli nedir, çalışıyor mu?
2. **HTTPS yolu (8.2):** Büronun alan adı var mı (ör. miaza.at), yönetim erişimi kimde ve hangi sağlayıcıda? Varsa A, yoksa B. Ofiste hangi modem kullanılıyor?
3. Kullanılacak etiket kâğıdının düzen PDF'i (ürün adı ya da kâğıt). Gelince düzen tanımı ona göre yapılır.
4. Google Drive masaüstü uygulaması mini PC'de mi, başka bir bilgisayarda mı?
5. Almanca biçimler Avusturya'ya göre mi (de-AT)? Durum adlarının ve "Kütüphane" bölümünün Almanca adları da bu turda kesinleşir (4.10).
6. "finds" ve "counts" vurgu renkleri, aile içinde birbirinden ayrışacak şekilde tasarımda belirlenecek.

## 12. Hayır listesi: bilerek yapılmayanlar

- Kullanıcı hesabı, şifre, rol ve yetki. Tek istisna: Systembereich'in yönetici şifresi (6.13); uygulamanın geri kalanı girişsizdir.
- Stok yönetimi, sipariş takibi, muhasebe.
- "Numune istendi" gibi ara durumlar.
- Kilit yönetimi ekranı.
- Kategori ve oda renkleri; birden fazla vurgu rengi.
- Telefonda kategori, filtre ve plan düzenleme; telefondan etiket baskısı.
- Birden fazla doküman klasörü; 40'lı etiket düzeni.
- Taslağı kaza sonrası geri getirme.
- Ünite türleri için ayrı bir liste.
- Ofis dışından erişim (gerekirse ayrıca değerlendirilir).
