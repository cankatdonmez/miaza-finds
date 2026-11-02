# miaza finds — tema

Bu dosya finds'ın renk temasını anlatır (D-023, D-024). Amaç: miaza counts ya da ailenin başka bir uygulaması aynı
yöntemle kendi temasını kurabilsin. Değerlerin tek kaynağı `app/static/css/app.css` dosyasının başındaki token bloğudur;
bu dosya onu açıklar.

## İlkeler

1. **İki tema birlikte tasarlanır.** Açık: beyaz zemin. Koyu: nötr antrasit (mavi alt ton yok).
2. **Tek vurgu rengi.** finds için amber. Vurgu yalnız şunlar içindir: birincil düğme, seçili olan, bağlantı, odak çizgisi.
3. **Renk üstüne renk yok.** Bir zemin hangi renk ailesindense, üstündeki yazı ve ikon da o ailedendir:
   - Açık temada: açık zemin + aynı ailenin koyu tonu (ör. `#FDF0DA` üstüne `#9A5600`).
   - Koyu temada: koyu zemin + aynı ailenin açık tonu (ör. `#3A2E1B` üstüne `#FFC870`).
   - Dolu vurgu düğmesinde yazı koyu kahve `#2A1A05` (amber ailesinin en koyusu). Amber düğmede mor ya da beyaz yazı olmaz.
4. **Renk anlam taşır.** Vurgu, üç durum, dijital tür ve planda oda renkleri. Başka yerde renk yok; geri kalan her şey
   gri tonlarıdır.
5. **Okunurluk.** Yazı ile zemini arasında en az 4,5:1. Renk tek başına anlam taşımaz; yanında yazı ya da açıklık farkı olur.
6. **Etiketler ve PDF'ler** her zaman açık renklidir (papier tokenları).

## Temel tokenlar

| Token | Açık | Koyu | Ne için |
|---|---|---|---|
| `--bg` | `#FFFFFF` | `#18191B` | sayfa zemini |
| `--card` | `#FFFFFF` | `#212224` | kart, panel, giriş alanı |
| `--sunk` | `#F6F6F5` | `#1C1D1F` | gömülü alanlar, boş görsel |
| `--ink` | `#1C1C1E` | `#EDEDEC` | metin |
| `--muted` | `#66656A` | `#A1A1A0` | ikincil metin |
| `--line` | `#E8E8E6` | `#303134` | kart kenarı, ayırıcı |
| `--line-2` | `#D6D5D2` | `#3D3E42` | giriş alanı kenarı |
| `--accent` | `#F2A43A` | `#F5AE3D` | birincil düğme zemini, seçili çizgi |
| `--accent-ink` | `#9A5600` | `#FFC870` | vurgu yazısı (bağlantı, seçili satır) |
| `--accent-soft` | `#FDF0DA` | `#3A2E1B` | seçili satır / menü zemini |
| `--on-accent` | `#2A1A05` | `#2A1A05` | dolu vurgu üstündeki yazı |

Açık temada kartlar zeminle aynı beyazdır; onları ince kenar çizgisi ayırır, gölge değil.

## Durum renkleri (her biri zemin + yazı çifti)

| Durum | Açık zemin / yazı | Koyu zemin / yazı |
|---|---|---|
| Am Platz (yeşil) | `#DCFCE7` / `#166534` | `#14351F` / `#86EFAC` |
| In Benutzung (mavi) | `#DBEAFE` / `#1E40AF` | `#172A4D` / `#93C5FD` |
| Außer Haus (gül) | `#FBE5EE` / `#9D2F5E` | `#45263A` / `#F2A7C3` |
| Digital (mor) | `#EDE9FE` / `#5B21B6` | `#2A1F4A` / `#C4B5FD` |

Durum renkleri ambere benzememeli; „Außer Haus“ bu yüzden sarıdan güle geçti.

## Oda renkleri (planda)

Altı pastel; her birinin dört tonu var: **oda** zemini, **ünite** (bir ton koyusu; koyu temada bir ton açığı),
**kenar** ve **yazı**. Odanın içindeki üniteler odanın ailesindendir; böylece raflar odalarıyla eşleşmiş görünür.

| Renk | Açık: oda · ünite · kenar · yazı | Koyu: oda · ünite · kenar · yazı |
|---|---|---|
| 1 Salbei | `#DCEBDB` · `#B5D3B3` · `#6F9A6C` · `#2F4A2E` | `#2E3B33` · `#435A4A` · `#8DB39A` · `#D4E8D8` |
| 2 Himmel | `#D9E7F3` · `#AFCCE6` · `#5F8DB8` · `#23405E` | `#2B3846` · `#3F5469` · `#8BB0D6` · `#D3E4F5` |
| 3 Lavendel | `#E4DFF3` · `#C6BCE6` · `#7E70B8` · `#3A3166` | `#36324A` · `#4E4769` · `#ADA2E0` · `#E2DDF7` |
| 4 Pfirsich | `#F9E0D1` · `#F0BFA3` · `#C27A55` · `#5C3220` | `#46352C` · `#654B3D` · `#E0A483` · `#F7DFD2` |
| 5 Vanille | `#F6EDCC` · `#E8D696` · `#A88E3A` · `#4D3F12` | `#433D2B` · `#5F563A` · `#D2BE7C` · `#F3EBCB` |
| 6 Rosé | `#F3DAE2` · `#E6B3C3` · `#B76A84` · `#55263A` | `#443039` · `#624451` · `#D99BB0` · `#F5DAE3` |
| 0 odasız | — · `#E6E6E4` · `#8E8C88` · `#333336` | — · `#3A3B3E` · `#9A9A98` · `#E5E5E5` |

- Seçili ünite: kenar kalınlaşır ve **yazı** tonuna döner. Başka renk eklenmez.
- Altlık açıkken odalar %50 saydamdır.
- Tokenlar: `--raum-N`, `--raum-N-einheit`, `--raum-N-rand`, `--raum-N-tinte`. Çizimde bir şekle
  `--f/--e/--r/--t` değişkenleri olarak verilir (`MF.raumStil`).

## counts için

counts bu yapıyı aynen alabilir: aynı token adları, aynı iki zemin (beyaz / antrasit), aynı „renk üstüne renk yok“
kuralı. Değişen tek şey **vurgu ailesi** olur (ör. finds amber, counts başka bir aile); vurgunun dört tokenu
(`--accent`, `--accent-ink`, `--accent-soft`, `--on-accent`) o ailenin tonlarıyla doldurulur ve yukarıdaki
okunurluk kontrolü yapılır.
