# STATUS

Stand: 09.11.2026 · v0.3.0 · SPEC 0.5 · Dal `main` (`origin/main`'den önde; push yalnız istenince)
Çalışma kopyası: `C:\Users\canka\Documents\miaza-finds` (D-049; Google Drive artık kullanılmıyor)
Akış: çok ajanlı (07.11.2026, etiket `pre-multiagent`): Yönetici + mimar/kodlayici/denetci/kesifci; bkz. CLAUDE.md.

## Aktueller Stand
- **Dilim 1–3 main'de, 229 test yeşil.** Ayrıntı ve kanıtlar: `DEVIR.md` (§5), kararlar: `DECISIONS.md` D-001…D-050.
  - Dilim 1: kütüphane, ürün kaydı, seri kayıt, kategori/filtre, etiket PDF'i, Systembereich.
  - Dilim 2: plan düzenleyici, üniteler, bölmeler, Büro görünümü, bölme etiketleri, „Hier einordnen“, tema (D-023/24).
  - Dilim 3: kişiler, Nehmen/Zurücklegen, Scannen (jsQR), bölme onayı, okutarak yerleştirme, „Wird bearbeitet“.
- **Dilim 4 (D-046):** ~~Statistik~~ → ~~Sammlungen (D-047)~~ → **Dokumente** → Nachtsicherung → Almanca son okuma.
- **Etiketler:** yalnız A4 24'lü (3 × 8) ve 38 mm rulo (Brother QL-570), varsayılan rulo (D-049, D-045).
- Bütün mevcut veri ve QR'lar **demo** (D-049); gerçek veri sunucu kurulunca başlar.
- Dev: `preview_start "dev"` → 8091, `dev.db`; `--reload` yok, kod değişince sunucuyu yeniden başlat.

## Sıradaki (çok ajanlı akış, `PLAN.md`)
1. ~~PLAN 1: aramada bölme kodu~~ (D-050: kod tam/baştan eşleşir, yalnız bölme koduna bakar) — main'de.
2. ~~PLAN 2: kartta konum kodu~~ (masaüstünde fareyle/odakla, tıklayınca Büro) — main'de.
3. PLAN 3–4: koyu temada altlık, açılış ekranı (karar gerektirmez).
4. PLAN 5–7 karar bekliyor: Dokumente (kök klasör), kart yayı/yelpaze, Almanca son okuma.
5. Cankat: gerçek dünya testi (etiket bas, telefonla okut) — demo verisiyle.

## Bekleyenler (acelesi yok, D-049)
- Gece yedeği (SPEC 8.4), HTTPS ve canlı kamera (SPEC 8.2), kalıcı QR adresi (`MF_BASIS_URL`):
  uygulama tamamlanıp sunucuya kurulurken konuşulacak.
- Mini PC kurulumu: teknisyen belgesi https://claude.ai/artifact/KtCQDEkSQeHfcE4NGtbAoW (denenmedi).
- „Linkten doldurma“ en son (D-048).

## Offene Fragen
1. SPEC 11: Drive uygulaması mini PC'de mi (yedek kopyası için), de-AT terimleri („Bibliothek“ adı), counts'un vurgu rengi.
2. Doküman kök klasörünün yeri (Dokumente'den önce).
3. Docker yolu kaldırılsın mı (D-003)? Mini PC Windows + start.bat.
