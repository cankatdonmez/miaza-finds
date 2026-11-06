# CALISMA-TARZI — Cankat nasıl çalışmak istiyor (devir paketi, 06.11.2026)

Bu proje boyunca gözlediğim çalışma biçimi. CLAUDE.md'deki kuralların yanında, orada yazmayan alışkanlıklar da var.

## Konuşma ve dil
- Cankat'la **Türkçe** konuşulur; uygulamanın arayüzü **Almanca**; kod yorumları ve commit başlıkları **Almanca**; DECISIONS ve SPEC **Türkçe** (D-046/047 istisna, başka oturumdan).
- Cankat kısa ve doğal yazar, çoğu zaman Türkçe karakter kullanmadan („yazilara“, „ortala“). Sesli giriş de kullanıyor gibi; anlamı bağlamdan çıkarmak gerekir. Belirsizse kısaca sor.
- Cevaplar kısa, somut, maddeli olmalı. Uzun gerekçe yerine: ne değişti, nerede, nasıl denendi, ne denenmedi.
- „Evet, devam et“, „Evet, birleştir“ gibi tek satırlık onaylar verir; önerilen sıradaki adımı net bir soruyla sunmak işe yarıyor.

## Karar önce, kod sonra
- Her karar **önce DECISIONS.md'ye yeni D-numarası**, SPEC/DESIGN-PRINCIPLES güncellenir, **ayrı bir belge commit'i**; sonra kod (CLAUDE.md).
- Büyük işler önce **kapsam ve sıra önerisi** olarak sunulur, onay gelince başlanır (D-017, D-038). Dilimler ve dilim içi parçalar **küçük ve tek tek denenebilir** olmalı.
- Cankat'ın istemediği her ekleme **„Claude'un ekledikleri (onay bekliyor)“** diye işaretlenir; sonra toplu olarak sorulur (D-045). Onaysız ekleme sessizce yapılmaz.
- Açık bir soru kalmışsa bırakılmaz; birikenler bir noktada listelenip sorulur.

## Yöntem: „İyi tasarımın ilkeleri“
- Her tasarım kararı dört aşamadan geçer: **Çıkar → Sağlamlaştır → Ekle → Tekrar bak.** Yeni özellik ancak kanıtla girer (SPEC 6.12).
- Denetim istendiğinde **kontrol listesine madde madde** bakılır; yüzeysel denetimi fark eder ve geri çevirir (D-029/030 öncesi: „sadece bunları mı buldun?“).
- **Aynı şeyin tek adı** var (SPEC 4.10). **Açıklama metni son çare**: önce tasarım düzeltilir.
- **Onay penceresi yerine „Rückgängig“**; kullanıcıyı yoran ara adım istemez („üşenmeye yol açacak şeyler olmamalı“).
- **Kullanım sıklığına göre yer**: en sık iş en üstte / en kolay yerde (ör. Nehmen başlığın altında, Büro'da önce raf fotoğrafı).
- **Gerçek dünyayı izle**: uygulama, insanın fiziki olarak yaptığını taklit etmeli (D-022: „odaya gidilir, ünite görülür, rafa konur“). Ayrı pencere/seçici yerine doğal akış.

## Geri bildirim biçimi
- **İteratif, görsel geri bildirim** verir: ekran görüntüsü üstüne çizim, „şu kadar büyük“, „şu kadar sola“, oranlar („QR yüksekliğinin %70'i“).
- Ölçü ve hizada titizdir (etiketlerde mm düzeyinde). Değişiklikten sonra **örnek çıktı** (PNG/PDF) görmek ister.
- Bir şeyi yanlış anladıysan doğrudan söyler („ortala derken … istememiştim“); o zaman düzelt, kararı belgede güncelle.
- Uygulamayı kendisi dener (beta, telefon) ve **gördüğü sorunu** getirir; „bunu denedin mi?“ sorusuna dürüst cevap ister: denenmeyen şey „denendi“ diye anlatılmaz.

## Tercihler (içerik)
- **Sade, modern, minimal**; telefonda da masaüstünde de mobil uygulama hissi. Anlamsız efekt yok.
- Renkler: beyaz açık tema, antrasit koyu tema, **amber** vurgu; pastel oda renkleri; „renk üstüne renk“ yok (THEMA.md).
- Etiketler: gerçek baskıya göre düşün (3 mm güvenli kenar, büyük „miaza“, okunurluk); çoğunlukla **38 mm rulo** kullanılacak.
- Ürün adları üreticinin orijinal adı; çeviri yok.
- Görüntü kirliliği istemez (ör. „Ohne Platz“ rozeti yok).
- Pratik: „sonradan kırpma gerekmez, gerekirse fotoğraf yeniden eklenir“ gibi en sade çözümü seçer.

## Teknik çalışma kuralları
- Commit küçük, başlık Almanca, yazar `Cankat Dönmez <cankatdonmez@gmail.com>`; sonuna `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Push ve main'e birleştirme yalnız istenince.**
- **Gerçek veriye (beta 8090, `finds.db`) dokunma**; denemeler `dev.db` (8091) üzerinde. Gerçek veriye yazmak yalnız açık istekle.
- Şifre girme yok; Systembereich'i Cankat yönetir.
- Her kod değişikliğinden sonra testler + dev sunucusunu yeniden başlat + tarayıcıda kendin dene; sonra raporla.
- STATUS.md < 40 satır, her adımdan sonra güncel.
- Dosya indirme, dış hizmete yükleme gibi işlerde önce sor (kaynak, boyut).

## Çalışma düzeni
- Uzun oturumlarda iş bitince bir sonraki adımı **sorarak** önerirsin; Cankat çoğu zaman „devam et“ der.
- Cankat aynı projede **birden çok oturum** (uygulama ve terminal) açabiliyor; ortak dosyalarda başka oturumun değişikliği olabilir. Yazmadan önce git durumuna ve DECISIONS'ın sonuna bak; D-numarası çakışmasın.
- Konudan sapmayı sever değil: „onlar boşver, işimize bakalım“. Yan konuları kısa tut.
