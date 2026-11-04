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
Claude'un ekledikleri (karar: D-045): seçici açılınca ürünün bulunduğu ünite seçili gelir; fotoğrafı olmayan ünitede
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
Claude'un ekledikleri (karar: D-045): yok; fotoğraf üstü renkler (karartma, etiket) iki temada aynıdır, çünkü fotoğrafın
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
Claude'un ekledikleri (karar: D-045): çoklu seçimde kırpma ekranının açılmaması ve yüklenmemiş fotoğraftaki kırpma
düğmesi. Kaydedilmiş bir fotoğrafı sonradan kırpmak şimdilik yok.
→ SPEC 6.2.

## D-028 · 02.11.2026 · Düzenlemede her şey „Speichern“e kadar taslak; seri sonrası listede „Speichern“
Cankat'ın denemesinden:
- **Ürün düzenleme:** fotoğraf silmek ve eklemek artık hemen sunucuya gitmez; diğer alanlar gibi „Speichern“de
  uygulanır, „Abbrechen“ hepsini geri alır. Fotoğraf değiştirmek: eskisinin ×'i, yenisini ekle, kaydet. Yeni fotoğraflar
  sona eklenir; bir ürünün birden çok fotoğrafı olabilir, ilk fotoğraf ana fotoğraftır.
- **Seri kayıttan sonraki liste** (eksik bilgili ürünler): adlar yazılırken liste altında her zaman görünen
  **„Speichern“** çubuğu; değişen bütün adları birlikte kaydeder. Enter ile bir sonraki ada geçmek ve o adı kaydetmek
  kalır. Kaydedilmemiş ad varken sayfadan çıkılınca tarayıcı uyarır. Diğer bilgiler sonra kütüphaneden girilir.
→ SPEC 6.2.

## D-029 · 02.11.2026 · Tasarım denetimi: önem 2 bulguları
„İyi tasarımın ilkeleri“ kontrol listesine göre yapılan denetimden; Claude'un önerileri, Cankat onayladı.
- **Yeni ürün formu kısa:** fotoğraf, tür, ad, kategori ve kategorinin filtreleri görünür; marka, ölçüler, fiyat, adet,
  link, renkler ve not kapalı bir „Weitere Angaben“ altında (dokununca açılır). Düzenlemede ya da doluysa açık. (İlke 6)
- **Dokunma hedefleri:** filtre, renk ve seçenek çipleri en az 44 px. (İlke 12)
- **Tarayıcının onay penceresi yok:** plan, bölme ve kategori düzenleyicide „Verwerfen“ hemen atar, bildirimde
  „Rückgängig“ geri getirir. Ürün formunda „Verwerfen“ değişiklik varsa ilk dokunuşta düğmenin kendisinde
  „Wirklich verwerfen?“ sorar, ikinci dokunuş atar (sayfadan çıkıldığı için geri al mümkün değil). Ürün silme onayı
  kalır: geri alınamaz. (İlke 5)
- **Tek ad:** taslağı atmak her yerde „Verwerfen“ (ürün formundaki „Abbrechen“ da). (Tek ad kuralı)
- **Telefon menüsü:** tek satırlık „Mehr“ sayfası kalkar; üçüncü sekme doğrudan „Einstellungen“. Başka şeyler gelince
  „Mehr“ geri gelir. (Çıkar)
→ SPEC 4.5, 6.2.

## D-030 · 02.11.2026 · Tasarım denetimi: önem 1 bulguları
Claude'un önerileri, Cankat onayladı.
- Büro'nun ilk panelindeki açıklama („Tippe auf eine Einheit …“) kalkar: liste satırları ve oklar ne yapılacağını
  gösteriyor. Yer seçme modundaki yönlendirmeler cihazdan bağımsız yazılır („Einheit wählen …“, „Fach wählen“).
- Plan ve bölme düzenleyici dar ekranda (< 900 px) açılmaz; yerine „Am Desktop zeichnen“ kartı. (SPEC 6.4: çizim
  masaüstünde.)
- Etiket listesindeki durum yazısı çiplerle aynı yazılır („Ungedruckt“, „Gedruckt“, „Neu drucken“).
→ SPEC 6.4.

## D-031 · 02.11.2026 · Ana renkler ve kategoriye özel renk tonları (Farbkasten)
Cankat'ın kararı (2. yöntem). Renk, malzemeyi aramanın temel yollarından biri.
- **Ana renkler** (bütün kategoriler için ortak, sabit, kategoriler arası arama bunlarla): Weiß, Beige, Braun, Rot,
  Orange, Gelb, Grün, Blau, Violett, Rosa, Grau, Schwarz, Metall, **Mehrfarbig**. Üründe birden çok ana renk seçilir;
  kütüphane filtresi çoklu seçimlidir („Rot oder Rosa“). Eski Terracotta → Orange, Gold → Metall (Migration 006).
- **Renk tonları kategoriye özeldir:** kategori ayarlarında yeni filtre tipi **„Farbe“**. Seçenekleri tonlardır: istenen
  ad (Eiche, Weinrot, Burgund …), seçilen renk (renk seçiciyle) ve bağlı olduğu ana renk. Üründe birden çok ton seçilir.
- **Farbkasten:** „Farbe“ filtresi ayarlarda her ana renk için bir kutu olarak görünür; tonlar kutuların içindedir.
  Kutunun „+“sı o ana renkte yeni ton açar; ton bir kutudan diğerine sürüklenince ana rengi değişir (masaüstü).
- **Arama:** ana renk filtresi, ürünün kendi ana renklerini ve seçili tonlarının ana renklerini birlikte arar
  („Rot“ → Weinrot'lu kumaşlar da). Kategori seçiliyken tonlar da ayrı filtre olarak görünür.
- Teknik: „Farbe“ filtresi veritabanında çoklu seçim filtresidir (`filter.farbe = 1`); tonlar `filter_option.hex`
  ve `filter_option.grundfarbe` taşır. Böylece ürün formu, toplu düzenleme ve arama mevcut filtre yolunu kullanır.
Yeni ton filtresinin adı varsayılan olarak „Farbton“ (ana renk filtresi „Farbe“ ile karışmasın; tek ad kuralı).
Claude'un ekledikleri (karar: D-045): ana renk listesi ve Terracotta → Orange, Gold → Metall eşlemesi; ton tutma noktası.
→ SPEC 6.1, 6.2, 6.3.

## D-032 · 02.11.2026 · Yeni renk filtresi ana renklerle dolu başlar
Cankat'ın düzeltmesi: her kutuya tonu elle yazmak gereksiz iş. Yeni bir „Farbe“ filtresi her ana renk kutusunda,
o rengin adını ve rengini taşıyan bir tonla başlar (Weiß altında „Weiß“, Rot altında „Rot“ …). Değiştirilmeyen ton
olduğu gibi kalır; istenen yeniden adlandırılır, rengi değiştirilir, silinir ya da yanına yeni ton eklenir.
Var olan renk filtrelerine dokunulmaz.
→ SPEC 6.3.

## D-033 · 02.11.2026 · Etiket kâğıdı ve ürün etiketi düzeni
Cankat'ın gönderdiği düzen PDF'inden („QR Code Sticker Paper.pdf“, A4).
- **Kâğıt:** 3 sütun × 8 satır = 24 etiket, her biri 69,5 × 36,8 mm; sol kenar 0,8 mm, üst kenar 1,1 mm
  (`app/etikett_bogen.json`; düzeltilmiş çizimden ölçüldü).
- **Ürün etiketi** (ölçüler çizimden): solda 29,6 × 29,6 mm QR (4,9 mm / 5,2 mm içeride); sağda, 38,5 mm'den başlayan
  sütunda yukarıdan aşağı:
  1. **Ürün adı** büyük harf, kalın, en çok iki satır (sığmazsa küçülür, sonra „…“),
  2. **Marka**, 3. **Marka kodu** (yeni alan „Artikelnummer“), 4. **Ölçüler**, 5. **Diğer özellikler**: kategorinin filtre
     değerleri, „ | “ ile ayrılmış (ör. WANDFLISE | R9); küçük, düz yazı, boş olan satır atlanır,
  6. altta **sistem kodu** (FL-001-001), ince ve büyükçe.
  Yazı tipi uygulamanınki (Figtree); çizimdeki Montserrat'a yakın.
- **Yeni alan „Artikelnummer“** (üreticinin ürün kodu): ürün formunda Marka'nın yanında, aramada da bulunur (Migration 007).
- **Bölme etiketi** aynı kâğıtta aynı düzende: solda QR, sağda büyük bölme kodu ve adı.
- Etiketler sayfasındaki önizleme de bu düzeni gösterir.
Claude'un ekledikleri (karar: D-045): basılmış bir etikette görünen bilgi (ad, marka, marka kodu, ölçüler, özellikler)
değişince etiket „yeniden bas“ listesine girer.
→ SPEC 6.6.

## D-034 · 02.11.2026 · Etiket içeriği ortalı; sol kenarda „miaza“
Cankat'ın isteği.
- **Sabit, ortalı, güvenli alanlı düzen** (Cankat'ın düzeltmesiyle): her kenardan 3 mm hayali güvenli alan; düzen bu alanı
  doldurur ve her etikette aynıdır (içeriğe göre kaymaz). Soldan: „miaza“ → 2 mm → QR → 2,5 mm → metin sütunu (sağ güvenli
  alana kadar, ~28 mm; içerik çoğalırsa yer olsun diye QR sola alındı). QR 26 mm kare, dikeyde tam ortada; metin QR'ın
  üst ve alt kenarı arasında (ad üst kenarla, kod alt kenarla hizalı). QR'ın yanında en az 2 mm boşluk: okunabilirlik.
- **Marka işareti:** sol kenarda, yan dönmüş (aşağıdan yukarı okunan) „miaza“, Comfortaa SemiBold; QR yüksekliğinin
  ~%70'i kadar uzun, dikeyde ortalı. Numunenin büroya ait olduğu anlaşılır. Ürün ve bölme etiketinde aynı.
- Yazı tipi dosyası Cankat'ın bilgisayarındaki Comfortaa'dan alındı (SIL Open Font License), `app/assets/fonts`.
→ SPEC 6.6.

## D-035 · 04.11.2026 · Rulo etiket: Brother QL-570, 38 mm rulo
Cankat'ın isteği. Büroda Brother QL-570 var; DK-22225 (38 mm genişlikte sürekli rulo) ile deneme baskısı çalıştı.
- **A4 bogen kalır; ikinci biçim „Rolle 38 mm“.** Etiket 70 × 38 mm; düzen D-034'ün aynısı (her kenarda 3 mm güvenli
  alan, „miaza“ | QR 26 mm | metin sütunu). İki biçim arasındaki fark yalnız ölçü ve sayfaya diziliş.
- **Etiketler sayfasında** önizlemenin üstünde iki seçenek: „A4-Bogen“ / „Rolle 38 mm“. Rulo önizlemesi etiketleri tek
  tek gösterir.
- **Çıktı: tek PDF, her etiket bir sayfa (70 × 38 mm).** Yazıcı sürücüsü sayfaları sırayla basar ve her etiketten sonra
  keser; 50 etiket tek baskı işidir. Ek program gerekmez; PDF herhangi bir bilgisayardan basılır.
- **Neden P-touch Editor'ın veri içe aktarması değil:** orada şablonu yeniden çizmek, QR'ı bir veri alanına bağlamak ve her
  düzen değişikliğinde iki yeri (uygulama ve şablon) güncellemek gerekir. PDF'te düzen ve yazı tipleri tek yerde kalır;
  önizleme baskının aynısıdır.
- **Sonra, kanıt gelirse (v2):** uygulamadan doğrudan yazıcıya basmak (raster komutlarıyla, ör. `brother_ql`). USB ve
  sürücü ayarı ister.
- Rulo tanımı `app/etikett_rolle.json`; A4 tanımı (`app/etikett_bogen.json`) değişmez.
Claude'un ekledikleri (karar: D-045): seçilen biçim tarayıcıda hatırlanır; bölme (Fach) etiketleri de rulodan basılabilir.
→ SPEC 6.6, SPEC 9 (v2), SPEC 11 (soru 1 cevaplandı).

## D-036 · 04.11.2026 · Bölme etiketinde yer bilgisi alt alta
Cankat'ın isteği. Bölme etiketinin sağ sütunu yukarıdan aşağı:
1. **Bölme kodu** (ör. 1.6.4), büyük, eskisi gibi,
2. **Oda** adı (ör. Lager),
3. **Ünite** adı (ör. Plotter Schrank),
4. **Bölme** adı (ör. Obere Reihe Links).
- Adlar girildiği gibi yazılır (büyük harfe çevrilmez); boş olan satır atlanır. Uzun ad önce küçülür, sonra „…“ ile biter.
- D-020'deki „bölmenin adı, yoksa ünitenin adı“ kuralının yerini alır. Etiketler sayfasındaki listede alt satır aynı kalır.
→ SPEC 6.6.

## D-037 · 04.11.2026 · Bölme etiketi: yer bilgisi ağaç gibi, alanı dolduran yazı
Cankat'ın düzeltmesi (D-036'nın üstüne).
- **Ağaç çizgisi, kademeli** (Cankat'ın düzeltmesi): oda en üstte; ünite odanın altında bir kademe içeride, bölme
  ünitenin altında bir kademe daha içeride. Her kademe üstündekine kendi „└“ çizgisiyle bağlanır: iç içe üç katman,
  aynı katmanda iki parça değil.
- **Alanı kullan:** yer bilgisi, kodun altından QR'ın alt kenarına kadar olan yüksekliği doldurur; son satır QR'ın alt
  kenarıyla hizalanır. Yazı boyu bu alana sığan en büyük boydur (en çok 10 pt).
- **„…“ son çare:** uzun ad önce ikinci satıra kayar (kelimeden bölünür), sonra yazı küçülür (en az 6,5 pt); ancak o da
  yetmezse „…“ ile biter. Önce tek satırda sığan bir boy aranır; ikinci satıra kaymak, yazıyı çok küçültmekten iyidir.
→ SPEC 6.6.

## D-038 · 04.11.2026 · Dilim 3'ün kapsamı ve sırası
Claude'un önerisi, Cankat onayladı. Dilim 2 main'e birleştirildi; Dilim 3 `dilim-3/bewegung` dalında. Sıra (her parça
kendi başına çalışır ve denenir):
1. **Kişiler ve „Bu cihaz“:** Ayarlar'da kişi listesi (yalnız ad); her cihazda kullanan kişi seçilir (cihazda saklanır).
2. **Al / Yerine koy** (6.7): „Nehmen“ (kim, Im Büro / Außer Haus, not), durumlar Am Platz · In Benutzung · Außer Haus,
   kütüphanede durum filtresi, çıkış kaydı. Önce düğmeyle, okutmasız.
3. **Okut / Scannen:** telefonda alt menünün ortasında, masaüstünde üst çubukta ikon. Canlı kamera yalnız güvenli
   bağlantıda; yoksa „Fotoğrafla okut“. Kod elle de yazılır. QR'daki adres yok sayılır, yalnız numara okunur (Claude'un
   önerisi: sunucu adresi değişse de basılı etiketler uygulama içinden okunur).
4. **Bölme onayı** (6.7, ayar Açık/Kapalı).
5. **Toplu yerleştirme okutarak:** bölme QR'ı, sonra ürünler art arda.
6. **„Wird bearbeitet“** (4.9).
Kart yayı ve yelpaze (D-017) Dilim 3'ten sonra, gerçek veriyle „Tekrar bak“ adımında.
→ SPEC 10, CLAUDE.md, STATUS.

## D-039 · 04.11.2026 · Al / Yerine koy (Dilim 3, 2. parça)
SPEC 6.7'nin okutmasız ilk hâli. Ayrıntılar Claude'un önerisi:
- **Ürün detayında, başlığın hemen altında** (sayfanın en sık işi; telefonda aşağıda kaybolmasın) fiziki ürünün durumu bir satırda: „Am Platz“ ya da „In Benutzung · Selin · seit 04.11.“ /
  „Außer Haus · Selin · seit 04.11.“ (+ not). Ana düğme duruma göre **„Nehmen“** ya da **„Zurücklegen“**.
- **Nehmen:** düğmenin yerinde küçük bir form açılır: kişi (bu cihazın kişisi seçili gelir), Im Büro / Außer Haus
  (Im Büro seçili), not (isteğe bağlı), „Nehmen“. Hiç kişi tanımlı değilse kişisiz de alınır.
- **Zurücklegen:** tek dokunuş, „Rückgängig“ ile. Bölme onayı (okutma) 4. parçada bunun önüne gelir.
- **Nehmen** de „Rückgängig“ ile geri alınır (kayıt silinir); yanlış dokunuşta iz kalmaz.
- **Durum** çıkış kaydından türetilir, üründe ayrı alan yok: açık kayıt → In Benutzung / Außer Haus; yoksa bölmesi
  varsa Am Platz. „Ohne Platz“ yine bölmesi olmayan fiziki üründür (alınmış olsa da).
- **Kütüphane kartında rozet** yalnız In Benutzung ve Außer Haus için (durum renkleriyle). „Ohne Platz“ rozet almaz:
  yeni kayıtların çoğu önce konumsuz, rozet gürültü olurdu; onun yeri filtre ve durum satırı.
- **Çıkış kaydı** (Migration 009): ürün, kişi, Im Büro / Außer Haus, not, alınma ve iade zamanı, bölme onayı (4. parça
  için boş). Bir ürünün aynı anda tek açık kaydı olur. Geçmişin gösterimi istatistikle (dilim 4).
Claude'un ekledikleri (karar: D-045): Nehmen'in geri alınabilmesi; rozetin yalnız iki durumda olması.
→ SPEC 6.1, 6.7, 7.

## D-040 · 04.11.2026 · Scannen (Dilim 3, 3. parça)
Cankat onayladı: QR çözücü olarak jsQR 1.4.0 (Apache-2.0) uygulamayla gelir (`app/static/vendor/`, npm'den, bütünlüğü
doğrulandı); tarayıcıda BarcodeDetector varsa o kullanılır. Ayrıntılar Claude'un önerisi:
- **Kendi sayfası `/scannen`.** Telefonda alt menüde vurgulu „Scannen“ (Koleksiyonlar gelince ortada kalır);
  masaüstünde her sayfanın başlık satırında küçük QR ikonu, yalnız kamera varsa.
- **Canlı kamera** güvenli bağlantıda (HTTPS, masaüstünde localhost): görüntü sürekli taranır, kod bulununca hemen gidilir.
  Değilse büyük „Foto aufnehmen“ düğmesi: telefonun kamera uygulaması açılır, QR fotoğraftan okunur.
- **Okunan içerik:** adresin yalnız sonu sayılır (`…/p/<nr>` ürün, `…/f/<id>` bölme); sunucu adresi önemsiz (D-038).
  Ürün → ürün sayfası (Nehmen / Zurücklegen orada). Bölme → Büro'da o bölme. miaza'ya ait olmayan QR → kısa uyarı.
- **Kod yazmak** her zaman mümkün: „265“, „FL-021-024“ (ürün) ya da „1.6.4“ (bölme). Tanınmayan yazı kütüphane aramasına gider.
Claude'un ekledikleri (karar: D-045): kod kutusunun bölme kodunu da tanıması; tanınmayanın aramaya gitmesi.
→ SPEC 4.5, 8.1.

## D-041 · 04.11.2026 · Scannen ohne HTTPS: Kamera direkt aus dem Menü, sichtbare Rückmeldung
Cankat'ın geri bildirimi: „Scannen“ → „Foto aufnehmen“ → kamera seçimi gereksiz adım; fotoğraftan sonra ne olduğu
görünmüyor. Neden: HTTPS olmadan tarayıcı sayfa içinde canlı kamera açmaz (SPEC 8.2). Çözüm Claude'un önerisi:
- **Canlı kamera mümkün değilse** (telefon, düz `http://`) alt menüdeki „Scannen“ doğrudan telefonun kamerasını açar;
  ara sayfa ve „Foto aufnehmen“ düğmesi yok.
- **Fotoğraftan hemen sonra tam ekran geri bildirim:** „Wird gelesen …“, sonra bulunan ürünün ya da bölmenin adı
  (kısa titreşim) ve sayfaya geçiş. Bulunamazsa „Kein QR-Code erkannt“ ile **„Noch einmal“** (kamerayı yeniden açar) ve
  „Code eingeben“ (`/scannen`).
- **Canlı kamera mümkünse** (HTTPS, masaüstünde localhost) değişiklik yok: `/scannen` açılır, kod görüntüye girince tanınır.
- Telefonun kendi kamerası tek ürün için zaten iyi çalışır (etiketteki QR bir link). Art arda okutma (bölme onayı,
  toplu yerleştirme) asıl HTTPS ile rahatlar; mkcert ile deneme sonra (Cankat).
→ SPEC 4.5, 8.2.

## D-042 · 04.11.2026 · Fach bestätigen (Dilim 3, 4. parça)
SPEC 6.7'nin bölme onayı. Ayrıntılar Claude'un önerisi:
- **„Zurücklegen“** (ürünün bölmesi varsa ve ayar açıksa) düğmenin yerinde küçük bir alan açar: „Fach-Etikett scannen ·
  2.2.5“. Canlı kamera varsa görüntü orada açılır ve etiket görünce kendiliğinden tanır; yoksa „Fach scannen“ telefonun
  kamerasını açar (D-041'deki geri bildirimle). Altta her zaman **„Ohne Scan bestätigen“** ve „Abbrechen“.
- **Doğru bölme:** kısa titreşim, „Zurückgelegt · 2.2.5“ (yeşil onay), kayıtta onaylı.
- **Başka bölme:** „Der Platz ist 2.2.5. Gescannt: 2.3.1.“ → **„Ich bringe es nach 2.2.5“** (kayıtta onaysız) ya da
  **„Neuer Platz: 2.3.1“** (ürünün yeri değişir, onaylı). Ürün etiketi okutulursa: „Das ist kein Fach-Etikett.“
- **Okutmadan onayla:** durum Am Platz olur; kayıtta onaysız. Kimse sorgulanmaz.
- **Bölmesi olmayan ürün** ya da **ayar kapalı:** „Zurücklegen“ eskisi gibi tek dokunuş.
- Hepsi „Rückgängig“ ile geri alınır; yeni yer seçildiyse eski yer de geri gelir.
- **Ayar** (büro geneli, sunucuda; Migration 010): Einstellungen › Allgemein › „Fach beim Zurücklegen bestätigen“
  Ein (varsayılan) / Aus.
→ SPEC 6.7, 6.11.

## D-043 · 04.11.2026 · Toplu yerleştirme okutarak (Dilim 3, 5. parça)
SPEC 6.7/4. Ayrıntılar Claude'un önerisi:
- **Büro'da bölmenin „Hier einordnen“** artık yerleştirme ekranını açar (`/scannen?fach=<id>`): başlıkta „In 1.6.4
  einordnen“, altında bu sırada yerleştirilenlerin listesi ve „Fertig“. D-016'daki 30 dakikalık mod da aynı anda açılır;
  telefonun kendi kamerasıyla açılan ürün sayfalarında „In 1.6.4 einordnen“ düğmesi yine çıkar.
- **Canlı kamera varsa** görüntü açık kalır; ürünler art arda okutulur, her biri hemen yerleşir (titreşim, listede ✓).
  Yoksa „Produkt scannen“ her seferinde telefonun kamerasını açar (D-041'deki geri bildirimle); kod da yazılabilir.
- **Ürün başka bir bölmede:** „Verano Tarçın liegt in 1.1.3.“ → „Hierher verlegen“ / „Überspringen“. Konumsuz ürün
  sorulmadan yerleşir; zaten bu bölmedeki „schon hier“ diye listelenir.
- **Başka bir bölme etiketi okutulursa** hedef o bölme olur (raf raf yerleştirirken akış kesilmez).
- Her satırın kendi „Rückgängig“'i vardır.
- **Alınmış ürün** (In Benutzung / Außer Haus) yerleştirilince aynı anda geri konmuş sayılır (onaylı): fiziken
  bölmede olduğu okutulmuştur. Ürün sayfasındaki „In … einordnen“ düğmesi de aynı kuralla çalışır.
Claude'un ekledikleri (karar: D-045): başka bölme etiketiyle hedef değiştirme; alınmış ürünün yerleştirilince geri
konmuş sayılması.
→ SPEC 6.7.

## D-044 · 04.11.2026 · „Wird bearbeitet“ (Dilim 3, 6. parça)
SPEC 4.9'un ilk hâli. Ayrıntılar Claude'un önerisi:
- **Kapsam:** ürün formu, kategori ve filtre ayarları, büro planı ve ünite fotoğrafı (plan ve fotoğraf düzenleyicisi
  aynı işareti paylaşır: ikisi de aynı plan sürümüne kaydeder). Koleksiyonlar gelince onlar da.
- **İşaret sunucunun belleğindedir, kalıcı değildir** (SPEC 7): kayıt, cihaz, kişi, başlangıç, son sinyal, son değişiklik.
  Cihaz tarayıcıda rastgele bir kimlikle tanınır; „kim“ bu cihazın kişisi, yoksa „Ein anderes Gerät“.
- **Düzenleyen cihaz** 30 sn'de bir sinyal yollar; sayfadan çıkınca işaret kalkar. 2 dk sinyal yoksa ya da 15 dk hiç
  değişiklik yapılmadıysa işaret kendiliğinden düşer. Elle kaldırılacak kilit yoktur.
- **Başkası açarsa** üstte ince bir şerit: „Wird bearbeitet · Selin bearbeitet das gerade (4 Min.)“; düzenleme alanı salt
  okunur (görünür, dokunulmaz). Şerit 10 sn'de bir sorar; işaret kalkınca „Jetzt kannst du bearbeiten.“ ve „Neu laden“
  (diğerinin kaydettiği hâli görmek için yeniden yükleme gerekir).
- Yedek güvenlik değişmez: yine de çakışma olursa sürüm kontrolü ikinci kaydı reddeder.
→ SPEC 4.9.

## D-045 · 04.11.2026 · Bekleyen önerilere Cankat'ın kararları
**Onaylandı:** D-021 (seçici ürünün ünitesiyle açılır), D-031 (14 ana renk; Terracotta → Orange, Gold → Metall),
D-033 (içerik değişince „Neu drucken“), D-035 (biçim hatırlanır; Fach etiketi de rulodan), D-039 (Nehmen geri alınır;
„Ohne Platz“ rozet almaz, görüntü kirliliği olur), D-040 (kod kutusu bölme kodunu tanır), D-043 (alınmış ürün
yerleşince geri konmuş sayılır).
**Değişenler:**
- **„Im Büro zeigen“ telefonda rafı önce gösterir.** Ürün sayfasından gelince (yeri bulmak için) ilk görünen ünitenin
  fotoğrafı ve vurgulu bölmedir; plan altta kalır. Adım adım gezerken düzen aynı (orada kaydırmak sorun değil).
- **Çoklu seçimde de her fotoğraf kırpılır** (D-027'nin yerine): kırpma ekranı fotoğrafları sırayla açar, başlıkta
  „2 / 5“. Kaydedilmiş fotoğrafı sonradan kırpmak gerekmez; gerekirse fotoğraf silinip yeniden eklenir.
- **Etiketlerde varsayılan „Rolle 38 mm“:** büro çoğunlukla ruloyla basar; seçim yine hatırlanır.
- **Scannen'de tanınmayan kod** (D-040'ın yerine): doğrudan aramaya gitmez; önce „… nicht erkannt“ der, sonra
  „In der Bibliothek suchen“ diye sorar.
- **Yerleştirirken başka bölme etiketi** (D-043'ün yerine): hedef hemen değişmez; „Jetzt in 1.6.6 einordnen?“ sorulur,
  onaylanınca sonraki ürünler oraya yerleşir.
Sonradan cevaplananlar (Cankat): ürün adları her zaman üreticinin kendi sitesindeki **orijinal adlarıyla** girilir, çevrilmez
(Verano Türkçe sayfadan geldiği için Türkçe; İtalyan ürünü İtalyanca). Ton ana renge bağlanır (Antrasit → Schwarz) — doğru.
Fach etiketinde adlar girildiği gibi (büyük harfe çevrilmez). Ürün kodu etikette boşluksuz: „FL-001-001“.
→ SPEC 6.1, 6.2, 6.6, 6.7, 4.5.
