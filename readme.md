# LoL Chat Translate (Live OCR)

**Türkçe aşağıda. / Turkish below.**

## English

Live-translate **League of Legends chat** from any screen region:
- Select an area with a translucent **overlay**.
- The selected region streams in a **Preview** window.
- Each chat line is split into **HEADER** (timestamp + name + champion + `:`) and **MESSAGE** (text after `:`).
- **One-line output** per message:  
  `[25:24] Weflix (Lux): thank you ekko`
- Translations flow in a separate window; duplicates are filtered.

> Tested on Python 3.12/3.13. Uses `deep-translator` (Google) for translation.

### Features
- Token-based parsing (`image_to_data`) + timestamp fallback ⇒ robust to missing `:` and broken line wraps  
- Built-in **Tesseract path** (Windows): `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Light **rate limiting** & **memory** control
- Single `PhotoImage` buffer for preview (lower RAM)

### Installation
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
pip install -r requirements.txt

## Using other languages / Başka dillerde kullanma

You can run the app with different OCR and target languages.

### 1) Install OCR language data (Tesseract)
Make sure Tesseract has the language packs you need (e.g., Japanese, Korean, Chinese, Arabic…).  
On Windows, select the extra languages during installation or add the corresponding `*.traineddata` files into your Tesseract `tessdata` folder.

**Common Tesseract OCR codes:**
- English: `eng`
- Turkish: `tur`
- Japanese: `jpn`
- Korean: `kor`
- Chinese (Simplified): `chi_sim`
- Chinese (Traditional): `chi_tra`
- Russian: `rus`
- Arabic: `ara`
- Spanish: `spa`
- German: `deu`
> You can also combine languages, e.g. `eng+tur`.

### 2) Set languages in the app
Edit `app.py` (top of file):
```python
LANG_OCR  = "eng"  # OCR language(s) for Tesseract, e.g. "jpn", "eng+tur"
DEST_LANG = "tr"   # Translation target, e.g. "en", "de", "ja"

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