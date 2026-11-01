# miaza finds — çalışma notları

Bu klasör **miaza finds** uygulamasının proje klasörüdür. Uygulama, büronun malzeme kütüphanesi ve ofis düzeni içindir. Bu dosyayı her oturumun başında oku.

## Durum (01.11.2026)

- Tasarım aşaması bitti. **SPEC 0.4** hazır ve onaylı; sıradaki iş gerçek uygulamaya başlamak.
- Proje, Zeiterfassung'un (miaza counts) geliştirildiği dizüstünde sürdürülecek. Altyapı, klasör yapısı, CSS değişkenleri, Docker ayarı ve test düzeni oradan alınacak; iki uygulama aynı ailenin üyesi gibi görünmeli.

## Dosyalar

| Dosya | Ne |
|---|---|
| `SPEC.md` | Ürün spesifikasyonu (0.4). Ne yapılacağının tek kaynağı. |
| `DESIGN-PRINCIPLES.md` | Tasarım ilkeleri, kontrol listesi ve karar tablosu. |
| `DEGERLENDIRME-0.3.md` | SPEC 0.4'ü doğuran dört aşamalı değerlendirme. |
| `demo/` | Tıklanabilir demonun kaynakları (`*.dc.html`) ve ofis planı PDF'i. Demo SPEC 0.3 düzeyindedir, 0.4'e güncellenmedi. |

**Çevrimiçi:**
- Demo: https://claude.ai/artifact/TTfaBZw1D3zk9AxwFFjuzT
- "İyi tasarımın ilkeleri" yol haritası: https://claude.ai/artifact/QaExctb1FhszrLeDNitvt1
- Zeiterfassung: https://claude.ai/artifact/AE8iJcycwFmTzU1jaHJemb

## Çalışma kuralları (kullanıcının istekleri)

- **Dil:** kullanıcıyla Türkçe konuşulur. Uygulamanın arayüzü Almanca olacak (terimler: SPEC 4.10).
- **Yöntem:** her tasarım ve özellik kararı "İyi tasarımın ilkeleri" yol haritasının dört aşamasından geçer: **Çıkar → Sağlamlaştır → Ekle → Tekrar bak.**
  - Her parçanın bir sahibi ve gerekçesi olur.
  - Yeni özellik ancak kanıtla girer (SPEC 6.12).
  - Aynı şeyin tek bir adı vardır.
  - Açıklama metni son çaredir.
- **İlkeler:** sade, kullanışlı, modern, minimal. Telefonda da masaüstünde de mobil uygulama hissi verir.
  - Yer, kullanım sıklığına göre verilir; seyrek kullanılan şey ayarlara gider.
  - Anlamsız efekt olmaz.
  - Kullanıcı rahatsız edilmez: kontrol adımları atlanabilir, onay penceresi yerine geri al tercih edilir.
  - Ayrıntılar `DESIGN-PRINCIPLES.md` dosyasında.
- **Kendi önerilerini işaretle:** kullanıcının istemediği bir şeyi eklersen bunu açıkça söyle ve onay iste.

## Gerçek uygulama: önerilen başlangıç

**Altyapı** (SPEC 8.1): Python 3.12+, FastAPI, uvicorn, Jinja2, SQLite (WAL), düz JS (build adımı yok), tek CSS dosyası, pytest. Miaza counts ile aynı.

**Dilimler** (Gall: küçük ve çalışır başla):
1. **Kütüphane ve kayıt:** arama, filtreler, tek ve seri kayıt, kategori ve filtre ayarları, ürün etiketi PDF'i. Büro bu dilimle ürün girmeye başlar; ürünler önce konumsuz kalır.
2. **Ofis:** plan düzenleyici, üniteler, bölmeler, bölme etiketleri, ofis görünümü. Konumsuz ürünler bölme QR'ıyla toplu yerleştirilir.
3. **Hareket:** ürünü alma, yerine koyma, bölme onayı, "Düzenleniyor" uyarısı.
4. **Kalanlar:** koleksiyonlar, istatistik, yedek, Almanca son okuma.

**Kamera:** uygulama önce HTTPS olmadan çalışacak şekilde yazılır ("Fotoğrafla okut"). Canlı kamera, HTTPS varsa kendiliğinden devreye girer (SPEC 8.2). HTTPS yolu (A: alan adı + Let's Encrypt, B: kendi kök sertifikası) henüz açık bir soru.

## Bu klasör Google Drive'da: dikkat edilecekler

- **Sanal ortam (`.venv`) ve geliştirme veritabanı bu klasörün dışında tutulur**, ör. `%LOCALAPPDATA%\miaza-finds\`. Binlerce küçük dosya ve açık bir SQLite dosyası Drive eşitlemesini bozar.
- **Git deposu burada durabilir ama:**
  - Aynı anda tek bilgisayarda çalışılır.
  - Bilgisayar değiştirmeden önce Drive'ın eşitlemeyi bitirmesi beklenir.
  - Güvenlik için ileride özel bir uzak depo (ör. GitHub, private) eklenmesi önerilir.
- Klasörün yolu uzun (Drive kısayolu). Windows'taki 260 karakter sınırına takılmamak için derin klasör yapısından kaçınılır. Gerekirse Git'te `core.longpaths true` açılır.

## Açık sorular (SPEC 11)

1. Brother yazıcı modeli (v2).
2. HTTPS yolu: büronun alan adı ve sağlayıcısı, ofisteki modem.
3. Etiket kâğıdının düzen PDF'i. Kullanıcı gönderecek.
4. Google Drive masaüstü uygulaması mini PC'de mi?
5. de-AT biçimleri ve Almanca terimlerin kesinleşmesi.
6. "finds" ve "counts" vurgu renkleri.

## Demo notu

`demo/test-harness.html` dosyası `.dc.html` kaynaklarını `project/` alt klasöründen okur. Yerel önizleme için dosyaları bir `project/` klasörüne koyup basit bir HTTP sunucusuyla açmak gerekir.
