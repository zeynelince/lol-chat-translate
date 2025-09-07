# -*- coding: utf-8 -*-
from __future__ import annotations
import time, shutil, sys, ctypes, re
from pathlib import Path
import tkinter as tk
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk

import pytesseract
from pytesseract import Output
from PIL import Image, ImageOps, ImageTk
import mss
from deep_translator import GoogleTranslator

# ---------- Ayarlar ----------
LANG_OCR   = "eng"   # Tesseract OCR dili: "eng", "tur", "jpn" ...
DEST_LANG  = "tr"    # Çeviri dili
REFRESH_MS = 300     # ms cinsinden tarama aralığı (~3 FPS)
MIN_CHARS  = 2       # Çok kısa satırları at

DEFAULT_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def ensure_tesseract():
    if Path(DEFAULT_TESSERACT).exists():
        pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT
        return
    found = shutil.which("tesseract")
    if found:
        pytesseract.pytesseract.tesseract_cmd = found
        return
    raise FileNotFoundError(
        "Tesseract bulunamadı. Windows'ta genelde "
        r"C:\Program Files\Tesseract-OCR\ altına kurulur."
    )
def preprocess(img: Image.Image) -> Image.Image:
    # Basit ve hızlı ön işleme: gri + autocontrast + ikili eşik
    if img.mode != "L":
        img = img.convert("L")
    img = ImageOps.autocontrast(img)
    bw  = img.point(lambda x: 0 if x < 160 else 255, "1")
    return bw

def ocr_text(pil_img, lang):
    # sohbet metni için: tek blok ama satır ayrımı kalsın
    cfg = "--oem 3 --psm 6"
    return pytesseract.image_to_string(pil_img, lang=lang, config=cfg)

def clean_text(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if len(ln) >= MIN_CHARS]
    dedup, prev = [], None
    for ln in lines:
        if ln != prev:
            dedup.append(ln)
        prev = ln
    return "\n".join(dedup).strip()

def translate_text(text: str, dest: str) -> str:
    if not text.strip():
        return ""
    try:
        return GoogleTranslator(source="auto", target=dest).translate(text)
    except Exception as e:
        return f"[Çeviri hatası: {e}]"

# ------ Ekrandan alan seçimi (tkinter overlay) ------
class RegionSelector:
    def __init__(self):
        # DPI farklarını azalt (Windows)
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

        self.root = tk.Tk()
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.25)
        self.root.overrideredirect(True)     # kenarlık yok
        self.root.state('zoomed')            # tam ekran

        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start = None
        self.rect  = None
        self.bbox  = None

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>",     self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Bilgi metni
        self.hint = self.canvas.create_text(
            20, 20, anchor="nw",
            text="Sürükleyip alan seçin (ESC: iptal)",
            fill="white", font=("Segoe UI", 14, "bold")
        )
        self.root.bind("<Escape>", lambda e: self.cancel())

    def on_press(self, event):
        self.start = (event.x, event.y)
        if self.rect:
            self.canvas.delete(self.rect)
            self.rect = None

    def on_drag(self, event):
        if not self.start:
            return
        x0, y0 = self.start
        x1, y1 = event.x, event.y
        if self.rect:
            self.canvas.coords(self.rect, x0, y0, x1, y1)
        else:
            # yarı saydam dikdörtgen
            self.rect = self.canvas.create_rectangle(
                x0, y0, x1, y1, outline="white", width=2
            )

    def on_release(self, event):
        if not self.start:
            return
        x0, y0 = self.start
        x1, y1 = event.x, event.y
        left, top = min(x0, x1), min(y0, y1)
        right, bottom = max(x0, x1), max(y0, y1)
        self.bbox = (left, top, right - left, bottom - top)
        self.root.destroy()

    def cancel(self):
        self.bbox = None
        self.root.destroy()

    def select(self) -> tuple[int, int, int, int] | None:
        self.root.mainloop()
        return self.bbox
# def extract_msg_from_line(line: str) -> str | None:
#     s = line.strip()
#     if not s:
#         return None
#     # OCR normalizasyonları
#     s = (s.replace('：', ':').replace('；', ':').replace(';', ':'))

#     # ')] :' varyantları (boşluk opsiyonel)
#     m = re.search(r'[\)\]]\s*:\s*(.+)$', s)
#     if m:
#         return m.group(1).strip()

#     # Parantez/braketten sonra iki nokta düşmüşse: boşluktan sonra gelen her şey mesaj
#     m = re.search(r'[\)\]]\s+(.+)$', s)
#     if m:
#         return m.group(1).strip()

#     # En sonda kalan ':' sonrası (timestamp’teki ':' öncedir)
#     pos = s.rfind(':')
#     if pos != -1 and pos + 1 < len(s):
#         return s[pos + 1:].strip()

#     return None
# def extract_white_messages_lines(text: str) -> list[str]:
#     """
#     LoL sohbet satırlarında yalnızca ':' sonrası (beyaz) mesajı döndürür.
#     OCR hatalarına toleranslı: '):', '];', '):', ']' veya ')' + boşluk gibi durumları da yakalar.
#     """
#     out = []
#     for raw in text.splitlines():
#         s = raw.strip()
#         if not s:
#             continue

#         # Olası iki nokta varyantlarını normalize et
#         s = (s
#              .replace('：', ':')  # tam genişlikli
#              .replace('﹕', ':')
#              .replace('；', ':')  # OCR'de ':' -> ';' olabilir
#         )

#         msg = None

#         # 1) En yaygın: '... ):' veya '... ]:' (boşluk opsiyonel)
#         m = re.search(r'[\)\]]\s*:\s*(.+)$', s)
#         if m:
#             msg = m.group(1).strip()

#         # 2) Parantez/braketten sonra boşluk + mesaj (':' kaçtıysa)
#         if msg is None:
#             m = re.search(r'[\)\]]\s+(.+)$', s)
#             if m:
#                 msg = m.group(1).strip()

#         # 3) Fallback: satırdaki **son** ':' sonrası her şeyi mesaj say
#         if msg is None:
#             colon = s.rfind(':')
#             if colon != -1 and colon < len(s) - 1:
#                 msg = s[colon + 1:].strip()

#         # İstenmeyen kısa/boş satırları ele
#         if msg and len(msg) >= 1:   # '15' gibi tek/çift karakterleri de alsın
#             out.append(msg)

#     return out
# def extract_chat_messages_by_timestamp(text: str) -> list[str]:
#     """
#     OCR çıktısından LoL sohbet mesajlarını satır satır çıkarır.
#     Satır sonları kaybolsa bile [mm:ss] desenini bölücü olarak kullanır.
#     """
#     # Olası iki nokta varyantlarını normalize et
#     t = text.replace('：', ':').replace('；', ':').replace(';', ':')

#     # Tüm metni tek satır gibi de gelse tarayalım
#     # Ör: [00:06] .... [00:12] .... [00:15] ...
#     chunks = re.findall(r'\[\s*\d{1,2}\s*:\s*\d{2}\s*\][^\[]+', t)

#     msgs = []
#     for seg in chunks:
#         # ']' sonrası ilk ':' mesaj ayırıcı kabul
#         rb = seg.find(']')
#         colon = seg.find(':', rb + 1 if rb != -1 else 0)
#         if colon == -1:
#             colon = seg.rfind(':')  # emniyet kemeri
#         if colon != -1 and colon + 1 < len(seg):
#             msg = seg[colon + 1:].strip()
#             if msg:
#                 msgs.append(msg)
#     return msgs
# def extract_white_messages(text: str) -> str:
#     """
#     Her satırdan yalnızca ':' karakterinden sonraki kısmı döndürür.
#     Zaman damgasındaki (00:06) ':' dikkate alınmaz.
#     ':' bulunmazsa satır atlanır.
#     """
#     out = []
#     for line in text.splitlines():
#         s = line.strip()
#         if not s:
#             continue
#         s = s.replace('：', ':')  # olası tam genişlikli iki nokta

#         # Tipik desen: "...): MESAJ"
#         m = re.search(r'\):\s*(.+)$', s)
#         if m:
#             msg = m.group(1).strip()
#         else:
#             # ']' kapandıktan sonraki ilk ':' mesaj ayracıdır
#             rb = s.find(']')
#             pos = s.find(':', rb + 1 if rb != -1 else 0)
#             if pos != -1:
#                 msg = s[pos + 1:].strip()
#             else:
#                 # ':' yoksa (ör. "Type /help...") satırı es geç
#                 continue

#         if len(msg) >= MIN_CHARS:
#             out.append(msg)
#     return "\n".join(out)
def preprocess_for_data(img: Image.Image) -> Image.Image:
    # image_to_data için binarize ETME; gri + autocontrast daha iyi satır/kelime verir
    if img.mode != "L":
        img = img.convert("L")
    return ImageOps.autocontrast(img)

def read_header_and_message_pairs(img_gray: Image.Image, lang: str) -> list[tuple[str, str]]:
    """
    image_to_data ile satırları kelime kelime topla; aynı satırda ':' konumuna göre
    HEADER = ':' öncesi (zaman + isim + şampiyon + ':')
    MESSAGE = ':' sonrası (beyaz kısım)
    """
    d = pytesseract.image_to_data(img_gray, lang=lang,
                                  config="--oem 3 --psm 6",
                                  output_type=Output.DICT)
    pairs = []
    cur_key = None
    words = []

    def flush_line(ws):
        if not ws:
            return
        # ':' bazlı ayırma (toleranslı)
        norm = [w.replace('：', ':').replace('；', ':').replace(';', ':') for w in ws]
        idx = -1
        for i, w in enumerate(norm):
            if w == ":" or w.endswith(":") or ":" in w:
                idx = i
                break
        if idx == -1:
            # emniyet: satırda en SON ':' nerede?
            for i in range(len(norm) - 1, -1, -1):
                if ":" in norm[i]:
                    idx = i
                    break
        if idx == -1 or idx == len(norm) - 1:
            return  # ':' yoksa/sondaysa mesaj yok

        header_tokens = norm[:idx + 1]
        # baştaki/sondaki noktalama/boş tokenları temizle
        header = " ".join(t for t in header_tokens if t.strip()).strip()
        if not header.endswith(":"):
            header += ":"

        msg_tokens = norm[idx + 1:]
        message = " ".join(t for t in msg_tokens if t.strip()).strip()

        if len(message) >= MIN_CHARS:
            pairs.append((header, message))

    n = len(d["text"])
    for i in range(n):
        txt = (d["text"][i] or "").strip()
        try:
            conf = int(float(d["conf"][i]))
        except Exception:
            conf = 0
        if conf < 45 or not txt:
            continue

        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        if key != cur_key:
            flush_line(words)
            words = []
            cur_key = key
        words.append(txt)

    flush_line(words)
    return pairs
def normalize_ocr_paragraph(t: str) -> str:
    """OCR çıktısını noktalama ve satır sonlarını bozmayacak şekilde toparla."""
    if not t: 
        return ""
    # OCR'nin ':' yerine farklı karakterler yazmasını normalize et
    t = t.replace('：', ':').replace('；', ':').replace(';', ':')
    # tireyle bölünmüş kelimeleri birleştir: "humor-\nous" -> "humorous"
    t = re.sub(r'-\s*\n', '', t)
    # fazla satır sonlarını sadeleştir
    t = re.sub(r'\s+\n', '\n', t)
    t = re.sub(r'\n+', '\n', t)
    # cümle ortası newline'ları boşluğa çevir (paragraf gibi akıt)
    t = re.sub(r'(?<![.!?])\n', ' ', t)
    # fazla boşlukları temizle
    t = re.sub(r'\s+', ' ', t).strip()
    return t
def split_by_timestamps(big_text: str) -> list[str]:
    """
    Paragraf gibi gelse bile [mm:ss] desenine göre segmentlere ayır.
    Örn: [00:06] ... [00:12] ... -> ["[00:06] ...", "[00:12] ..."]
    """
    t = big_text
    pat = re.compile(r'\[\s*\d{1,2}\s*:\s*\d{2}\s*\]')
    starts = [m.start() for m in pat.finditer(t)]
    if not starts:
        return []
    segs = []
    for i, st in enumerate(starts):
        en = starts[i+1] if i+1 < len(starts) else len(t)
        segs.append(t[st:en].strip())
    return segs

def split_header_message(segment: str) -> tuple[str, str] | None:
    """
    Segment'i 'HEADER: MESSAGE' olarak ikiye ayır.
    HEADER = zaman + isim + şampiyon + ':' (renkli kısım)
    MESSAGE = ':' sonrası (beyaz kısım)
    """
    s = segment.strip()
    if not s:
        return None
    # zaman damgasının kapanışı neredeyse oradan sonra ilk ':' mesaj ayracıdır
    rb = s.find(']')
    pos = s.find(':', rb + 1 if rb != -1 else 0)
    if pos == -1:               # emniyet kemeri: en sondaki ':' da olabilir
        pos = s.rfind(':')
    if pos == -1 or pos + 1 >= len(s):
        return None
    header  = s[:pos+1].strip()
    message = s[pos+1:].strip()
    if not message:
        return None
    return header, message
def live_capture_loop(bbox: tuple[int,int,int,int], ocr_lang: str, dest: str):
    import mss
    from tkinter.scrolledtext import ScrolledText
    from collections import deque

    left, top, width, height = bbox
    monitor = {"left": left, "top": top, "width": width, "height": height}

    # --- Önizleme ---
    root = tk.Tk()
    root.title("Seçili Bölge Önizleme")
    panel = tk.Label(root)
    panel.pack()
    

    # Pencereyi seçili alanın DIŞINA koy (kendi penceresini yakalamasın)
    px = max(5, left - min(700, width))
    py = max(5, top - 5)
    try:
        root.geometry(f"+{px}+{py}")
    except Exception:
        pass

    # --- Çeviriler (tek satır format) ---
    tw = tk.Toplevel(root)
    tw.title("Çeviriler")
    tbox = ScrolledText(tw, width=80, height=30, wrap="word")
    tbox.pack(fill="both", expand=True, padx=6, pady=6)
    # Tek satır görünüm: hafif monospace daha derli toplu
    tbox.configure(font=("Consolas", 10))
    try:
        tw.geometry(f"+{left + width + 20}+{top}")
    except Exception:
        pass

    def append_line(header: str, translation: str):
        # header sonu ':' değilse ekle
        h = header.strip()
        if not h.endswith(":"):
            h += ":"
        # çeviri içindeki gereksiz satır sonlarını boşluk yap
        tr = " ".join((translation or "").split())
        line = f"{h} {tr}\n"
        tbox.configure(state="normal")
        tbox.insert("end", line)
        tbox.see("end")
        tbox.configure(state="disabled")

    last_ocr_ts = 0.0
    seen: set[tuple[str, str]] = set()    # (header, message)
    MIN_TRANSLATE_GAP = 0.8
    last_tr_ts = 0.0
    MAX_LINES_KEEP = 500
    pending: deque[tuple[str, str, int | None]] = deque()  # (header, message, ts_sec)
    recent_keys = deque(maxlen=200)  # (header, message) (isteğe bağlı, kalsın)
    recent_set: set[tuple[str, str]] = set()

    # ZAMAN DAMGASI FİLTRESİ
    SEEN_TS_MAX = 500
    seen_ts = deque()        # FIFO
    seen_ts_set = set()

    def remember_ts(ts: int) -> bool:
        """Yeni ts ise True döner ve kaydeder; daha önce varsa False döner."""
        if ts in seen_ts_set:
            return False
        seen_ts.append(ts)
        seen_ts_set.add(ts)
        if len(seen_ts) > SEEN_TS_MAX:
            old = seen_ts.popleft()
            seen_ts_set.discard(old)
        return True

    def remember_key(key):
        recent_keys.append(key)
        recent_set.add(key)
        while len(recent_keys) > recent_keys.maxlen:
            old = recent_keys.popleft()
            recent_set.discard(old)

    def trim_if_needed():
        # Çok uzarsa baştan kırp (performans için)
        try:
            if int(tbox.index("end-1c").split(".")[0]) > MAX_LINES_KEEP:
                tbox.configure(state="normal")
                tbox.delete("1.0", "200.0")
                tbox.configure(state="disabled")
        except Exception:
            pass

    with mss.mss() as sct:
        while True:
            # --- Ekranı yakala ---
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # --- Önizleme ---
            disp = img
            max_w = 640
            if disp.width > max_w:
                r = max_w / disp.width
                disp = disp.resize((int(disp.width * r), int(disp.height * r)))
            tkimg = ImageTk.PhotoImage(disp)
            panel.configure(image=tkimg)
            panel.image = tkimg  # GC koruması

            # --- OCR + ayrıştırma ---
            now = time.time()
            if (now - last_ocr_ts) * 1000 >= REFRESH_MS:
                pairs: list[tuple[str, str]] = []

                # 1) Birincil: token bazlı (daha sağlam)
                img_data = preprocess_for_data(img)  # gri + autocontrast
                pairs = read_header_and_message_pairs(img_data, ocr_lang)

                # 2) Yedek: timestamp’a göre böl (hiç bulamadıysa)
                if not pairs:
                    img_pre = preprocess(img)  # binarize
                    raw     = ocr_text(img_pre, ocr_lang)
                    para    = normalize_ocr_paragraph(raw)
                    for seg in split_by_timestamps(para):
                        sm = split_header_message(seg)
                        if sm:
                            pairs.append(sm)

                # Aynı karede tekrarı engelle
                seen_frame = set()

                for header, message in pairs:
                    key = (header, message)
                    if key in seen_frame or key in seen:
                        continue
                    seen_frame.add(key)

                    # Throttle: çok sık çeviri atma
                    if time.time() - last_tr_ts < MIN_TRANSLATE_GAP:
                        continue

                    tr = translate_text(message, dest)
                    append_line(header, tr)
                    trim_if_needed()

                    last_tr_ts = time.time()
                    seen.add(key)
                    if len(seen) > 800:
                        seen = set(list(seen)[-400:])

                last_ocr_ts = now

            # --- Tk olayları ---
            try:
                root.update_idletasks()
                root.update()  # Toplevel'ı da günceller
            except tk.TclError:
                break

            time.sleep(REFRESH_MS / 1000.0)
# def live_capture_loop(bbox: tuple[int,int,int,int], ocr_lang: str, dest: str):
#     import mss
#     from tkinter.scrolledtext import ScrolledText

#     left, top, width, height = bbox
#     monitor = {"left": left, "top": top, "width": width, "height": height}

#     # --- Önizleme penceresi ---
#     root = tk.Tk()
#     root.title("Seçili Bölge Önizleme")
#     panel = tk.Label(root)
#     panel.pack()

#     # Pencereyi seçili alanın DIŞINA koy (kendi kendini yakalamasın)
#     px = max(5, left - min(700, width))
#     py = max(5, top - 5)
#     try:
#         root.geometry(f"+{px}+{py}")
#     except Exception:
#         pass

#     # --- Çeviriler penceresi ---
#     tw = tk.Toplevel(root)
#     tw.title("Çeviriler")
#     tbox = ScrolledText(tw, width=60, height=30, wrap="word")
#     tbox.pack(fill="both", expand=True, padx=6, pady=6)
#     tbox.tag_configure("hdr", font=("Segoe UI", 9, "bold"))
#     tbox.tag_configure("sep", foreground="#888")
#     tbox.tag_configure("tr",  font=("Segoe UI", 10))
#     try:
#         tw.geometry(f"+{left + width + 20}+{top}")
#     except Exception:
#         pass

#     def append_translation(header: str, translation: str):
#         tbox.configure(state="normal")
#         tbox.insert("end", header + "\n", ("hdr",))
#         tbox.insert("end", "—" * 36 + "\n", ("sep",))
#         tbox.insert("end", translation + "\n\n", ("tr",))
#         tbox.see("end")
#         tbox.configure(state="disabled")

#     last_ocr_ts = 0.0
#     seen: set[tuple[str, str]] = set()  # (header, message)
#     MIN_TRANSLATE_GAP = 0.9  # hız limiti; çok istek atmasın
#     last_tr_ts = 0.0

#     with mss.mss() as sct:
#         while True:
#             # --- Ekranı yakala ---
#             sct_img = sct.grab(monitor)
#             img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

#             # --- Önizleme ---
#             disp = img
#             max_w = 640
#             if disp.width > max_w:
#                 r = max_w / disp.width
#                 disp = disp.resize((int(disp.width * r), int(disp.height * r)))
#             tkimg = ImageTk.PhotoImage(disp)
#             panel.configure(image=tkimg)
#             panel.image = tkimg  # GC koruması

#             # --- OCR + HEADER/MESSAGE ayırma ---
#             now = time.time()
#             if (now - last_ocr_ts) * 1000 >= REFRESH_MS:
#                 pairs: list[tuple[str, str]] = []

#                 # 1) Birincil: token bazlı (image_to_data)
#                 img_data = preprocess_for_data(img)  # gri + autocontrast
#                 pairs = read_header_and_message_pairs(img_data, ocr_lang)  # [(header, message), ...]

#                 # 2) Yedek: timestamp’a göre string bölme (hiç bulamadıysa)
#                 if not pairs:
#                     img_pre = preprocess(img)          # binarize
#                     raw     = ocr_text(img_pre, ocr_lang)
#                     para    = normalize_ocr_paragraph(raw)
#                     for seg in split_by_timestamps(para):
#                         sm = split_header_message(seg)
#                         if sm:
#                             pairs.append(sm)

#                 # Aynı karede tekrarı engelle
#                 seen_frame = set()

#                 for header, message in pairs:
#                     key = (header, message)
#                     if key in seen_frame or key in seen:
#                         continue
#                     seen_frame.add(key)

#                     # sadece ':' sonrası çeviri; header aynen
#                     # rate limit koruması
#                     if now - last_tr_ts < MIN_TRANSLATE_GAP:
#                         continue
#                     tr = translate_text(message, dest)
#                     append_translation(header, tr)
#                     last_tr_ts = time.time()

#                     seen.add(key)
#                     if len(seen) > 800:
#                         seen = set(list(seen)[-400:])

#                 last_ocr_ts = now

#             # --- Tk olayları ---
#             try:
#                 root.update_idletasks()
#                 root.update()  # Toplevel'ı da günceller
#             except tk.TclError:
#                 break

#             time.sleep(REFRESH_MS / 1000.0)

def main():
    ensure_tesseract()
    print(">> Ekrandan bir alan seçin...")
    selector = RegionSelector()
    bbox = selector.select()
    if not bbox:
        print("İptal edildi.")
        sys.exit(0)
    if bbox[2] <= 0 or bbox[3] <= 0:
        print("Geçersiz seçim (genişlik/yükseklik 0). Tekrar deneyin.")
        sys.exit(1)

    try:
        live_capture_loop(bbox, LANG_OCR, DEST_LANG)
    except KeyboardInterrupt:
        print("\nÇıkıldı.")

if __name__ == "__main__":
    main()
