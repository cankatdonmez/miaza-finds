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
