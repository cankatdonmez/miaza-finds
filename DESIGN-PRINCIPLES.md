# miaza iç sistemleri — Tasarım İlkeleri

Sürüm: 1.0 · 01.11.2026
Geçerli olduğu uygulamalar: **miaza finds** (malzeme kütüphanesi ve ofis düzeni), **miaza counts** (Zeiterfassung) ve ailenin sonraki uygulamaları.

Bu dosya her tasarım ve kod kararında başvurulan yol göstericidir. Yeni bir ekran, özellik veya değişiklik önce buradaki kontrol listesinden geçer. SPEC bir uygulamanın **ne** yapacağını söyler; bu dosya **nasıl** olması gerektiğini.

> Kaynak: Zeiterfassung'da birlikte kurduğumuz temel prensipler ("sade ve kullanışlı, modern ve minimal") ve miaza finds tasarımı sırasında verilen kararlar. Zeiterfassung'un kodu bu bilgisayarda olmadığı için oradaki yazılı bir ilke dosyasıyla karşılaştırılmadı; varsa bu dosyaya eklenir.

## Yol haritası: dört aşamalı döngü (üst kural)

Asıl yöntem "İyi tasarımın ilkeleri" belgesidir: https://claude.ai/artifact/QaExctb1FhszrLeDNitvt1 (Rams, Jobs, Musk, Norman, Nielsen, Apple HIG). Her tasarım turu bu sırayla yürür ve bir aşamanın bitiş ölçütü sağlanmadan sonrakine geçilmez:

1. **Çıkar** (Musk · Rams): her parçanın bir sahibi ve tek cümlelik bir gerekçesi olsun. "Olmasa ne bozulur?" sorusunun cevabı yoksa parça silinir. Aynı işi yapan iki şeyden biri kalkar.
2. **Sağlamlaştır** (Jobs · Norman · Nielsen): ana işi kullanıcının gözüyle yürü. Nielsen'in on kuralını uygula, sorunlara 0–4 puan ver, önce 3–4'leri düzelt. Aynı şeyin tek adı, tek yeri, tek davranışı olsun. Açıklama metni son çaredir.
3. **Ekle** (Christensen · Kano · Gall · Shape Up): eksik fikirden değil, kanıttan bulunur ("kullanıcı bugün ne yapıyor?"). Özellik değil iş tanımlanır. Önce temel beklentiler gelir. En küçük çalışan hali, mevcut akışın içine eklenir.
4. **Tekrar bak** (Rams · Musk · Apple): tek cümle testi, squint testi ve sayaçlar (yazı boyutu, renk, açıklama metni). Hızlandırma ve otomasyon en sona kalır.

Aşağıdaki ilkeler bu döngünün miaza uygulamalarına uyarlanmış halidir. İkisi çelişirse yol haritası geçerlidir.

---

## Dört temel kelime

| | Anlamı | Pratikte |
|---|---|---|
| **Sade** | Ekranda sadece o an gereken var. | Bir ekran, bir ana iş. Seyrek kullanılan şey göze batmaz. |
| **Kullanışlı** | İş en kısa yoldan biter. | Az dokunuş, akıllı varsayılan değerler, bekletme yok. |
| **Modern** | Bugünün mobil uygulamaları gibi hissettirir. | Kartlar, büyük görseller, yumuşak ve anlamlı geçişler. |
| **Minimal** | Gerçek ihtiyaç yoksa eklenmez. | Ara durum, fazladan menü, süs yok. |

## İlkeler

### 1. Bir ekran, bir ana iş
Her ekranın tek bir amacı vardır ve ana düğmesi bellidir. İkincil işlemler geri planda durur (ikincil düğme, "Daha" menüsü, ayarlar).
*Kontrol:* Bu ekranın ana işi tek cümleyle söylenebiliyor mu?

### 2. Yer, kullanım sıklığına göre verilir
Sık yapılan iş merkezdedir, seyrek yapılan iş ayarlardadır. Bir şeyin önemli olması onu öne koymak için yeterli değildir; **ne kadar sık** kullanıldığı belirler.
- Telefonda QR okutma alt menünün ortasında, çünkü telefonun ana işi.
- Masaüstünde QR okutma üst çubukta küçük bir ikon, çünkü orada seyrek kullanılır (kameralı tablet veya dizüstü).
- Tema seçimi Ayarlar'da; kenar çubuğunda veya ana ekranda değil.
- İstatistik "Daha" altında; açılış ekranında değil.

*Kontrol:* Bu öğe haftada kaç kez kullanılır? Az ise ayarlara veya ikincil bir yere.

### 3. Her cihazda mobil uygulama hissi
Telefon ve masaüstü aynı dili konuşur. Masaüstü ayrı bir "kurumsal" arayüz değildir; sadece fazla alanı akıllıca kullanır (kalıcı filtre sütunu, yandan açılan panel). Tablet masaüstü düzenini kullanır. Telefon birinci sınıf cihazdır: fotoğraf ve QR işleri orada yapılır.
*Kontrol:* Bu ekran telefonda da aynı mantıkla çalışıyor mu?

### 4. Kullanıcıyı bekletme, oyalama
- Açılış ekranı en fazla 700 ms sürer ve bir dokunuşla geçilir.
- Animasyon sürerken de tıklanabilir.
- Veri arkada yüklenir; ekran önce açılır.
- Arama sonuçları anında gelir (< 200 ms).

*Kontrol:* Kullanıcı hiçbir yerde bir şeyin bitmesini beklemek zorunda kalıyor mu?

### 5. Rahatsız etme
Kontrol adımları işi yavaşlatıyorsa atlanabilir olur. "Emin misin?" penceresi yerine **geri al** tercih edilir. Uyarılar olguyu söyler, kullanıcıyı suçlamaz veya sorgulamaz.
- Raf onayı: "Okutmadan onayla" her zaman görünür.
- Hızlı işlemlerin bildiriminde birkaç saniye "Geri al".
- Düzenleme içindeki silme geri alınabilir bir adımdır; ayrıca onay sorulmaz.

*Kontrol:* Bu adım kaldırılsa ne kaybedilir? Kayıp küçükse, adım atlanabilir olmalı.

### 6. Veri girişi zahmetsiz
Veri girmek üşendirdiği an uygulama kullanılmaz olur. En kısa yol her zaman açıktır, ayrıntılar sonra tamamlanır.
- Ürün: fotoğraf (çek veya seç), ad, kaydet.
- Otomatik doldurma: linkten bilgi, fotoğraftan renk, kopyalama, kendiliğinden verilen kod.
- Akıllı varsayılanlar: bugünün tarihi, bu cihazın kişisi, son kullanılan kategori.

*Kontrol:* En kısa kayıt kaç dokunuş? Zorunlu alan gerçekten zorunlu mu?

### 7. Her şey arayüzden yönetilir
Kategori, filtre, oda, ünite, bölme, kişi ve plan kod yazmadan eklenir, düzenlenir, silinir. Geliştiriciye dönmeyi gerektiren hiçbir yapılandırma olmaz. Arayüz metinleri tek bir sözlük dosyasındadır; dil değişimi kod değişikliği gerektirmez.
*Kontrol:* Bunu değiştirmek için birinin kod açması gerekir mi?

### 8. Göster, yazıyla anlatma
Konum plan üzerinde ve fotoğrafta vurgulanarak gösterilir; "Oda › Dolap › Raf" metni ana gösterim değildir. Görseller büyüktür; malzeme kütüphanesi görsel bir şeydir.
*Kontrol:* Bu bilgi bir resimle daha hızlı anlaşılır mı?

### 9. Efekt anlam taşır
Hareket uygulamayı **anlaşılır ve canlı** kılar: nereden nereye gidildiğini, neyin seçildiğini gösterir. Süs için efekt yoktur.
- İstenen: hedefe yumuşak yaklaşma, seçimi vurgulayan spot ışığı, kartların açılması, hafif hover tepkisi.
- İstenmeyen: 3B eğme (warp), fareyi takip eden parallax, kaçan hedefler, dekoratif animasyon.
- Geçişler 150–800 ms. "Hareketi azalt" açıksa kısalır veya kapanır.

*Kontrol:* Bu efekt kaldırılsa kullanıcı bir şeyi daha zor mu anlar? Hayırsa kaldır.

### 10. Veri kaybı sessiz olmaz
- Çok adımlı düzenleme taslakta yapılır: **Geri al · Yinele · Vazgeç · Kaydet.**
- Kaydetmeden önce etkisi söylenir ("3 ürün konumsuz kalacak").
- Kaydedilmemiş değişiklik uyarmadan atılmaz. Yarım kayıt olmaz.
- Aynı kaydı iki kişi habersizce düzenlemez: düzenlenen kayıt diğerlerine "kullanımda" görünür.

*Kontrol:* Kullanıcı bu işlemi yanlışlıkla yaparsa geri dönebilir mi, en azından önceden haberdar olur mu?

### 11. Kalıcı olan, değişenden ayrı tutulur
Basılı etiketler, kalıcı kimlikler ve linkler hiçbir düzenlemeyle geçersiz olmaz. Değişebilen bilgi (konum, numara sırası) her zaman uygulamadan okunur, kâğıda veya QR'a gömülmez.
*Kontrol:* Bu değişiklik basılmış bir şeyi bozar mı?

### 12. Görsel düzen: az ve tutarlı
- Tek vurgu rengi. Durum renkleri sadece durum için.
- Bütün renkler değişkendir (token); açık ve koyu tema baştan birlikte tasarlanır.
- Kart tabanlı ekranlar, yuvarlak köşeler, çizgi ikonlar. Emoji ve gradyan süs yok.
- Dokunma hedefi en az 44 × 44 px; ikincil metin bile zeminde ≥ 4.5:1 kontrast.
- Renk tek başına anlam taşımaz; açıklık farkı veya yazıyla desteklenir.
- Yazı tipi: bütün ailede miaza counts'un sistemi: arayüzde Figtree, sayı ve kodlarda IBM Plex Mono; yazı boyutları yalnız `--fs-*` basamakları. Logoda "miaza" Figtree SemiBold, fiil Figtree Medium ve uygulamanın vurgu rengi.

*Kontrol:* Bu ekranda kaç farklı renk ve yazı boyutu var? Koyu temada da okunuyor mu?

### 13. Gerçek ihtiyaç yoksa ekleme
Yeni fikir ancak gerçek bir ihtiyaca karşılık geliyorsa girer. Ara durumlar ("numune istendi"), sırf bir durum için açılan menüler, kimsenin bakmadığı sayılar eklenmez. Kontrol mekanizmaları büronun ölçeğine göredir (4–5 kişi, giriş yok, rol yok).
*Kontrol:* Bunu kim, ne sıklıkla kullanacak? Cevap belirsizse ekleme.

### 14. Yerel, sade, bağımsız teknoloji
Ofisin mini PC'sinde çalışır; bulut servisine, CDN'e veya dış hesaba bağlı değildir. Bilinen, sıkıcı ama sağlam araçlar kullanılır (FastAPI, SQLite, düz JS, build adımı yok). Her uygulama aynı altyapıyı ve klasör düzenini paylaşır (Windows: kod `C:\miaza\<uygulama>`, veri `%USERPROFILE%\miaza-local\<uygulama>`; D-049).
- **Port düzeni:** her uygulamanın kendi port çifti vardır (beta / geliştirme), hiçbir zaman paylaşılmaz: counts 8080/8081, finds 8090/8091; yeni uygulama bir sonraki onluğu alır (8100/8101, 8110/8111 …).
*Kontrol:* İnternet kesilse veya bir servis kapansa bu özellik çalışmaya devam eder mi?

---

## Hızlı kontrol listesi

Her yeni ekran veya özellik için:

- [ ] Ekranın tek bir ana işi ve tek bir ana düğmesi var. (1)
- [ ] Öğeler kullanım sıklığına göre yerleştirildi; seyrek olan ayarlarda. (2)
- [ ] Telefonda ve masaüstünde aynı mantıkla çalışıyor. (3)
- [ ] Hiçbir yerde bekletme yok; animasyon sırasında tıklanabiliyor. (4)
- [ ] Kontrol adımları atlanabilir; onay penceresi yerine geri al var. (5)
- [ ] En kısa kayıt yolu açık; varsayılan değerler akıllı. (6)
- [ ] Ayar gerektiren her şey arayüzden yönetilebiliyor; metinler sözlükte. (7)
- [ ] Konum ve ilişki görsel gösteriliyor. (8)
- [ ] Her efektin bir anlamı var; "hareketi azalt"a uyuyor. (9)
- [ ] Taslak, geri al, kaydet/vazgeç ve etki özeti var; eşzamanlı düzenleme korunuyor. (10)
- [ ] Basılı etiket ve kalıcı kimlik bozulmuyor. (11)
- [ ] Renkler token; koyu temada kontrol edildi; hedefler ≥ 44 px. (12)
- [ ] Gerçek bir ihtiyaca karşılık geliyor. (13)
- [ ] Dış servise bağımlı değil. (14)

## Karar örnekleri

İlkelerin uygulamada nasıl yorumlandığını gösteren kararlar. Yeni karar verildikçe eklenir.

| Tarih | Karar | İlke |
|---|---|---|
| 31.10.2026 | Fotoğrafa 3B eğme efekti kaldırıldı; kartların açılması ve spot ışığı kaldı. | 9 |
| 31.10.2026 | "Numune istendi" durumu eklenmedi; dijitalden fizikiye tek adımda çevirme yeterli. | 13 |
| 31.10.2026 | Kategori ve filtreler koda değil ayarlara; filtre tipleriyle kullanıcı tanımlı. | 7 |
| 01.11.2026 | Ürün etiketinde konum yok; QR sadece kalıcı envanter numarasını taşır. | 11 |
| 01.11.2026 | Raf QR onayı isteğe bağlı; "Okutmadan onayla" her zaman görünür. | 5 |
| 01.11.2026 | Plan altlığının görünürlüğü ofis menüsünde değil, ayarlarda. | 2 |
| 01.11.2026 | Açılış ekranı ≤ 700 ms, dokunuşla geçilir. | 4 |
| 01.11.2026 | Tema seçimi kenar çubuğundan ve "Daha" ekranının başından Ayarlar'a taşındı. | 2 |
| 01.11.2026 | Masaüstüne QR okutma eklendi ama üst çubukta küçük bir ikon olarak. | 2, 3 |
| 01.11.2026 | Eşzamanlı düzenleme: kilit yönetimi yerine kendiliğinden kalkan "kullanımda" uyarısı. | 10, 13 |
| 01.11.2026 | Tekli ve çoklu seçim filtreleri birleştirilmedi: tekli değerler birbirini dışlar, çoklu değerler bağımsızdır. Anlam farkı varsa tip ayrı kalır. | 2 (Sağlamlaştır: kavramsal model) |
| 01.11.2026 | Ofiste fareyle önizleme kaldı: teknik sorun çıkarmadığı sürece göz gezdirmeye yarıyor. | 1 (Çıkar: geri eklenen) |
| 01.11.2026 | Genel terimler: **Einheit** (2.1) ve **Fach** (2.1.5). Ünitenin türünü isteğe bağlı adı söyler ("Schrank links"); ayrı bir tür listesi yok. "Einheit" fiyat tarafında kullanılmaz (orada "/ m²" ve dışa aktarımda "ME"). | 1, 2 (tek ad) |
