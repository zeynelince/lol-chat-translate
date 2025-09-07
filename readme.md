# LoL Chat Translate (Live OCR)

Seçtiğiniz ekran bölgesindeki **LoL sohbetini** canlı olarak okur:
- Bölgeyi overlay ile **sürükle-bırak** seçersiniz.
- Seçili bölge **önizleme penceresinde** akar.
- Satırları **HEADER** (zaman + isim + şampiyon + `:`) ve **MESSAGE** (`:` sonrası) diye ayırır.
- **Tek satır görüntü**: `[25:24] Weflix (Lux): teşekkürler ekko`
- Çeviriler ayrı bir pencerede akar; tekrarları filtreler.

> Python 3.12/3.13 ile test edildi. Çeviride `deep-translator` (Google) kullanır.

## Özellikler
- Token-bazlı ayırma (`image_to_data`) + timestamp fallback ⇒ bozuk `:` ve satır kırılmalarına dayanıklı
- Kaynak kodda **Tesseract yolu** (Windows): `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Hafif **rate limit** ve **hafıza** kontrolü
- Önizleme için tek `PhotoImage` buffer (daha düşük RAM)

## Kurulum
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
pip install -r requirements.txt

Çeviri servisi ücretsizdir; bazen hız limiti olabilir.

Performans için REFRESH_MS ve PREVIEW_MAX_W değerleri ayarlanabilir.