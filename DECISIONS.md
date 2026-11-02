# DECISIONS — miaza finds

Kararların tarihçesi. Güncel hali SPEC.md ve DESIGN-PRINCIPLES.md'dedir. Yeni karar sona eklenir; numara değişmez.
SPEC 0.4'e kadar olan kararlar SPEC'in sürüm geçmişinde ve DESIGN-PRINCIPLES › Karar örnekleri'nde.

## D-001 · 01.11.2026 · Aile port düzeni
Her uygulama kendi port çiftini kullanır, paylaşmaz: counts 8080 (beta) / 8081 (geliştirme), finds 8090 / 8091.
Yeni uygulama sonraki onluğu alır (8100/8101, 8110/8111 …). Gerekçe: ileride aynı mini PC'de çakışma olmasın (Cankat).
→ SPEC 8.1, DESIGN-PRINCIPLES 14.

## D-002 · 01.11.2026 · Yazı sistemi counts'tan
Cankat: "counts'ta ne kullandıysan o sistemi kullan." Arayüz Figtree (400/500/600), sayı ve kodlar IBM Plex Mono
(400/500), yazı ölçeği counts'un `--fs-*` basamakları (11 · 12,5 · 13,5 · 15 · 19 · 28 · 52). Logo da Figtree
("miaza" SemiBold, fiil Medium + vurgu rengi); SPEC 0.4'teki Inter ve Comfortaa kalktı. Renk değerleri finds'in kendi
paleti (SPEC 4.4) kalır, token adları counts ile aynıdır. → SPEC 4.1, 4.4, DESIGN-PRINCIPLES 12.

## D-003 · 01.11.2026 · Docker ve start.bat birlikte
Mini PC'nin işletim sistemi ve kurulum yolu henüz belli değil. Risk almamak için iki yol da hazır tutulur:
`Dockerfile` + `docker-compose.yml` ve Windows için `start.bat` + `.venv`. Kurulumdan sonra kullanılmayan kaldırılır.
→ SPEC 8.1.

## D-004 · 01.11.2026 · Dokümanlar dilim 4'te
SPEC 6.9 v1'de kalır ama dilim 1'e girmez; dilim 4 (Kalanlar). → CLAUDE.md › Dilimler.

## D-005 · 01.11.2026 · Belge düzeni counts gibi
CLAUDE.md (çalışma kuralları), STATUS.md (anlık durum), DECISIONS.md (bu dosya), SPEC.md (ürün, tek dosya),
DESIGN-PRINCIPLES.md (aile ilkeleri). → CLAUDE.md.

## D-006 · 01.11.2026 · Systembereich: şifreli yönetim alanı
Cankat: Ayarlar'ın en altında küçük bir "backend control" alanı; bir yönetici ve şifre. Yedekleme, toplu veri silme,
veri kümesini değiştirme ve diğer güvenlik işleri burada. SPEC 12'deki "şifre yok" kuralının tek istisnası; uygulamanın
geri kalanı girişsiz. Dilim 1'e girer (büro veri girmeye başlarken yedek ve geri yükleme gerekli).
Açık: şifre unutulunca yol, içe aktarma biçimi (STATUS › Offene Fragen). → SPEC 5, 6.11, 6.13, 12.

## D-007 · 01.11.2026 · İstek koruması
Giriş olmadığı için başka bir web sayfası, aynı tarayıcıdan finds'e gizlice istek gönderebilir (CSRF). Önlem: veri
değiştiren her istekte `Origin` başlığı uygulamanın kendi adresi olmalı. Systembereich'te ek olarak counts'taki gibi
oturum + CSRF anahtarı. Teknik karar (Claude), Cankat'ın seçmesi gereken bir şey yok. → SPEC 8.1.

## D-008 · 01.11.2026 · Yerel çalışma klasörü
`.venv`, veritabanları ve `media/` Drive dışında: `%USERPROFILE%\miaza-local\finds\`. `%LOCALAPPDATA%` Claude
masaüstü uygulamasında sanal bir klasöre yönlendiriliyor; oraya kurulan ortamı `start.bat` göremez. → CLAUDE.md.

## D-009 · 01.11.2026 · Veri taşıma (yeni sunucuya)
Cankat: sunucu değişirse dosyalar kopyalanıp sistem yeniden kurulur; eski veri yeni kuruluma alınabilmeli.
Systembereich'te "Dışa aktar" (tek dosya: veritabanı + fotoğraflar) ve "Verileri al" (bu dosya ya da kopyalanmış
`data/` + `media/` klasörü). Eski sürümün verisi yükseltilir, yeni sürümün verisi reddedilir. Öneri (Claude): yeni
kurulumun yönetici şifresi ve güvenlik anahtarı kalır, eskisi alınmaz. → SPEC 6.13.

## D-010 · 01.11.2026 · Güvenlik anahtarı ile şifre sıfırlama
Cankat: bir güvenlik anahtarı olacak, güvenli yerde saklanacak, şifre onunla sıfırlanacak. İlk kurulumda bir kez
gösterilir (yazdır / indir). Bir kez kullanılınca yenisi verilir (counts'taki Recovery Key gibi). Sunucuda yalnız
özeti saklanır. → SPEC 6.13.

## D-011 · 01.11.2026 · İçinde ürün olan kategori silinmez
Cankat: ürün içeren kategori silinemesin, sadece düzenlensin. SPEC 0.4'teki "silinen kategorinin ürünleri Diğer'e
taşınır" kalktı. Boş kategori silinebilir; dolu kategoride silme yerine ürün sayısı görünür. Veritabanı da bunu
zorlar (yabancı anahtar, migration 001). → SPEC 6.3.

## D-012 · 01.11.2026 · Toplu düzenleme
Cankat: ürünleri topluca seçip kategorisini veya diğer özelliklerini değiştirebilmek (kanıt: kategoriler zamanla
ayrışınca onlarca ürünü tek tek değiştirmek gerekir). Claude'un önerisi, Cankat onayladı: masaüstünde liste
görünümünde seçim; alanlar kategori, marka, tür, renk ekle/kaldır, aynı kategorideyse filtre değerleri; kod sorusu bir
kez; etkisi panelde, onay penceresi yerine "Rückgängig". Dilim 1'de kütüphaneden (adım 7) hemen sonra. → SPEC 6.2.

## D-013 · 02.11.2026 · „Alles löschen“ numaraları 1'den başlatır
Claude'un önerisi, Cankat onayladı. Deneme verisi temizlendikten sonra gerçek ürünler temiz numaralarla başlasın.
"Numaralar asla yeniden kullanılmaz" kuralının tek istisnası; bedeli, önceden basılmış etiketlerin geçersiz olması.
Arayüz bunu silmeden önce yazar ve otomatik yedek alır. "Alle Produkte löschen" sayaçlara dokunmaz. → SPEC 6.2, 6.13.

## D-014 · 02.11.2026 · Beta geri bildirimi 1: masaüstü kamerası, Option ekleme, QR adresi
Cankat'ın ilk denemesinden. Çözümler Claude'un önerisi:
- **Foto aufnehmen (masaüstü):** masaüstü tarayıcısı `capture`'ı yok sayar, iki düğme aynı dosya penceresini açıyordu.
  Masaüstünde güvenli bağlantıda (localhost veya HTTPS) düğme canlı kamera penceresi açar; kamera yoksa ya da bağlantı
  güvenli değilse düğme gizlenir, yalnız "Bild wählen" kalır. Birden çok kamera varsa (laptop, USB, sanal) pencerede seçilir;
  seçim bu cihazda hatırlanır (Cankat). Telefonda değişiklik yok (kamera uygulaması açılır).
- **Option ekleme:** giriş kutusunun içinde, sağda "+" düğmesi (Cankat); Enter da çalışır. Kaydederken kutuda kalan yazı da Option
  olur, kaybolmaz. Virgülle ayırma yok: Almanca ondalık virgülüyle (ör. „0,5“) karışır.
- **QR adresi:** `MF_BASIS_URL` yoksa ve sayfa localhost'tan açıldıysa, `start.bat netz` ile çalışırken QR bu
  bilgisayarın ofis ağı adresini (ör. `http://192.168.1.20:8090`) alır. Etiket sayfasının önizlemesi gerçek QR'ı
  gösterir. Kalıcı adres yine açık soru (STATUS). → SPEC 8.2.

## D-015 · 02.11.2026 · Görsel boyutları ekrana göre
Claude'un önerisi, Cankat onayladı. Detaydaki büyük görsel 2400 px'lik jpg yerine 960'lık webp'yi gösterir; görsele
dokununca tam boy jpg tam ekran açılır (kapatmak: dokun veya Esc). Kütüphane kartları ekranın piksel yoğunluğuna göre
320 veya 960'lık önizlemeyi seçer (`srcset`). Dosyalar kırpılmaz; kare görünüm yalnız ekranda (`object-fit: cover`).
→ SPEC 8.1.

## D-016 · 02.11.2026 · „Hier einordnen“: uygulama içi tarayıcı olmadan toplu yerleştirme
Claude'un önerisi, Cankat onayladı. Bölme QR'ı telefonun kamera uygulamasıyla okutulur, bölme sayfası açılır;
„Hier einordnen“ bu cihazı 30 dakika „2.2.5'e yerleştiriyorum“ moduna alır (tarayıcıda saklanır). Bu sürede okutulan
her ürün sayfasında büyük „In 2.2.5 einordnen“ düğmesi çıkar: tek dokunuş. Mod çubuktaki ×'le veya süre dolunca biter.
Masaüstünde toplu düzenlemeye „Platz“ alanı eklenir. Uygulama içi tarayıcı Dilim 3'te gelir. → SPEC 6.7.

## D-017 · 02.11.2026 · Dilim 2'nin kapsamı
Claude'un önerisi, Cankat onayladı. Dilim 2: veri yapısı, altlık, plan düzenleyici (oda, ünite), ünite fotoğrafı ve
bölmeler, büro görünümü, „Im Büro zeigen“, bölme etiketleri, „Hier einordnen“, „Ohne Platz“ filtresi. Dilim 3'e kalan:
„Düzenleniyor“, alma / yerine koyma, uygulama içi tarayıcı. Kart yayı ve yelpaze animasyonları önce sade hâlde (bölmenin
ürünleri liste olarak); gerçek veriyle „Tekrar bak“ adımında eklenir. Çakışmaya karşı şimdilik sürüm kontrolü yeter.
Menüdeki adı „Büro“ (SPEC 4.10'a eklendi). → SPEC 4.7, 4.10, 10.

## D-018 · 02.11.2026 · Plan yazıları ve oda renkleri
Cankat'ın geri bildirimi (oda adı çok küçük ve odanın dışında, ünite kodu okunmuyor, odalar renkli olsun). Çözüm Claude'un önerisi:
- **Yer:** oda ve ünite yazısı şeklin ağırlık merkezine değil, **içindeki en geniş noktaya** gelir (L biçimli odada da içeride kalır).
  Elle taşıma yok; gerekirse sonra.
- **Boyut:** yazı şeklin içine sığacak kadar büyür, ekranda okunur sınırlar içinde kalır (oda 13–30 px, ünite kodu 13–22 px).
  Bütün üniteler aynı boyda yazılır; yalnız buna sığmayan küçük ünite daha küçük yazı alır. En küçük boyda da sığmayan
  yazı çizilmez (ör. telefonda bütün plan), yakınlaşınca görünür. Ünitenin adı, sığarsa kodun altında küçük yazılır.
- **Renk:** odalar 5 pastel tondan birini alır; renk oda numarasından gelir (1 → 1. ton, 6 → yine 1. ton). Seçim adımı yok.
  Üniteler odalardan ayrışan tek bir renkte; seçili ünite vurgu rengindedir. Açık ve koyu temada ayrı tonlar.
→ SPEC 6.4.

## D-019 · 02.11.2026 · Dikdörtgen ünite duvara ve komşusuna yapışır
Cankat'ın isteği. Plan düzenleyicide dikdörtgen bir ünite sürüklenirken:
- **Duvara yapışma:** odanın bir kenarına yeterince yaklaşınca (ekranda ~10 px) ona yapışır ve o kenara paralel olacak
  şekilde döner: uzun kenarı duvara gelir (dolap sırtıyla), iki yönden hangisi eski duruşa yakınsa o; elle döndürme yok. Yapışıkken kenar boyunca kayar, köşede durur (kenarın ucunu geçmez).
  Kenardan ~24 px uzaklaşınca ayrılır ve son açısını korur. Duvarın odanın iç tarafına yapışır.
- **Komşuya yapışma:** başka bir ünitenin kenarına da aynı şekilde, dış tarafından yapışır.
- **Çarpışma:** dikdörtgen ünite başka bir ünitenin içine giremez; çarpınca onun kenarında durur, komşuyu itmez.
  Komşunun yanından kayarak geçince ilerlemeye devam eder.
Claude'un ekledikleri (Cankat onayladı): yalnız dikdörtgen üniteler için (poligon üniteler ve odalar serbest); Alt tuşu
basılıyken yapışma ve çarpışma kapalı; zaten üst üste duran üniteler birbirini engellemez.
→ SPEC 6.4.

## D-020 · 02.11.2026 · Bölmenin isteğe bağlı adı
Cankat'ın isteği. Bölmenin otomatik kodunun (2.2.5) yanına, ünitedeki gibi isteğe bağlı bir **Name** gelir
(„Obere Schublade“, „Linke Tür“). Bölme düzenleyicide yazılır; Büro'daki bölme listesinde, bölme panelinde, ürün
detayındaki yerde ve toplu düzenlemenin „Platz“ listesinde kodun yanında görünür. Kod değişmez, ad yalnız bilgi verir.
Claude'un ekledikleri (Cankat onayladı): bölme etiketinde kodun altında ünite adı yerine bölmenin adı yazılır (ad yoksa
ünite adı); basılmış bir etiketin adı değişirse etiket „yeniden bas“ listesine girer.
→ SPEC 6.4, 6.6.

## D-021 · 02.11.2026 · Ürün detayında „Platz ändern“
**D-022 ile değişti:** seçici pencere kaldırıldı, yer Büro sayfasında seçilir.
Cankat'ın isteği. Fiziki ürünün detayında „Im Büro zeigen“in yanında **„Platz ändern“** düğmesi (yeri yoksa
**„Platz wählen“**). Açılan seçici demodaki konum seçicisini izler: üstte ünite çipleri, altında seçili ünitenin
fotoğrafı; bölmeye fotoğrafta ya da altındaki listede dokunulur, seçilen kod büyük yazılır. „Übernehmen“ kaydeder;
onay penceresi yok, bildirimde „Rückgängig“ var. Yeri olan üründe „Ohne Platz“ da seçilebilir.
Claude'un ekledikleri (onay bekliyor): seçici açılınca ürünün bulunduğu ünite seçili gelir; fotoğrafı olmayan ünitede
yalnız liste görünür.
→ SPEC 6.1.

## D-022 · 02.11.2026 · Yer, Büro'da seçilir (D-021'in seçici penceresinin yerine)
Cankat'ın düzeltmesi: gerçekte odaya gidilir, ünite görülür, rafa konur; uygulama da öyle yönlendirmeli. Ürün detayındaki
„Platz ändern“ / „Platz wählen“ Büro sayfasını **yer seçme modunda** açar. Üstte bir çubuk: „Platz für „Ürün“ wählen“.
Plan → ünite → bölme; bölme panelinde büyük **„Hier ablegen“**. Kaydedince ürün sayfasına dönülür, bildirimde
„Rückgängig“ vardır. Çubuktaki × vazgeçer.
Claude'un ekledikleri (Cankat onayladı): ürünün yeri varsa Büro o bölmede açılır (nerede olduğu görülür, oradan başka
üniteye geçilir); çubukta „Ohne Platz“ da var.
→ SPEC 6.1.

## D-023 · 02.11.2026 · Tema: beyaz ve antrasit, amber vurgu
Cankat'ın kararı, değerler Claude'un önerisi. Mavi vurgu ve mavimsi koyu tema bırakıldı.
- **Açık tema:** zemin beyaz (`#FFFFFF`), kartlar beyaz ve ince kenarlı, metin `#1C1C1E` / `#66656A`.
- **Koyu tema:** nötr antrasit, mavi alt ton yok: zemin `#18191B`, kart `#212224`, metin `#EDEDEC` / `#A1A1A0`.
- **Vurgu: amber.** Düğme zemini açıkta `#F2A43A`, koyuda `#F5AE3D`; düğme yazısı koyu kahve `#2A1A05`.
  Beyaz üstünde okunacak vurgu yazısı (bağlantı, seçili satır) koyu amber `#9A5600`, koyuda `#FFC870`. Açık zemin
  tonu `#FDF0DA` / `#3A2E1B`.
- **Renk üstüne renk yok:** bir zemin hangi renk ailesindense üstündeki yazı ve ikon aynı ailenin koyu (açıkta) ya da
  açık (koyuda) tonudur. Amber düğmede mor yazı olmaz.
- **Durum renkleri:** Yerinde yeşil, Kullanımda mavi, Dijital mor kalır. „Büro dışında“ ambere çok yakındı: gül rengine
  geçer (`#FBE5EE` / `#9D2F5E`, koyuda `#45263A` / `#F2A7C3`).
- Tema `THEMA.md`'de anlatılır; miaza counts ileride aynı yoldan kendi temasını kurabilir. counts şimdilik değişmez.
→ SPEC 4.4.

## D-024 · 02.11.2026 · Oda rengi seçilir, üniteler odanın tonunda (D-018'in renk kısmının yerine)
Cankat'ın kararı. Altı pastel: **Salbei, Himmel, Lavendel, Pfirsich, Vanille, Rosé**; iki temada ayrı tonlar.
- Plan düzenleyicide oda panelinde altı renk düğmesi; yeni oda sıradaki rengi alır, sonra değiştirilir (Migration 005).
- **Üniteler odalarının renginde, bir ton koyusu** (koyu temada bir ton açığı); ünite yazısı aynı ailenin koyu tonu.
  Hiçbir odada olmayan ünite nötr gri. Tek renk ünite yok.
- **Seçili ünite:** kenar çizgisi kalınlaşır ve aynı ailenin en koyu tonuna döner; başka renk eklenmez.
- **Altlık açıkken** odalar %50 saydam.
→ SPEC 4.4, 6.4.

## D-025 · 02.11.2026 · Seçerek silme (D-013'ün iki düğmesinin yerine)
Cankat'ın isteği, maddeler Claude'un önerisi. Systembereich'te „Löschen“ onay kutularıyla:
**Produkte** (fotoğraflarla) · **Kategorien und Filter** (seçilince Produkte de seçilir) · **Büroplan** (odalar, üniteler,
bölmeler, ünite fotoğrafları, altlık; ürünler „Ohne Platz“ olur) · **Nummern zurücksetzen** (envanter ve bölme numaraları
1'den; yalnız Produkte ve Büroplan da seçiliyse). Üstte „Alles auswählen“. Her kutunun yanında etkisi yazar; önce
kendiliğinden yedek alınır. „Alles löschen (Neuanfang)“ ayrı düğmesi kalkar. Dışa aktarma her zaman tümüdür.
→ SPEC 6.13.

## D-026 · 02.11.2026 · Ünite fotoğrafındaki bölmeler demodaki gibi
Cankat'ın isteği: Büro'daki ünite fotoğrafı demodaki davranışı alır.
- Bölme alanları dolgusuz ve kenarsız; fareyle üzerine gelince hafif aydınlanır.
- Her bölmenin sol üst köşesinde küçük koyu etiket: **kod · ürün sayısı** (boş bölmede yalnız kod, daha soluk).
- **Spot ışığı** yuvarlak köşeli bir çerçevedir; bölmeden bölmeye kayarak geçer (0,45 sn). Seçili bölmede zemin koyu
  karartılır, kenar vurgu renginde ve nabız gibi atar; fareyle üzerine gelinen bölmede hafif karartma ve beyaz kenar
  (önizleme). Spot dışındaki etiketler solar.
- Hareket azaltma tercihi varsa kayma ve nabız olmaz.
- Spot, bölmenin dış çerçevesini (sınır kutusu) izler; bölmeler çoğunlukla dikdörtgen çizilir.
Claude'un ekledikleri (onay bekliyor): yok; fotoğraf üstü renkler (karartma, etiket) iki temada aynıdır, çünkü fotoğrafın
üstündedir.
→ SPEC 4.7.

## D-027 · 02.11.2026 · Fotoğrafı eklerken kırpma
Cankat'ın isteği (üşendiren ara adım olmasın: ayrıca kırpıp yeniden eklemek gerekmesin). Çözüm Claude'un önerisi:
- **Tek fotoğraf** eklenince (kamerayla çekilen ya da seçilen tek dosya) hemen kırpma ekranı açılır. Bu ekranın kendisi
  „kırpayım mı?“ sorusudur; ayrı bir soru penceresi yok. Tek kayıtta da seri kayıtta da aynı.
- Ekran: fotoğraf ve üstünde çerçeve. Köşeler ve kenarlar sürüklenir, çerçevenin içi sürüklenince çerçeve kayar;
  dışı kararır. Düğmeler: **„Übernehmen“** (birincil) ve **„Ganzes Bild“**; × fotoğrafı eklemekten vazgeçer.
  Çerçeve başta bütün fotoğraftır; hiç dokunmadan „Übernehmen“ fotoğrafı olduğu gibi alır.
- Kırpma telefonda yapılır, fotoğraf kırpılmış hâliyle yüklenir (uzun kenar en çok 3000 px). Sunucu değişmez.
- **Birden çok dosya** birlikte seçilince ekran açılmaz (çok sayıda dosyada üşendirir); yeni üründe henüz yüklenmemiş
  her fotoğrafın üstünde bir kırpma düğmesi vardır.
- Oran serbesttir; döndürme yok.
Claude'un ekledikleri (onay bekliyor): çoklu seçimde kırpma ekranının açılmaması ve yüklenmemiş fotoğraftaki kırpma
düğmesi. Kaydedilmiş bir fotoğrafı sonradan kırpmak şimdilik yok.
→ SPEC 6.2.
