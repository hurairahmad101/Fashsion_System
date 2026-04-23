# -*- coding: utf-8 -*-
"""
GlamourBot - AI Fashion Designer
Powered by Stability AI (No Gemini needed!)
"""

import os
import sys
import pathlib
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Fix Windows encoding
if sys.platform == "win32":
    os.system("chcp 65001 >nul 2>&1")
    sys.stdout.reconfigure(encoding="utf-8")

# Groq install check
try:
    from groq import Groq
except ImportError:
    print("[!] Groq install ho raha hai...")
    import subprocess
    subprocess.check_call(["pip", "install", "groq", "-q"])
    from groq import Groq

# ================================================================
#  API KEYS
# ================================================================
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY", os.environ.get("Stabiliy_API_KEY", ""))
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")

# ================================================================
#  PAKISTANI EVENT RULES
# ================================================================
EVENT_RULES = {
    "eid":         {"weight": "light",  "colors": "pastel pink, mint green, sky blue, soft yellow, ivory",         "fabric": "lawn, chiffon, cotton", "embroidery": "minimal gota work, simple border",          "silhouette": "straight cut kameez with shalwar or trousers", "dupatta": "light chiffon dupatta"},
    "eid ul fitr": {"weight": "light",  "colors": "pastel pink, mint green, sky blue, soft yellow, ivory",         "fabric": "lawn, chiffon, cotton", "embroidery": "minimal gota work, simple border",          "silhouette": "straight cut kameez with shalwar or trousers", "dupatta": "light chiffon dupatta"},
    "eid ul adha": {"weight": "light",  "colors": "white, cream, earthy tones, beige, light green",                "fabric": "cotton, lawn",          "embroidery": "very minimal, clean lines",                 "silhouette": "simple shalwar kameez",                        "dupatta": "simple cotton dupatta"},
    "casual":      {"weight": "light",  "colors": "any comfortable colors, pastels or neutrals",                   "fabric": "cotton, lawn, khaddar", "embroidery": "no embroidery or very minimal print",       "silhouette": "relaxed fit kameez shalwar or kurta pants",    "dupatta": "optional casual dupatta"},
    "picnic":      {"weight": "light",  "colors": "bright cheerful colors, floral prints",                         "fabric": "cotton, lawn",          "embroidery": "simple prints or no embroidery",            "silhouette": "comfortable loose fit",                        "dupatta": "optional"},
    "college":     {"weight": "light",  "colors": "any, pastels or neutrals preferred",                            "fabric": "cotton, lawn",          "embroidery": "minimal or printed fabric",                 "silhouette": "simple straight kameez shalwar",               "dupatta": "simple dupatta"},
    "office":      {"weight": "light",  "colors": "navy, grey, white, black, subtle tones",                        "fabric": "cotton blend, chiffon", "embroidery": "no embroidery, clean professional look",    "silhouette": "formal straight cut kameez shalwar",           "dupatta": "formal dupatta pinned neatly"},
    "lunch":       {"weight": "light",  "colors": "soft pastels, coral, peach, blush",                             "fabric": "chiffon, cotton",       "embroidery": "light embroidery or printed",               "silhouette": "semi-casual kameez",                           "dupatta": "light dupatta"},
    "birthday":    {"weight": "medium", "colors": "rose gold, blush pink, lilac, gold, silver",                    "fabric": "chiffon, georgette",    "embroidery": "light sequins, dabka work, pearl embellishments", "silhouette": "A-line or flared kameez, or short lehenga",  "dupatta": "embellished chiffon dupatta"},
    "dawat":       {"weight": "medium", "colors": "jewel tones, teal, burgundy, forest green, royal blue",         "fabric": "silk, chiffon, organza","embroidery": "moderate embroidery, zari work",            "silhouette": "formal kameez or short gharara",               "dupatta": "embroidered dupatta"},
    "dinner":      {"weight": "medium", "colors": "black, navy, deep red, emerald green",                          "fabric": "silk, velvet, chiffon", "embroidery": "moderate embellishments, sequins",          "silhouette": "elegant maxi or formal kameez",                "dupatta": "embellished evening dupatta"},
    "mehndi":      {"weight": "medium", "colors": "yellow, green, orange, fuchsia, bright festive colors",         "fabric": "chiffon, organza, net", "embroidery": "colorful gota, dabka, mirror work",         "silhouette": "flared lehenga or sharara",                    "dupatta": "colorful heavily embellished dupatta"},
    "dholki":      {"weight": "medium", "colors": "bright colors, multicolor, hot pink, yellow, orange",           "fabric": "chiffon, cotton net",   "embroidery": "playful colorful embellishments, tassels",  "silhouette": "fun flared kameez or short lehenga",           "dupatta": "colorful dupatta"},
    "engagement":  {"weight": "medium", "colors": "blush pink, gold, peach, dusty rose, light purple",             "fabric": "silk, chiffon, organza","embroidery": "heavy embroidery, zari, sequins, pearls",   "silhouette": "lehenga or formal gharara",                    "dupatta": "heavily embroidered dupatta"},
    "nikkah":      {"weight": "heavy",  "colors": "ivory, gold, blush, mint, powder blue, pastels",                "fabric": "jamawar, silk, brocade","embroidery": "heavy zari, gota, dabka, pearl work",       "silhouette": "formal gharara or lehenga",                    "dupatta": "heavily embroidered dupatta draped on head"},
    "shaadi":      {"weight": "heavy",  "colors": "bridal red, maroon, deep pink, gold",                           "fabric": "pure silk, velvet",     "embroidery": "maximum embellishments, heavy zardozi, gota","silhouette": "bridal lehenga or sharara",                   "dupatta": "full bridal dupatta draped on head with embroidery"},
    "wedding":     {"weight": "heavy",  "colors": "bridal red, maroon, deep pink, gold",                           "fabric": "pure silk, velvet",     "embroidery": "maximum embellishments, heavy zardozi, gota","silhouette": "bridal lehenga or sharara",                   "dupatta": "full bridal dupatta draped on head"},
    "barat":       {"weight": "heavy",  "colors": "deep red, maroon, crimson with gold",                           "fabric": "pure silk, velvet, jamawar", "embroidery": "maximum zardozi, heavy gold work, full embellishment", "silhouette": "full bridal lehenga with blouse and sharara", "dupatta": "heavy bridal dupatta with gold border draped on head"},
    "valima":      {"weight": "heavy",  "colors": "ivory, white, gold, pastel pink, mint",                         "fabric": "silk, chiffon, organza","embroidery": "heavy embroidery, sequins, pearl work",     "silhouette": "elegant lehenga or formal gharara",            "dupatta": "embellished dupatta"},
    "formal":      {"weight": "heavy",  "colors": "jewel tones, black, navy, emerald, deep purple",                "fabric": "velvet, silk, brocade", "embroidery": "heavy formal embellishments, zari, sequins", "silhouette": "formal maxi or lehenga",                      "dupatta": "heavily embellished formal dupatta"},
}

def detect_event(text: str) -> dict:
    text_lower = text.lower()
    for key, rules in EVENT_RULES.items():
        if key in text_lower:
            return {"event": key, **rules}
    return {
        "event": "general", "weight": "medium",
        "colors": "jewel tones, pastels",
        "fabric": "chiffon, silk",
        "embroidery": "moderate embroidery",
        "silhouette": "elegant kameez or lehenga",
        "dupatta": "embellished dupatta"
    }

def extract_user_details(user_prompt: str) -> dict:
    text = user_prompt.lower()
    details = {}

    colors = [
        "red","maroon","crimson","pink","blush","rose","fuchsia","orange","peach",
        "coral","yellow","gold","golden","green","emerald","mint","olive","teal",
        "blue","navy","purple","violet","lavender","white","ivory","cream","black",
        "grey","silver","brown","beige","nude","laal","gulabi","neela","sabz",
        "ferozi","jamni","asmani","peelay","safed"
    ]
    found_colors = [c for c in colors if c in text]
    if found_colors:
        details["user_colors"] = ", ".join(found_colors)

    fabrics = [
        "silk","chiffon","lawn","cotton","velvet","net","organza","georgette",
        "jamawar","brocade","lace","satin","tissue","khaddar","linen","crepe",
        "raw silk","banarsi"
    ]
    found_fabrics = [f for f in fabrics if f in text]
    if found_fabrics:
        details["user_fabric"] = ", ".join(found_fabrics)

    embellishments = [
        "gota","dabka","zari","zardozi","sequins","pearls","crystals","beads",
        "mirror work","thread work","embroidery","sitara","lace","resham","stone work"
    ]
    found_emb = [e for e in embellishments if e in text]
    if found_emb:
        details["user_embellishments"] = ", ".join(found_emb)

    styles = {
        "lehenga":"lehenga choli with flared skirt",
        "sharara":"sharara with wide flared pants",
        "gharara":"gharara with knee-length kameez",
        "anarkali":"anarkali frock",
        "maxi":"full length maxi dress",
        "trail":"outfit with long dramatic trail",
        "jacket":"kameez with embellished jacket",
        "cape":"outfit with attached cape",
        "straight":"straight cut kameez",
        "peplum":"peplum style kameez",
    }
    for s, desc in styles.items():
        if s in text:
            details["user_style"] = desc
            break

    sleeves = {
        "sleeveless":"sleeveless",
        "short sleeve":"short sleeves",
        "half sleeve":"half sleeves",
        "full sleeve":"full length sleeves",
        "bell sleeve":"bell sleeves",
        "off shoulder":"off-shoulder",
    }
    for s, desc in sleeves.items():
        if s in text:
            details["user_sleeve"] = desc
            break

    necklines = {
        "v neck":"V-neckline","v-neck":"V-neckline",
        "round neck":"round neckline","boat neck":"boat neckline",
        "square neck":"square neckline","sweetheart":"sweetheart neckline",
    }
    for n, desc in necklines.items():
        if n in text:
            details["user_neckline"] = desc
            break

    return details


def build_prompt(user_prompt: str, event_info: dict,
                 has_fabric_img: bool, has_material_img: bool) -> str:
    e = event_info
    ud = extract_user_details(user_prompt)

    colors   = ud.get("user_colors",         e["colors"])
    fabric   = ud.get("user_fabric",         e["fabric"])
    emb      = ud.get("user_embellishments", e["embroidery"])
    style    = ud.get("user_style",          e["silhouette"])
    sleeve   = ud.get("user_sleeve",         "")
    neckline = ud.get("user_neckline",       "")

    prompt  = f"A stunning Pakistani {style} for {e['event']} occasion. "
    prompt += f"Crafted in {fabric} fabric in {colors} color. "
    if neckline:
        prompt += f"Features a {neckline}. "
    if sleeve:
        prompt += f"With {sleeve}. "
    prompt += f"Adorned with {emb}. {e['dupatta']}. "
    prompt += f"Specific design request: {user_prompt}. "

    # Add fabric image note
    if has_fabric_img:
        prompt += "The fabric texture and color from the provided swatch is used as the main material. "

    # Add material note
    if has_material_img:
        prompt += "Special embellishment materials from provided images are incorporated in the design. "

    # Weight-based finishing touches
    weight = e["weight"]
    if weight == "light":
        prompt += (
            "The outfit is elegant yet comfortable, perfect for daytime wear. "
            "Simple, clean lines with graceful draping. "
        )
    elif weight == "medium":
        prompt += (
            "Semi-formal festive look with tasteful embellishments. "
            "Balanced between comfort and elegance. "
        )
    else:  # heavy
        prompt += (
            "Full bridal/formal look with maximum embellishments. "
            "Intricate handwork, rich fabric, complete jewelry set with "
            "maang tikka, jhumkas, choker necklace, and bangles. "
        )

    # Photography style
    prompt += (
        "Professional Pakistani model wearing the outfit. "
        "Soft studio lighting with elegant background. "
        "Full body shot showing complete outfit and dupatta draping. "
        "Vogue Pakistan fashion editorial style. "
        "Photorealistic, 8K resolution, sharp details, professional fashion photography."
    )

    return prompt


def load_image_as_part(path: str):
    try:
        from google import genai
        from google.genai import types
        p = pathlib.Path(path.strip().strip('"'))
        if not p.exists():
            return None
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".webp": "image/webp"}
        mime = mime_map.get(p.suffix.lower(), "image/jpeg")
        return types.Part.from_bytes(data=p.read_bytes(), mime_type=mime)
    except:
        return None


def enhance_with_groq(base_prompt: str, user_prompt: str, event_info: dict) -> str:
    """Use Groq (Llama) to enhance the fashion prompt."""
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)

        system_msg = """You are an expert Pakistani fashion designer and AI image prompt engineer.
Your job is to take a base fashion prompt and make it ultra-detailed and vivid for image generation.
Keep the event dress code rules strictly:
- Light events (Eid, casual): simple, comfortable, minimal embroidery
- Medium events (Mehndi, dawat, birthday): semi-formal, moderate embellishments
- Heavy events (Barat, Nikkah, Shaadi, Valima): maximum embellishments, rich fabric

Output ONLY the enhanced prompt. No explanations. No bullet points. Just one detailed paragraph."""

        user_msg = f"""Base prompt: {base_prompt}

User original request: {user_prompt}
Event: {event_info['event']} (Dress level: {event_info['weight']})

Enhance this into an ultra-detailed, vivid image generation prompt.
Make it more specific about: fabric texture, embroidery details, color shades, 
model pose, jewelry, background, lighting. 
End with: photorealistic, 8K, Vogue Pakistan editorial, professional fashion photography."""

        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg}
            ],
            max_tokens=500,
            temperature=0.7
        )
        enhanced = response.choices[0].message.content.strip()
        return enhanced

    except Exception as e:
        print(f"  [!] Groq error: {e}")
        print("  Base prompt use ho raha hai...")
        return base_prompt


def generate_image_stability(prompt: str, output_path: str) -> bool:
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {STABILITY_API_KEY}"
    }
    payload = {
        "prompt": prompt,
        "output_format": "jpeg",
        "aspect_ratio": "2:3",
    }
    print("  Stability AI se image generate ho rahi hai...")
    print("  (30-60 seconds lag sakte hain...)\n")
    try:
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers=headers,
            files={"none": ""},
            data=payload,
            timeout=90
        )
        response.raise_for_status()
        pathlib.Path(output_path).write_bytes(response.content)
        return True
    except requests.exceptions.HTTPError as e:
        print(f"  [!] Stability AI error: {e}")
        print(f"  Response: {response.text[:300]}")
        return False
    except Exception as e:
        print(f"  [!] Error: {e}")
        return False


def get_image_paths(image_type: str) -> list:
    paths = []
    print(f"  {image_type} images upload karo.")
    print(f"  (Seedha path daalo, Enter se skip, 'done' se finish)\n")
    while True:
        p = input(f"  Path {len(paths)+1} (ya Enter skip): ").strip().strip('"')
        if p.lower() in ("", "done", "skip"):
            break
        if pathlib.Path(p).exists():
            paths.append(p)
            print(f"  [OK] Loaded: {pathlib.Path(p).name}")
        else:
            print(f"  [!] File nahi mila, dobara try karo.")
    return paths


def banner():
    print()
    print("  +=======================================================+")
    print("  |       ** GLAMOURBOT - AI FASHION DESIGNER **          |")
    print("  |       Pakistani Fashion, Powered by Stability AI      |")
    print("  +=======================================================+")
    print()


def divider(label=""):
    if label:
        print(f"\n  ===== {label} =====\n")
    else:
        print("  " + "-" * 51)


def main():
    banner()

    if STABILITY_API_KEY == "YOUR_STABILITY_KEY_HERE":
        print("  [X] STABILITY_API_KEY set nahi!")
        print("  Key yahan se lo: https://platform.stability.ai/account/keys")
        sys.exit(1)

    if GROQ_API_KEY == "YOUR_GROQ_KEY_HERE":
        print("  [X] GROQ_API_KEY set nahi!")
        print("  Key yahan se lo: https://console.groq.com/keys")
        sys.exit(1)

    # Step 1: User Prompt
    divider("AAPKA DESIGN IDEA")
    print("  Jo chahiye likho - event ka naam zaroor likho!")
    print("  Examples:")
    print("    - eid ke liye light pink lawn dress")
    print("    - barat ke liye heavy red bridal lehenga")
    print("    - mehndi ke liye yellow sharara")
    print("    - casual outing ke liye simple outfit")
    print()
    user_prompt = input("  Aapka idea: ").strip()
    if not user_prompt:
        user_prompt = "eid ke liye khubsurat outfit"

    # Detect event
    event_info = detect_event(user_prompt)
    print(f"\n  [OK] Event: {event_info['event'].upper()}")
    print(f"  [OK] Dress level: {event_info['weight'].upper()}")
    print(f"  [OK] Colors: {event_info['colors']}")

    # Step 2: Fabric Images
    divider("FABRIC IMAGE (Optional)")
    fabric_paths = get_image_paths("Fabric/Kaprey ki")

    # Step 3: Material Images
    divider("MATERIAL IMAGE (Optional)")
    material_paths = get_image_paths("Material/Embellishment ki")

    # Step 4: Enhance prompt with Groq
    divider("PROMPT ENHANCEMENT")
    print("  Groq AI se prompt enhance ho raha hai...\n")

    base_prompt = build_prompt(
        user_prompt, event_info,
        has_fabric_img=len(fabric_paths) > 0,
        has_material_img=len(material_paths) > 0
    )
    prompt = enhance_with_groq(base_prompt, user_prompt, event_info)
    print("  [OK] Prompt ready!\n")

    # Step 5: Generate image
    divider("IMAGE GENERATION")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"glamour_{event_info['event']}_{ts}.jpeg"
    script_dir = pathlib.Path(__file__).parent
    out_path = str(script_dir / out_file)

    success = generate_image_stability(prompt, out_path)

    if success:
        print(f"  [OK] Image saved: {out_file}")
        print(f"  Folder: {script_dir}")
        try:
            if sys.platform == "win32":
                os.startfile(out_path)
        except:
            pass
    else:
        print("  [!] Image generate nahi hui.")
        print("  Stability key check karo: https://platform.stability.ai/account/keys")

    divider()
    print("\n  ** Shukriya GlamourBot use karne ka! **\n")


if __name__ == "__main__":
    main()