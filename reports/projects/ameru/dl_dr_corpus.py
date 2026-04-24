#!/usr/bin/env python3
"""6本DR-LPから画像URL抽出+DL。
WebFetch代わりにurllib+re（正規表現）で<img src>抽出。
出力: corpus/dr/<brand>_<idx>.png + corpus_dr_metadata.json
"""
import re, json, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "corpus" / "dr"
OUT.mkdir(parents=True, exist_ok=True)
META_OUT = ROOT / "corpus_dr_metadata.json"

LPS = [
    ("regina", "https://sb.reginaclinic.jp/ab/enq_google_offer_d_001",
     {"brand":"regina_clinic","genre":"beauty_medical_dr","category":"脱毛"}),
    ("laric", "https://b-ris.shop/Landing/larichscalp/cb4_02_1500_men2/",
     {"brand":"laric_scalp","genre":"haircare_dr","category":"育毛スカルプ"}),
    ("yuriiro", "https://ec.e-seeds.co.jp/lp/yuriiro/oil_061/",
     {"brand":"yuriiro","genre":"beauty_dr","category":"美容オイル"}),
    ("kimie", "https://toyama-jobiyaku.co.jp/lp?u=kimie_placenta_white_premium_mono_01_link_lv_GDN_01",
     {"brand":"kimie_placenta","genre":"skincare_dr","category":"プラセンタ美容液"}),
    ("meimoku", "https://sakura-forest.com/lp/meimoku/dis_me_T01_g_1.html",
     {"brand":"meimoku","genre":"health_medicine_dr","category":"健康医薬品"}),
    ("felissimo", "https://www.felissimo.co.jp/couturier/iamwithyou/iamwithyou_ct.html",
     {"brand":"felissimo_iamwithyou","genre":"craft_kit","category":"手芸キット"}),
]

IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
BG_RE  = re.compile(r'background(?:-image)?\s*:\s*url\(["\']?([^"\')]+)', re.IGNORECASE)

def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read()
    for enc in ("utf-8","shift_jis","cp932","euc_jp"):
        try: return raw.decode(enc)
        except: pass
    return raw.decode("utf-8", errors="ignore")

def absolutize(url: str, base: str) -> str:
    if url.startswith("//"): return "https:" + url
    if url.startswith("http"): return url
    return urllib.parse.urljoin(base, url)

def safe_name(u: str) -> str:
    name = Path(urllib.parse.urlparse(u).path).name
    return re.sub(r"[^\w.\-]", "_", name) or "img"

def dl(url: str, out: Path) -> bool:
    if out.exists() and out.stat().st_size > 1000: return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            out.write_bytes(r.read())
        return out.stat().st_size > 1000
    except Exception as e:
        return False

SECTION_KEYWORDS = [
    (["fv","hero","main","top","kv"], "fv"),
    (["price","offer","kakaku","otoku","discount","off"], "offer"),
    (["voice","user","review","kuchikomi","jirei","case","rei"], "proof_voice"),
    (["media","tv","hosou","tvcm"], "proof_media"),
    (["nayami","nayam","worry","pain","conflict"], "empathy"),
    (["seibun","ingredient","koudou","effect"], "solution"),
    (["faq","qna","question","qa"], "faq"),
    (["cta","button","btn","buy","kounyu","touroku"], "cta"),
    (["step","flow","tejun","method"], "how"),
    (["hikaku","compare","before","after"], "compare"),
    (["hosho","guarantee","henkin","anshin"], "guarantee"),
    (["logo"], "logo"),
]

def infer_section(filename: str) -> str:
    low = filename.lower()
    for kws, sec in SECTION_KEYWORDS:
        for k in kws:
            if k in low: return sec
    return "other"

def main():
    all_meta = {}
    for prefix, url, base_meta in LPS:
        print(f"\n=== {prefix} ({base_meta['brand']}) ===")
        try:
            html = fetch_html(url)
        except Exception as e:
            print(f"  ❌ html fetch failed: {e}")
            continue
        urls = set()
        for m in IMG_RE.finditer(html):
            urls.add(absolutize(m.group(1), url))
        for m in BG_RE.finditer(html):
            urls.add(absolutize(m.group(1), url))
        # filter: skip obvious tracking/transparent pixels
        urls = [u for u in urls if not any(x in u.lower() for x in [
            "pixel","tracker","ghostery","google-analytics","logo-header",
            "icon-","favicon",".svg"])]
        urls = [u for u in urls if u.lower().endswith((".jpg",".jpeg",".png",".webp",".gif"))]
        print(f"  found {len(urls)} image URLs")

        saved = 0
        for i, u in enumerate(urls):
            fname = f"{prefix}_{i:03d}_{safe_name(u)}"
            out = OUT / fname
            if dl(u, out):
                sec = infer_section(u)
                meta = dict(base_meta)
                meta["section"] = sec
                meta["src"] = u
                all_meta[fname] = meta
                saved += 1
        print(f"  ✅ saved {saved}")

    META_OUT.write_text(json.dumps(all_meta, ensure_ascii=False, indent=2))
    print(f"\n=== total {len(all_meta)} DR images in corpus/dr/ ===")
    # セクション別カウント
    from collections import Counter
    c = Counter(m["section"] for m in all_meta.values())
    for sec, n in c.most_common():
        print(f"  {sec:15} {n}")

if __name__ == "__main__":
    main()
