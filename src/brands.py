import os
import json
import time
import threading
import sqlite3
import requests
import re
from datetime import datetime
from typing import Optional

# Groq — optional, only used if GROQ_API_KEY is set
try:
    from groq import Groq as _Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _Groq = None
    _GROQ_AVAILABLE = False

GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL    = "llama-3.3-70b-versatile"
GROQ_FALLBACK = "llama3-8b-8192"

def _get_groq_client():
    if _GROQ_AVAILABLE and GROQ_API_KEY:
        return _Groq(api_key=GROQ_API_KEY)
    return None

def _call_groq(system_prompt: str, user_prompt: str, max_tokens: int = 600) -> str:
    """
    Call Groq API with automatic model fallback.
    Returns empty string if Groq is unavailable or fails.
    """
    client = _get_groq_client()
    if not client:
        return ""
    for model in [GROQ_MODEL, GROQ_FALLBACK]:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if "rate" in str(e).lower() or "429" in str(e):
                continue   # try fallback model
            print(f"[Groq Error] {model}: {e}")
            return ""
    return ""


def _groq_system_prompt(language: str) -> str:
    """Build language-aware system prompt for Groq."""
    if language == "roman_urdu":
        return """Aap GlamourBot hain — ek Pakistani fashion stylist AI.

Aap ka kaam:
- Jo products diye gaye hain unhe friendly, natural tarike se present karein
- HAMESHA Roman Urdu mein jawab dein — jaise ek dost baat karta hai

Rules:
- Koi markdown nahi (koi ** ya ### nahi) — sirf plain text
- Short intro (1-2 lines max) — zyada salutation nahi, seedha kaam ki baat
- "Assalam o alaikum" ya "Hope you are doing great" jaisi baatein BILKUL MAT KARO
- Har product ek line mein: number, brand, title, price
- Akhir mein ek practical styling tip
- Sale ho to zaroor mention karein
- Specific color manga ho to confirm karein

Tip format: Tip: [Roman Urdu mein practical advice]"""

    return """You are GlamourBot — a Pakistani fashion stylist AI.

Your job:
- Present the given products in a natural, friendly way
- ALWAYS respond in English

Rules:
- No markdown (no ** or ###) — plain text only
- Short intro (1-2 lines max) — no over-the-top greetings, get to the point
- NEVER say "I am excited to help" or "I hope you are doing great"
- Each product on one line: number, brand, title, price
- End with one practical styling tip
- Mention sale if applicable
- Confirm color match if user asked for specific color

Tip format: Tip: [practical English advice]"""


def _groq_user_prompt(user_message: str, products: list, result: dict) -> str:
    """Build the product context prompt for Groq."""
    event    = result.get("event", "general")
    gender   = result.get("gender", "women")
    color    = result.get("detected_color") or "not specified"
    fabric   = result.get("detected_fabric") or "not specified"
    category = result.get("category", "clothing")

    lines = []
    for i, p in enumerate(products[:6], 1):
        name     = p.get("brand_name") or p.get("brand_id", "")
        logo     = p.get("brand_logo", "")
        title    = p.get("title", "")
        price    = p.get("price", 0)
        on_sale  = p.get("on_sale", False)
        url      = p.get("product_url", "")
        p_color  = p.get("color", "")
        p_fabric = p.get("fabric", "")

        price_str = f"PKR {int(price):,}" if price > 0 else "See website"
        sale_str  = " [ON SALE]" if on_sale else ""
        title_str = f" — {title}" if title else ""
        meta      = " | ".join(filter(None, [
            f"Color: {p_color}" if p_color else "",
            f"Fabric: {p_fabric}" if p_fabric else "",
        ]))
        lines.append(
            f"{i}. {logo} {name}{title_str} | {price_str}{sale_str}"
            + (f" | {meta}" if meta else "")
            + f" | {url}"
        )

    products_text = "\n".join(lines) if lines else "No products found."

    return (
        f"User query: \"{user_message}\"\n"
        f"Context: event={event}, gender={gender}, color={color}, "
        f"fabric={fabric}, category={category}\n\n"
        f"Products to present:\n{products_text}\n\n"
        f"Write a natural stylist response presenting these products. "
        f"Include product names and prices. End with a styling tip."
    )

# ══════════════════════════════════════════════════════════════
# BRANDS REGISTRY
# is_shopify=True  -> /products.json se real data fetch hota hai
# is_shopify=False -> fallback brand suggestion only
# ══════════════════════════════════════════════════════════════
BRANDS_REGISTRY = [

    # ── WOMEN (6) ──
    {
        "id": "gulahmed", "name": "Gul Ahmed", "logo": "🌺",
        "gender": ["women"], "category": ["clothing"],
        "rating": 4.3, "is_shopify": True, "domain": "www.gulahmedshop.com",
        "sale_months": [3, 4, 6, 9, 10, 12],
        "speciality": ["lawn", "eid", "casual", "formal", "winter"],
        "nav_urls": {
            "women": "https://www.gulahmedshop.com/collections/women",
            "sale":  "https://www.gulahmedshop.com/sale",
        },
        "fetch_url": "https://www.gulahmedshop.com/products.json",
        "gender_filter": "women",
    },
    {
        "id": "mariab", "name": "Maria B", "logo": "👑",
        "gender": ["women"], "category": ["clothing", "jewelry", "bags"],
        "rating": 4.8, "is_shopify": True, "domain": "www.mariab.pk",
        "sale_months": [1, 6, 7, 12],
        "speciality": ["bridal", "wedding", "luxury", "mehndi", "walima"],
        "nav_urls": {
            "women":   "https://www.mariab.pk/collections/new-arrivals",
            "bridal":  "https://www.mariab.pk/collections/bridals",
            "jewelry": "https://www.mariab.pk/collections/jewelry",
            "bags":    "https://www.mariab.pk/collections/bags",
            "sale":    "https://www.mariab.pk/pages/sale-view-all",
        },
        "fetch_url": "https://www.mariab.pk/products.json",
        "gender_filter": "women",
    },
    {
        "id": "sanasafinaz", "name": "Sana Safinaz", "logo": "✨",
        "gender": ["women"], "category": ["clothing"],
        "rating": 4.6, "is_shopify": True, "domain": "sanasafinaz.com",
        "sale_months": [2, 6, 8, 11],
        "speciality": ["luxury", "lawn", "formal", "wedding"],
        "nav_urls": {
            "women": "https://sanasafinaz.com/collections/ready-to-wear",
            "sale":  "https://sanasafinaz.com/collections/sale",
        },
        "fetch_url": "https://sanasafinaz.com/products.json",
        "gender_filter": "women",
    },
    {
        "id": "alkaram", "name": "Alkaram Studio", "logo": "🎨",
        "gender": ["women"], "category": ["clothing"],
        "rating": 4.2, "is_shopify": True, "domain": "www.alkaramstudio.com",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["lawn", "casual", "pret", "eid", "winter"],
        "nav_urls": {
            "women": "https://www.alkaramstudio.com/collections/pret",
            "sale":  "https://www.alkaramstudio.com/collections/sale",
        },
        "fetch_url": "https://www.alkaramstudio.com/products.json",
        "gender_filter": "women",
    },
    {
        "id": "khaadi", "name": "Khaadi", "logo": "🌿",
        "gender": ["women"], "category": ["clothing", "bags"],
        "rating": 4.4, "is_shopify": False, "domain": "pk.khaadi.com",
        "sale_months": [3, 4, 6, 9, 10, 12],
        "speciality": ["lawn", "eid", "casual", "pret", "festive", "winter"],
        "nav_urls": {
            "women": "https://pk.khaadi.com/ready-to-wear.html",
            "sale":  "https://pk.khaadi.com/sale.html",
        },
    },
    {
        "id": "nomiansari", "name": "Nomi Ansari", "logo": "🌸",
        "gender": ["women"], "category": ["clothing"],
        "rating": 4.7, "is_shopify": False, "domain": "nomiansari.com",
        "sale_months": [1, 7],
        "speciality": ["bridal", "couture", "mehndi", "wedding", "party"],
        "nav_urls": {"women": "https://nomiansari.com"},
    },
    {
        "id": "hsy", "name": "HSY", "logo": "💎",
        "gender": ["women"], "category": ["clothing"],
        "rating": 4.9, "is_shopify": False, "domain": "hsy.com.pk",
        "sale_months": [1, 8],
        "speciality": ["bridal", "couture", "luxury", "wedding", "barat"],
        "nav_urls": {"women": "https://hsy.com.pk", "bridal": "https://hsy.com.pk"},
    },

    # ── MEN (6) ──
    {
        "id": "bonanza", "name": "Bonanza Satrangi", "logo": "🎪",
        "gender": ["men"], "category": ["clothing"],
        "rating": 4.3, "is_shopify": True, "domain": "www.bonanzasatrangi.com",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["men kurta", "shalwar kameez", "eid", "casual", "festive"],
        "nav_urls": {"men": "https://www.bonanzasatrangi.com/collections/mens"},
        "fetch_url": "https://www.bonanzasatrangi.com/products.json",
        "gender_filter": "men",
    },
    {
        "id": "edenrobe", "name": "Edenrobe", "logo": "🌿",
        "gender": ["men"], "category": ["clothing"],
        "rating": 4.2, "is_shopify": True, "domain": "www.edenrobe.com",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["men kurta", "shalwar kameez", "eid", "casual", "formal"],
        "nav_urls": {"men": "https://www.edenrobe.com/collections/mens"},
        "fetch_url": "https://www.edenrobe.com/products.json",
        "gender_filter": "men",
    },
    {
        "id": "sapphire_men", "name": "Sapphire Men", "logo": "💙",
        "gender": ["men"], "category": ["clothing"],
        "rating": 4.5, "is_shopify": False, "domain": "pk.sapphireonline.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["men kurta", "eid", "casual", "pret", "formal"],
        "nav_urls": {"men": "https://pk.sapphireonline.pk/collections/man"},
    },
    {
        "id": "cambridge", "name": "Cambridge", "logo": "🎓",
        "gender": ["men"], "category": ["clothing"],
        "rating": 4.4, "is_shopify": True, "domain": "www.cambridge.com.pk",
        "sale_months": [6, 12],
        "speciality": ["formal", "western", "shirts", "trousers", "suits"],
        "nav_urls": {"men": "https://www.cambridge.com.pk/collections/all"},
        "fetch_url": "https://cambridge-shop.myshopify.com/products.json",
        "gender_filter": "men",
    },
    {
        "id": "charcoal", "name": "Charcoal", "logo": "🖤",
        "gender": ["men"], "category": ["clothing"],
        "rating": 4.3, "is_shopify": True, "domain": "www.charcoal.com.pk",
        "sale_months": [6, 12],
        "speciality": ["formal", "western", "casual", "shirts", "modern"],
        "nav_urls": {"men": "https://www.charcoal.com.pk/collections/all"},
        "fetch_url": "https://www.charcoal.com.pk/products.json",
        "gender_filter": "men",
    },
    {
        "id": "junaidjamshed", "name": "J. (Junaid Jamshed)", "logo": "👔",
        "gender": ["men"], "category": ["clothing"],
        "rating": 4.4, "is_shopify": False, "domain": "jdot.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["men kurta", "shalwar kameez", "eid", "casual", "formal"],
        "nav_urls": {"men": "https://www.jdot.pk/men"},
    },

    # ── KIDS (6) ──
    {
        "id": "mariab_kids", "name": "Maria B Kids", "logo": "👧",
        "gender": ["kids"], "category": ["clothing"],
        "rating": 4.8, "is_shopify": True, "domain": "www.mariab.pk",
        "sale_months": [1, 6, 7, 12],
        "speciality": ["eid kids", "festive", "casual", "formal"],
        "nav_urls": {"kids": "https://www.mariab.pk/collections/view-all-kids"},
        "fetch_url": "https://www.mariab.pk/collections/view-all-kids/products.json",
        "gender_filter": "kids",
    },
    {
        "id": "alkaram_kids", "name": "Alkaram Kids", "logo": "🎨",
        "gender": ["kids"], "category": ["clothing"],
        "rating": 4.2, "is_shopify": True, "domain": "www.alkaramstudio.com",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["eid kids", "casual", "festive"],
        "nav_urls": {"kids": "https://www.alkaramstudio.com/collections/kids"},
        "fetch_url": "https://www.alkaramstudio.com/collections/kids/products.json",
        "gender_filter": "kids",
    },
    {
        "id": "bonanza_kids", "name": "Bonanza Kids", "logo": "🎪",
        "gender": ["kids"], "category": ["clothing"],
        "rating": 4.3, "is_shopify": True, "domain": "www.bonanzasatrangi.com",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["eid kids", "casual", "festive"],
        "nav_urls": {"kids": "https://www.bonanzasatrangi.com/collections/kids"},
        "fetch_url": "https://www.bonanzasatrangi.com/collections/kids/products.json",
        "gender_filter": "kids",
    },
    {
        "id": "sapphire_kids", "name": "Sapphire Kids", "logo": "💙",
        "gender": ["kids"], "category": ["clothing"],
        "rating": 4.5, "is_shopify": False, "domain": "pk.sapphireonline.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["eid kids", "casual", "festive"],
        "nav_urls": {"kids": "https://pk.sapphireonline.pk/collections/kids"},
    },
    {
        "id": "babyhaven", "name": "Baby Haven", "logo": "👶",
        "gender": ["kids"], "category": ["clothing"],
        "rating": 4.2, "is_shopify": False, "domain": "babyhavenpk.com",
        "sale_months": [3, 9],
        "speciality": ["baby clothes", "toddler", "kids casual", "eid kids"],
        "nav_urls": {"kids": "https://www.babyhavenpk.com"},
    },
    {
        "id": "ethnicbypfl", "name": "Ethnic by Outfitters", "logo": "🏵️",
        "gender": ["kids"], "category": ["clothing"],
        "rating": 4.1, "is_shopify": False, "domain": "ethnicbyoutfitters.com",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["casual", "eid kids", "pret", "everyday"],
        "nav_urls": {"kids": "https://www.ethnicbyoutfitters.com/collections/kids"},
    },

    # ── SHOES (6) ──
    {
        "id": "stylo", "name": "Stylo Shoes", "logo": "👠",
        "gender": ["women", "men", "kids"], "category": ["shoes"],
        "rating": 4.3, "is_shopify": False, "domain": "stylo.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["heels", "flats", "formal shoes", "casual shoes", "bridal shoes"],
        "nav_urls": {
            "women": "https://www.stylo.pk/collections/women",
            "men":   "https://www.stylo.pk/collections/men",
            "kids":  "https://www.stylo.pk/collections/kids",
        },
    },
    {
        "id": "bata", "name": "Bata Pakistan", "logo": "👟",
        "gender": ["women", "men", "kids"], "category": ["shoes"],
        "rating": 4.0, "is_shopify": False, "domain": "bata.com.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["casual shoes", "formal shoes", "everyday wear", "kids shoes"],
        "nav_urls": {
            "women": "https://www.bata.com.pk/collections/women",
            "men":   "https://www.bata.com.pk/collections/men",
            "kids":  "https://www.bata.com.pk/collections/kids",
        },
    },
    {
        "id": "borjan", "name": "Borjan Shoes", "logo": "👡",
        "gender": ["women", "men"], "category": ["shoes"],
        "rating": 4.2, "is_shopify": False, "domain": "borjan.com.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["heels", "formal shoes", "bridal shoes", "casual shoes"],
        "nav_urls": {
            "women": "https://www.borjan.com.pk/collections/women",
            "men":   "https://www.borjan.com.pk/collections/men",
        },
    },
    {
        "id": "servis", "name": "Servis Shoes", "logo": "🥿",
        "gender": ["women", "men", "kids"], "category": ["shoes"],
        "rating": 4.0, "is_shopify": False, "domain": "servis.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["casual shoes", "formal shoes", "everyday wear", "kids shoes"],
        "nav_urls": {
            "women": "https://www.servis.pk/collections/women",
            "men":   "https://www.servis.pk/collections/men",
        },
    },
    {
        "id": "insignia", "name": "Insignia", "logo": "✨",
        "gender": ["women"], "category": ["shoes"],
        "rating": 4.4, "is_shopify": False, "domain": "insignia.com.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["heels", "bridal shoes", "formal shoes", "clutch"],
        "nav_urls": {"women": "https://www.insignia.com.pk/collections/footwear"},
    },
    {
        "id": "metro", "name": "Metro Shoes", "logo": "👞",
        "gender": ["women", "men", "kids"], "category": ["shoes"],
        "rating": 4.1, "is_shopify": False, "domain": "metroshoes.net",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["casual shoes", "formal shoes", "bridal shoes", "kids shoes"],
        "nav_urls": {
            "women": "https://www.metroshoes.net/collections/women",
            "men":   "https://www.metroshoes.net/collections/men",
        },
    },

    # ── JEWELRY (6) ──
    {
        "id": "mariab_jewelry", "name": "Maria B Jewelry", "logo": "💍",
        "gender": ["women"], "category": ["jewelry"],
        "rating": 4.8, "is_shopify": True, "domain": "www.mariab.pk",
        "sale_months": [1, 6, 7, 12],
        "speciality": ["wedding", "bridal", "mehndi", "party", "formal"],
        "nav_urls": {"jewelry": "https://www.mariab.pk/collections/jewelry"},
        "fetch_url": "https://www.mariab.pk/collections/jewelry/products.json",
        "gender_filter": "women",
        "category_override": "jewelry",
    },
    {
        "id": "aghasnoor", "name": "Agha Noor", "logo": "🌟",
        "gender": ["women"], "category": ["jewelry"],
        "rating": 4.5, "is_shopify": False, "domain": "aghasnoor.com",
        "sale_months": [1, 6, 12],
        "speciality": ["bridal", "wedding", "mehndi", "party", "jewelry"],
        "nav_urls": {"jewelry": "https://www.aghasnoor.com/collections/jewelry"},
    },
    {
        "id": "thelabelstudio", "name": "The Label Studio", "logo": "🏷️",
        "gender": ["women"], "category": ["jewelry"],
        "rating": 4.3, "is_shopify": False, "domain": "thelabelstudio.pk",
        "sale_months": [6, 12],
        "speciality": ["jewelry", "party", "formal"],
        "nav_urls": {"jewelry": "https://www.thelabelstudio.pk/collections/jewelry"},
    },
    {
        "id": "gulahmed_jewelry", "name": "Gul Ahmed Jewelry", "logo": "🌺",
        "gender": ["women"], "category": ["jewelry"],
        "rating": 4.3, "is_shopify": True, "domain": "www.gulahmedshop.com",
        "sale_months": [3, 4, 6, 9, 10, 12],
        "speciality": ["jewelry", "casual", "formal", "eid"],
        "nav_urls": {"jewelry": "https://www.gulahmedshop.com/collections/accessories-jewelry"},
        "fetch_url": "https://www.gulahmedshop.com/collections/accessories-jewelry/products.json",
        "fetch_delay": 3,
        "gender_filter": "women",
        "category_override": "jewelry",
    },
    {
        "id": "zarqjewels", "name": "Zarq Jewels", "logo": "💎",
        "gender": ["women"], "category": ["jewelry"],
        "rating": 4.4, "is_shopify": False, "domain": "zarqjewels.com",
        "sale_months": [6, 12],
        "speciality": ["bridal", "wedding", "mehndi", "party"],
        "nav_urls": {"jewelry": "https://www.zarqjewels.com"},
    },
    {
        "id": "hsy_jewelry", "name": "HSY Jewelry", "logo": "💎",
        "gender": ["women"], "category": ["jewelry"],
        "rating": 4.9, "is_shopify": False, "domain": "hsy.com.pk",
        "sale_months": [1, 8],
        "speciality": ["bridal", "couture", "luxury", "wedding"],
        "nav_urls": {"jewelry": "https://hsy.com.pk"},
    },

    # ── BAGS (6) ──
    {
        "id": "mariab_bags", "name": "Maria B Bags", "logo": "👜",
        "gender": ["women"], "category": ["bags"],
        "rating": 4.8, "is_shopify": True, "domain": "www.mariab.pk",
        "sale_months": [1, 6, 7, 12],
        "speciality": ["clutch", "handbag", "wedding", "formal", "party"],
        "nav_urls": {"bags": "https://www.mariab.pk/collections/bags"},
        "fetch_url": "https://www.mariab.pk/collections/bags/products.json",
        "fetch_delay": 3,
        "gender_filter": "women",
        "category_override": "bags",
    },
    {
        "id": "gulahmed_bags", "name": "Gul Ahmed Bags", "logo": "🌺",
        "gender": ["women"], "category": ["bags"],
        "rating": 4.3, "is_shopify": True, "domain": "www.gulahmedshop.com",
        "sale_months": [3, 4, 6, 9, 10, 12],
        "speciality": ["tote", "handbag", "casual", "everyday"],
        "nav_urls": {"bags": "https://www.gulahmedshop.com/collections/accessories-tote-bags"},
        "fetch_url": "https://www.gulahmedshop.com/collections/accessories-tote-bags/products.json",
        "fetch_delay": 3,
        "gender_filter": "women",
        "category_override": "bags",
    },
    {
        "id": "insignia_bags", "name": "Insignia Bags", "logo": "✨",
        "gender": ["women"], "category": ["bags"],
        "rating": 4.4, "is_shopify": False, "domain": "insignia.com.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["clutch", "handbag", "formal", "party", "bridal"],
        "nav_urls": {"bags": "https://www.insignia.com.pk/collections/bags"},
    },
    {
        "id": "khaadi_bags", "name": "Khaadi Bags", "logo": "🌿",
        "gender": ["women"], "category": ["bags"],
        "rating": 4.5, "is_shopify": False, "domain": "pk.khaadi.com",
        "sale_months": [3, 4, 6, 9, 10],
        "speciality": ["tote", "handbag", "casual", "everyday"],
        "nav_urls": {"bags": "https://pk.khaadi.com/accessories.html"},
    },
    {
        "id": "sapphire_bags", "name": "Sapphire Bags", "logo": "💙",
        "gender": ["women"], "category": ["bags"],
        "rating": 4.5, "is_shopify": False, "domain": "pk.sapphireonline.pk",
        "sale_months": [3, 6, 9, 12],
        "speciality": ["handbag", "tote", "casual", "formal"],
        "nav_urls": {"bags": "https://pk.sapphireonline.pk/collections/bags"},
    },
    {
        "id": "thelabelstudio_bags", "name": "The Label Studio Bags", "logo": "🏷️",
        "gender": ["women"], "category": ["bags"],
        "rating": 4.3, "is_shopify": False, "domain": "thelabelstudio.pk",
        "sale_months": [6, 12],
        "speciality": ["handbag", "clutch", "formal", "party"],
        "nav_urls": {"bags": "https://www.thelabelstudio.pk/collections/bags"},
    },
]


# ══════════════════════════════════════════════════════════════
# COLOR SYSTEM
# Supports English + Roman Urdu + Urdu
# Each entry maps to a normalized English color name
# ══════════════════════════════════════════════════════════════

# All color keywords -> normalized English name
COLOR_KEYWORDS: dict[str, str] = {
    # ── English ──
    "red": "red", "crimson": "red", "scarlet": "red",
    "maroon": "maroon", "burgundy": "maroon", "wine": "maroon", "dark red": "maroon",
    "pink": "pink", "hot pink": "pink", "baby pink": "pink", "blush": "pink", "rose pink": "pink",
    "peach": "peach", "coral": "peach", "salmon": "peach",
    "orange": "orange", "rust": "orange", "burnt orange": "orange",
    "yellow": "yellow", "mustard": "yellow", "lemon": "yellow", "golden yellow": "yellow",
    "green": "green", "olive": "green", "sage": "green", "mint": "green", "bottle green": "green",
    "teal": "teal", "turquoise": "teal", "aqua": "teal",
    "blue": "blue", "sky blue": "blue", "royal blue": "blue", "cobalt": "blue", "powder blue": "blue",
    "navy": "navy", "navy blue": "navy", "dark blue": "navy", "midnight blue": "navy",
    "purple": "purple", "violet": "purple", "lavender": "purple", "lilac": "purple", "mauve": "purple",
    "black": "black", "jet black": "black", "charcoal black": "black",
    "white": "white", "off white": "white", "ivory": "white", "cream": "white", "off-white": "white",
    "grey": "grey", "gray": "grey", "silver": "grey", "charcoal": "grey",
    "brown": "brown", "chocolate": "brown", "caramel": "brown", "coffee": "brown",
    "beige": "beige", "nude": "beige", "tan": "beige", "skin": "beige",
    "gold": "gold", "antique gold": "gold", "golden": "gold",
    "multi": "multicolor", "multicolor": "multicolor", "multi color": "multicolor", "printed": "multicolor",

    # ── Roman Urdu ──
    "kala": "black", "kaala": "black", "kali": "black", "kaali": "black",
    "safed": "white", "sufaid": "white", "sufed": "white", "safaid": "white",
    "laal": "red", "lal": "red", "surkh": "red",
    "peela": "yellow", "pila": "yellow", "zard": "yellow", "peeli": "yellow",
    "hara": "green", "hari": "green", "sabz": "green",
    "neela": "blue", "nila": "blue", "neeli": "blue",
    "gulabi": "pink", "ghulaabi": "pink", "gulabi rang": "pink",
    "narangi": "orange", "narnji": "orange", "naranga": "orange",
    "jamni": "purple", "baingan": "purple", "arghwani": "purple",
    "asmani": "blue", "falai": "teal",
    "bhura": "brown", "khakhi": "beige", "khaki": "beige",
    "sunehra": "gold", "sona rang": "gold",
    "gehra laal": "maroon", "dark laal": "maroon",
    "rang birangi": "multicolor", "rangeen": "multicolor",
}

# CSS swatches for UI display
COLOR_SWATCHES: dict[str, str] = {
    "red":        "#dc2626",
    "maroon":     "#7f1d1d",
    "pink":       "#ec4899",
    "peach":      "#fb923c",
    "orange":     "#f97316",
    "yellow":     "#eab308",
    "green":      "#16a34a",
    "teal":       "#0d9488",
    "blue":       "#2563eb",
    "navy":       "#1e3a5f",
    "purple":     "#7c3aed",
    "black":      "#1e1b26",
    "white":      "#e5e7eb",
    "grey":       "#9ca3af",
    "brown":      "#92400e",
    "beige":      "#d4a96a",
    "gold":       "#ca8a04",
    "multicolor": "linear-gradient(135deg,#dc2626,#eab308,#16a34a,#2563eb)",
}


def detect_color(text: str) -> Optional[str]:
    """
    Detect color from user query.
    Handles English, Roman Urdu, and Urdu color names.
    Returns normalized English color name or None.
    """
    text = text.lower().strip()
    # Try multi-word phrases first (longest match wins)
    for phrase in sorted(COLOR_KEYWORDS.keys(), key=len, reverse=True):
        if phrase in text:
            return COLOR_KEYWORDS[phrase]
    return None


def get_color_swatch(color: str) -> str:
    """Return CSS color value for a normalized color name."""
    return COLOR_SWATCHES.get(color, "#888888")


def normalize_product_color(tags: list, title: str) -> str:
    """
    Detect color from Shopify product tags and title.
    Returns normalized English color name or 'multi'.
    """
    text = " ".join(tags) + " " + title.lower()
    # Check tags first (most accurate)
    for tag in tags:
        if tag in COLOR_KEYWORDS:
            return COLOR_KEYWORDS[tag]
    # Then full text
    detected = detect_color(text)
    return detected if detected else "multi"


# ══════════════════════════════════════════════════════════════
# FABRIC SYSTEM
# Maps fabric names to their best-suited events
# ══════════════════════════════════════════════════════════════

FABRIC_EVENT_MAP: dict[str, list] = {
    "lawn":       ["eid", "casual", "summer"],
    "cotton":     ["casual", "everyday", "eid"],
    "linen":      ["casual", "summer", "formal"],
    "chiffon":    ["party", "formal", "mehndi", "wedding"],
    "georgette":  ["party", "formal", "mehndi"],
    "organza":    ["wedding", "party", "formal"],
    "net":        ["wedding", "bridal", "party"],
    "silk":       ["wedding", "barat", "formal", "party"],
    "raw silk":   ["wedding", "barat", "formal"],
    "jamawar":    ["wedding", "barat", "formal"],
    "velvet":     ["wedding", "winter", "formal", "barat"],
    "khaddar":    ["winter", "casual"],
    "karandi":    ["winter", "casual"],
    "dobby":      ["eid", "casual"],
    "jacquard":   ["formal", "party", "wedding"],
    "cambric":    ["casual", "everyday"],
    "wool":       ["winter", "formal"],
    "crepe":      ["formal", "party"],
    "satin":      ["wedding", "party", "formal"],
    "tissue":     ["wedding", "party"],
    "banarsi":    ["wedding", "barat"],
}

ALL_FABRICS = list(FABRIC_EVENT_MAP.keys())


def detect_fabric(text: str) -> Optional[str]:
    """Detect fabric from text. Returns fabric name or None."""
    text = text.lower()
    # Longest match first
    for fabric in sorted(ALL_FABRICS, key=len, reverse=True):
        if fabric in text:
            return fabric
    return None


def extract_fabric_tags(tags: list, title: str) -> list:
    """Extract all matching fabrics from product tags and title."""
    text = " ".join(tags) + " " + title.lower()
    return [f for f in ALL_FABRICS if f in text]


# ══════════════════════════════════════════════════════════════
# EVENT SYSTEM
# Supports English + Roman Urdu keywords
# ══════════════════════════════════════════════════════════════

EVENT_KEYWORDS: dict[str, list] = {
    "wedding": [
        "wedding", "shadi", "shaadi", "bride", "bridal", "nikah", "nikkah",
        "valima", "walima", "dulhan", "barat", "baraat",
    ],
    "barat": [
        "barat", "baraat", "barat day", "barat function",
    ],
    "mehndi": [
        "mehndi", "mehendi", "henna", "mayoun", "mayun", "mehndi function",
    ],
    "eid": [
        "eid", "eid ul fitr", "eid ul adha", "eidi", "festive", "festival",
        "eid collection", "eid outfit",
    ],
    "party": [
        "party", "function", "dinner", "evening", "dawat", "dawaat",
        "gathering", "mehfil",
    ],
    "formal": [
        "formal", "office", "professional", "work", "meeting", "interview",
        "corporate",
    ],
    "casual": [
        "casual", "daily", "everyday", "ghar", "home", "simple", "rozmara",
        "routine",
    ],
    "winter": [
        "winter", "sardi", "cold", "season", "winters",
    ],
}


def detect_event(text: str) -> str:
    """
    Detect event from user query.
    Returns event name or 'general'.
    Barat is checked before wedding to avoid merge.
    """
    text = text.lower()
    # Check barat first (subset of wedding keywords — needs priority)
    if any(k in text for k in EVENT_KEYWORDS["barat"]):
        return "barat"
    for event, keywords in EVENT_KEYWORDS.items():
        if event == "barat":
            continue  # already checked
        if any(k in text for k in keywords):
            return event
    return "general"


# ══════════════════════════════════════════════════════════════
# GENDER SYSTEM
# Supports English + Roman Urdu
# ══════════════════════════════════════════════════════════════

GENDER_KEYWORDS: dict[str, list] = {
    "kids": [
        "kids", "child", "children", "baby", "toddler", "bacha", "bachi",
        "bachon", "bacche", "girls dress", "boys dress", "girls eid",
        "boys eid", "larki ka", "larka ka", "beti", "beta ke liye",
        "chota", "choti",
    ],
    "men": [
        " men ", " man ", " male ", "gents", "mard", "larke", "larkon",
        "bhai ke liye", "abbu ke liye", "husband ke liye",
        "sherwani", "mard ka", "mard ke liye",
        "larke ke liye", "men suit", "men kurta", "men shalwar",
        "larka", "boys kurta", "boys shalwar",
    ],
}


def detect_gender(text: str) -> str:
    """
    Detect gender from user query.
    Returns 'women', 'men', or 'kids'.
    Kids checked first, then men, women is default.
    """
    text = " " + text.lower() + " "   # pad for whole-word matching
    if any(k in text for k in GENDER_KEYWORDS["kids"]):
        return "kids"
    if any(k in text for k in GENDER_KEYWORDS["men"]):
        return "men"
    return "women"


# ══════════════════════════════════════════════════════════════
# CATEGORY DETECTION
# ══════════════════════════════════════════════════════════════

def detect_category(text: str) -> str:
    """Detect product category from user query. Returns category string."""
    text = text.lower()
    if any(k in text for k in [
        "shoes", "heels", "chappal", "sandal", "joota", "khussa",
        "footwear", "sandals", "slippers", "jutti",
    ]):
        return "shoes"
    if any(k in text for k in [
        "bag", "purse", "clutch", "handbag", "tote", "shoulder bag",
        "hand bag",
    ]):
        return "bags"
    if any(k in text for k in [
        "jewelry", "jewellery", "zewar", "necklace", "earring", "earrings",
        "bangles", "tikka", "jhumka", "haar", "mala", "choker", "ring",
        "bracelet",
    ]):
        return "jewelry"
    return "clothing"


# ══════════════════════════════════════════════════════════════
# LANGUAGE DETECTION
# Detect if user wrote in Roman Urdu / Urdu or English
# ══════════════════════════════════════════════════════════════

# These markers appear in Roman Urdu but NOT in normal English
ROMAN_URDU_MARKERS = [
    "ke liye", "chahiye", "kya hai", "wala", "wali", "walay",
    "mujhe", "mujhy", "acha", "bata do", "dikhao", "batao",
    "mard", "aurat", "bhai ke", "behn", "shadi", "mehndi", "eid ke", "barat ke",
    "kala", "laal", "peela", "hara", "neela", "gulabi", "safed",
    "kali", "kaala", "sufaid", "surkh", "zard",
    "kurta", "dupatta", "lehenga", "gharara", "shalwar",
    "bahut", "accha", "theek", "zaroor", "bohat",
]


# Strong single-word Urdu markers — even 1 is enough
STRONG_URDU_MARKERS = [
    # These words are ONLY used in Roman Urdu context — never in plain English
    "shadi", "barat", "dupatta", "shalwar", "kameez",
    "gharara", "kala", "laal", "gulabi", "peela", "neela",
    "safed", "mard", "chahiye", "ke liye", "wala", "wali",
    # Note: "mehndi", "kurta", "lehenga" removed — appear in English fashion queries too
]


def detect_language(text: str) -> str:
    """
    Returns 'roman_urdu' if user message appears to be Roman Urdu/Urdu,
    otherwise returns 'english'.
    - 1 strong Urdu marker is enough
    - OR 2+ general markers
    """
    text_lower = text.lower()
    if any(m in text_lower for m in STRONG_URDU_MARKERS):
        return "roman_urdu"
    urdu_score = sum(1 for marker in ROMAN_URDU_MARKERS if marker in text_lower)
    return "roman_urdu" if urdu_score >= 2 else "english"


# ══════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════

class BrandDB:
    def __init__(self, db_path: str = None):
        if db_path is None:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base, "brands_cache.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS brand_products (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand_id        TEXT,
                    brand_name      TEXT,
                    brand_logo      TEXT,
                    title           TEXT,
                    price           REAL,
                    compare_price   REAL,
                    color           TEXT,
                    gender          TEXT,
                    category        TEXT,
                    event_tags      TEXT,
                    fabric          TEXT,
                    fabric_tags     TEXT,
                    image_url       TEXT,
                    product_url     TEXT,
                    on_sale         INTEGER DEFAULT 0,
                    rating          REAL,
                    source          TEXT DEFAULT 'shopify',
                    last_updated    TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS brand_sync_log (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand_id         TEXT,
                    sync_time        TEXT,
                    status           TEXT,
                    products_fetched INTEGER DEFAULT 0,
                    error_msg        TEXT
                )
            """)
            # Safe column additions for existing databases
            for col, typedef in [
                ("brand_logo",    "TEXT"),
                ("compare_price", "REAL"),
                ("fabric",        "TEXT"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE brand_products ADD COLUMN {col} {typedef}")
                except Exception:
                    pass
            conn.commit()

    def upsert_products(self, brand_id: str, products: list):
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM brand_products WHERE brand_id = ?", (brand_id,))
            for p in products:
                conn.execute("""
                    INSERT INTO brand_products
                    (brand_id, brand_name, brand_logo, title, price, compare_price,
                     color, gender, category, event_tags, fabric, fabric_tags,
                     image_url, product_url, on_sale, rating, source, last_updated)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    brand_id,
                    p.get("brand_name", ""),
                    p.get("brand_logo", ""),
                    p.get("title", ""),
                    p.get("price", 0),
                    p.get("compare_price", 0),
                    p.get("color", ""),
                    p.get("gender", "women"),
                    p.get("category", "clothing"),
                    json.dumps(p.get("event_tags", [])),
                    p.get("fabric", ""),
                    json.dumps(p.get("fabric_tags", [])),
                    p.get("image_url", ""),
                    p.get("product_url", ""),
                    1 if p.get("on_sale") else 0,
                    p.get("rating", 4.0),
                    p.get("source", "shopify"),
                    now,
                ))
            conn.commit()

    def log_sync(self, brand_id: str, status: str, count: int, error: str = ""):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO brand_sync_log "
                "(brand_id, sync_time, status, products_fetched, error_msg) "
                "VALUES (?,?,?,?,?)",
                (brand_id, datetime.now().isoformat(), status, count, error),
            )
            conn.commit()

    def get_products(self, filters: dict = None) -> list:
        query = "SELECT * FROM brand_products WHERE 1=1"
        params = []
        if filters:
            if filters.get("gender"):
                query += " AND gender = ?"
                params.append(filters["gender"])
            if filters.get("category"):
                query += " AND category = ?"
                params.append(filters["category"])
            if filters.get("brand_id"):
                query += " AND brand_id = ?"
                params.append(filters["brand_id"])
            if filters.get("color"):
                query += " AND color = ?"
                params.append(filters["color"])
        query += " ORDER BY rating DESC, on_sale DESC LIMIT 300"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def count_products(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM brand_products").fetchone()[0]

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total   = conn.execute("SELECT COUNT(*) FROM brand_products").fetchone()[0]
            women   = conn.execute("SELECT COUNT(*) FROM brand_products WHERE gender='women'").fetchone()[0]
            men     = conn.execute("SELECT COUNT(*) FROM brand_products WHERE gender='men'").fetchone()[0]
            kids    = conn.execute("SELECT COUNT(*) FROM brand_products WHERE gender='kids'").fetchone()[0]
            shoes   = conn.execute("SELECT COUNT(*) FROM brand_products WHERE category='shoes'").fetchone()[0]
            jewelry = conn.execute("SELECT COUNT(*) FROM brand_products WHERE category='jewelry'").fetchone()[0]
            bags    = conn.execute("SELECT COUNT(*) FROM brand_products WHERE category='bags'").fetchone()[0]
            # Per-brand breakdown for debugging
            by_brand = {}
            rows = conn.execute(
                "SELECT brand_id, category, COUNT(*) as cnt FROM brand_products "
                "GROUP BY brand_id, category ORDER BY brand_id"
            ).fetchall()
            for row in rows:
                by_brand[f"{row[0]}:{row[1]}"] = row[2]
            return {
                "total": total, "women": women, "men": men,
                "kids": kids, "shoes": shoes, "jewelry": jewelry, "bags": bags,
                "by_brand": by_brand,
            }


# ══════════════════════════════════════════════════════════════
# SHOPIFY FETCHER
# Collection-specific URLs — no cross-gender contamination
# ══════════════════════════════════════════════════════════════

class ShopifyFetcher:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {"User-Agent": "Mozilla/5.0 (GlamourBot/2.0)"}

    def fetch_products(self, brand: dict, limit: int = 150) -> list:
        if not brand.get("is_shopify"):
            return []

        url = brand.get("fetch_url", f"https://{brand['domain']}/products.json")
        url = f"{url}?limit={limit}"

        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            products = []

            for p in response.json().get("products", []):
                variant       = p.get("variants", [{}])[0]
                price         = float(variant.get("price", 0) or 0)
                compare_price = float(variant.get("compare_at_price") or 0)
                on_sale       = compare_price > 0 and compare_price > price

                # Best quality image from Shopify CDN
                image_url = ""
                if p.get("images"):
                    raw = p["images"][0].get("src", "")
                    # Request medium (600px) version for faster loading
                    image_url = re.sub(r"(\.\w+)(\?.*)?$", r"_600x\1\2", raw) if raw else ""

                tags       = [t.lower().strip() for t in p.get("tags", [])]
                title      = p.get("title", "")
                body_text  = re.sub(r"<[^>]+>", " ", p.get("body_html", "") or "")
                full_text  = f"{title} {' '.join(tags)} {body_text}".lower()

                gender     = brand.get("gender_filter", brand["gender"][0])
                category   = brand.get("category_override", "clothing")

                color       = normalize_product_color(tags, title)
                fabric      = detect_fabric(full_text)
                fabric_tags = extract_fabric_tags(tags, title)
                event_tags  = self._extract_event_tags(tags, title, fabric)

                # If brand has gender_tags, filter by them
                gender_tags_filter = brand.get("gender_tags", [])
                if gender_tags_filter:
                    product_text = full_text + " " + " ".join(tags)
                    if not any(gt in product_text for gt in gender_tags_filter):
                        continue   # skip products not matching gender

                products.append({
                    "brand_name":   brand["name"],
                    "brand_logo":   brand.get("logo", ""),
                    "title":        title,
                    "price":        price,
                    "compare_price": compare_price,
                    "color":        color,
                    "gender":       gender,
                    "category":     category,
                    "event_tags":   event_tags,
                    "fabric":       fabric or "",
                    "fabric_tags":  fabric_tags,
                    "image_url":    image_url,
                    "product_url":  f"https://{brand['domain']}/products/{p.get('handle', '')}",
                    "on_sale":      on_sale,
                    "rating":       brand["rating"],
                    "source":       "shopify",
                })
            return products

        except Exception as e:
            print(f"[Fetch Error] {brand['id']}: {e}")
            return []

    def _extract_event_tags(self, tags: list, title: str, fabric: str) -> list:
        text = " ".join(tags) + " " + title.lower()
        found = []

        for event, keywords in EVENT_KEYWORDS.items():
            if any(k in text for k in keywords):
                found.append(event)

        # Fabric-based inference when no direct event tags
        if not found and fabric:
            found = FABRIC_EVENT_MAP.get(fabric, [])

        # Final fallbacks by fabric keywords
        if not found:
            if any(f in text for f in ["lawn", "cotton", "cambric"]):
                found = ["eid", "casual"]
            elif any(f in text for f in ["chiffon", "organza", "net", "georgette"]):
                found = ["party", "formal"]
            elif any(f in text for f in ["velvet", "silk", "jamawar", "raw silk", "satin"]):
                found = ["wedding", "formal"]
            elif any(f in text for f in ["khaddar", "karandi", "wool"]):
                found = ["winter", "casual"]

        return found or ["casual"]


# ══════════════════════════════════════════════════════════════
# CRON MANAGER
# ══════════════════════════════════════════════════════════════

class CronManager:
    def __init__(self, db: BrandDB, fetcher: ShopifyFetcher, interval_hours: int = 24):
        self.db       = db
        self.fetcher  = fetcher
        self.interval = interval_hours * 3600
        self._thread  = None
        self._running = False

    def sync_brand(self, brand: dict) -> int:
        try:
            if brand["is_shopify"]:
                # Respect per-brand delay (for sub-collections of same domain)
                delay = brand.get("fetch_delay", 0)
                if delay:
                    time.sleep(delay)
                products = self.fetcher.fetch_products(brand)
                if products:
                    self.db.upsert_products(brand["id"], products)
                    self.db.log_sync(brand["id"], "success", len(products))
                    return len(products)
                else:
                    self.db.log_sync(brand["id"], "empty", 0)
            else:
                self.db.log_sync(brand["id"], "skipped_no_api", 0)
            return 0
        except Exception as e:
            self.db.log_sync(brand["id"], "error", 0, str(e))
            return 0

    def sync_all(self):
        print("[Sync] Starting full brand sync...")
        total = 0
        for brand in BRANDS_REGISTRY:
            n = self.sync_brand(brand)
            if n:
                print(f"  OK  {brand['name']}: {n} products")
            time.sleep(1.2)
        print(f"[Sync] Done. Total products in DB: {self.db.count_products()}")

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        self.sync_all()
        while self._running:
            time.sleep(self.interval)
            if self._running:
                self.sync_all()

    def stop(self):
        self._running = False


# ══════════════════════════════════════════════════════════════
# BRAND RECOMMENDER — Main class
# ══════════════════════════════════════════════════════════════

class BrandRecommender:
    def __init__(self, db_path: str = None, auto_sync: bool = True, groq_key: str = None):
        self.db      = BrandDB(db_path)
        self.fetcher = ShopifyFetcher()
        self.cron    = CronManager(self.db, self.fetcher)

        # Groq key override
        if groq_key:
            global GROQ_API_KEY
            GROQ_API_KEY = groq_key

        if auto_sync:
            if self.db.count_products() == 0:
                threading.Thread(target=self.cron.sync_all, daemon=True).start()
            else:
                self.cron.start()

    def recommend(self, user_message: str, event_info: dict = None, max_results: int = 6) -> dict:
        query    = user_message.lower()
        gender   = detect_gender(query)
        category = detect_category(query)
        language = detect_language(user_message)

        # Event: prefer explicit override, else auto-detect
        if event_info and event_info.get("event") and event_info["event"] != "general":
            event = event_info["event"]
        else:
            event = detect_event(query)

        detected_color  = detect_color(query)
        detected_fabric = detect_fabric(query)

        # Shoes -> always fallback (no Shopify data)
        if category == "shoes":
            return self._fallback_brand_suggest(event, gender, category, language)

        # Bags / Jewelry -> try DB first, fallback if empty
        if category in ("bags", "jewelry"):
            db_products = self.db.get_products({"category": category})
            if not db_products:
                return self._fallback_brand_suggest(event, gender, category, language)
        else:
            # Clothing
            db_products = self.db.get_products({"gender": gender, "category": "clothing"})

        if not db_products:
            return self._fallback_brand_suggest(event, gender, category, language)

        month = datetime.now().month

        event_fabrics = {
            "wedding": ["silk", "velvet", "net", "jamawar", "raw silk", "organza", "satin", "tissue", "banarsi"],
            "barat":   ["silk", "velvet", "net", "raw silk", "banarsi", "jamawar"],
            "mehndi":  ["chiffon", "organza", "net", "georgette", "crepe"],
            "eid":     ["lawn", "chiffon", "cotton", "dobby", "cambric"],
            "casual":  ["lawn", "cotton", "khaddar", "linen", "cambric"],
            "formal":  ["chiffon", "silk", "organza", "jacquard", "crepe"],
            "party":   ["chiffon", "net", "silk", "satin", "crepe", "georgette"],
            "winter":  ["khaddar", "karandi", "velvet", "wool"],
        }

        scored = []
        for p in db_products:
            score = 0
            event_tags  = json.loads(p.get("event_tags", "[]") or "[]")
            fabric_tags = json.loads(p.get("fabric_tags", "[]") or "[]")
            brand_info  = next((b for b in BRANDS_REGISTRY if b["id"] == p["brand_id"]), {})
            title_lower = p.get("title", "").lower()
            p_color     = p.get("color", "")
            p_fabric    = p.get("fabric", "")

            # ── EVENT SCORE ──
            if event != "general":
                if event in event_tags:
                    score += 40
                elif event in brand_info.get("speciality", []):
                    score += 25
                # Fabric matches event
                preferred_fabrics = event_fabrics.get(event, [])
                if p_fabric and p_fabric in preferred_fabrics:
                    score += 20
                elif any(f in fabric_tags for f in preferred_fabrics):
                    score += 12

            # ── COLOR SCORE (high weight — wrong color = big penalty) ──
            if detected_color:
                if p_color == detected_color:
                    score += 55
                elif detected_color in title_lower:
                    score += 35
                elif p_color == "multi":
                    score -= 10   # multi-color slight penalty when specific color requested
                else:
                    score -= 40   # wrong color — strong penalty

            # ── FABRIC SCORE ──
            if detected_fabric:
                if p_fabric == detected_fabric:
                    score += 30
                elif detected_fabric in fabric_tags:
                    score += 18

            # ── GENDER EXACT MATCH / MISMATCH ──
            if p.get("gender") == gender:
                score += 30
            else:
                score -= 60   # hard penalty — wrong gender products must never appear

            # ── KEYWORD MATCH in title ──
            query_words = [w for w in query.split() if len(w) > 3]
            score += sum(4 for w in query_words if w in title_lower)

            # ── SALE + RATING ──
            if p.get("on_sale"):
                score += 12
            if month in brand_info.get("sale_months", []):
                score += 8
            score += (float(p.get("rating", 4.0)) - 4.0) * 10

            # ── IMAGE BOOST ──
            if p.get("image_url"):
                score += 5

            # ── PENALIZE unstitched for ready-to-wear events ──
            if event in ("eid", "casual", "mehndi", "party"):
                if "unstitched" in title_lower:
                    score -= 25

            # ── BONANZA SKU gender check ──
            if p.get("brand_id") in ("bonanza", "bonanza_kids"):
                sku_match = re.search(r"\(([A-Z]{2,3})\d*", p.get("title", "").upper())
                if sku_match:
                    prefix = sku_match.group(1)
                    if gender == "men" and not any(prefix.startswith(x) for x in ["MU", "MP", "MN", "MS"]):
                        score -= 40
                    if gender == "kids" and not any(prefix.startswith(x) for x in ["GP", "BP", "KP", "GS", "BS"]):
                        score -= 30

            # ── TITLE gender keyword check — extra safety ──
            if gender == "men":
                if any(w in title_lower for w in ["girl", "girls", "women", "ladies", "female", "baby girl"]):
                    score -= 50
            if gender == "women":
                if any(w in title_lower for w in ["boy", "boys", "men's", "gents", "male"]):
                    score -= 50
            if gender == "kids":
                if any(w in title_lower for w in ["polo shirt", "t-shirt", "trousers"]) and                    not any(w in title_lower for w in ["kids", "girl", "boy", "child"]):
                    score -= 20

            if score > 0:
                scored.append({**p, "score": round(score)})

        scored.sort(key=lambda x: x["score"], reverse=True)

        # Deduplicate
        seen, unique = set(), []
        for p in scored:
            key = (p.get("brand_id", ""), p.get("title", "")[:40])
            if key not in seen:
                seen.add(key)
                unique.append(p)

        top = unique[:max_results]
        if not top:
            return self._fallback_brand_suggest(event, gender, category, language)

        return {
            "brands":           top,
            "has_results":      True,
            "event":            event,
            "gender":           gender,
            "category":         category,
            "language":         language,
            "detected_color":   detected_color,
            "detected_fabric":  detected_fabric,
            "summary":          self._build_summary(top, event, gender, category),
        }

    def _fallback_brand_suggest(self, event: str, gender: str, category: str, language: str = "english") -> dict:
        month = datetime.now().month
        matched = []

        for brand in BRANDS_REGISTRY:
            if category and category not in brand.get("category", []):
                continue
            score = 0
            if gender and gender in brand.get("gender", []):
                score += 20
            if event in brand.get("speciality", []):
                score += 30
            if month in brand.get("sale_months", []):
                score += 15
            score += (brand["rating"] - 4.0) * 10

            if score <= 0:
                continue

            # Pick best nav URL
            if event in ["wedding", "barat"] and "bridal" in brand["nav_urls"]:
                nav_url = brand["nav_urls"]["bridal"]
            elif gender == "kids" and "kids" in brand["nav_urls"]:
                nav_url = brand["nav_urls"]["kids"]
            elif gender == "men" and "men" in brand["nav_urls"]:
                nav_url = brand["nav_urls"]["men"]
            elif category in brand["nav_urls"]:
                nav_url = brand["nav_urls"][category]
            else:
                nav_url = list(brand["nav_urls"].values())[0]

            matched.append({
                "brand_id":    brand["id"],
                "brand_name":  brand["name"],
                "brand_logo":  brand.get("logo", ""),
                "title":       "",
                "product_url": nav_url,
                "image_url":   "",
                "price":       0,
                "compare_price": 0,
                "on_sale":     month in brand["sale_months"],
                "rating":      brand["rating"],
                "score":       score,
                "source":      "fallback",
                "color":       "",
                "fabric":      "",
            })

        matched.sort(key=lambda x: x["score"], reverse=True)
        top = matched[:6]

        return {
            "brands":          top,
            "has_results":     len(top) > 0,
            "event":           event,
            "gender":          gender,
            "category":        category,
            "language":        language,
            "detected_color":  None,
            "detected_fabric": None,
            "summary":         self._build_summary(top, event, gender, category),
        }

    def _build_summary(self, products: list, event: str, gender: str, category: str) -> str:
        """Plain text RAG context for the AI model."""
        if not products:
            return ""
        lines = [f"Pakistani brand recommendations for {event} ({gender}, {category}):"]
        for p in products[:5]:
            price_str = f"PKR {int(p['price']):,}" if p.get("price", 0) > 0 else "See website"
            sale_str  = " [ON SALE]" if p.get("on_sale") else ""
            title_str = f" — {p['title']}" if p.get("title") else ""
            color_str = f" | Color: {p['color']}" if p.get("color") else ""
            fab_str   = f" | Fabric: {p['fabric']}" if p.get("fabric") else ""
            lines.append(
                f"- {p.get('brand_name','')} ({p.get('brand_logo','')})"
                f"{title_str} | {price_str}{sale_str}"
                f"{color_str}{fab_str}"
                f" | Rating: {p.get('rating', 4.0)}"
                f" | {p.get('product_url', '')}"
            )
        return "\n".join(lines)

    def enhance_prompt(self, user_message: str, event_info: dict = None) -> str:
        """
        Enhance user message with fashion context for the AI model.
        Preserves original language — adds context in English.
        """
        query    = user_message.lower()
        language = detect_language(user_message)

        if event_info and event_info.get("event") and event_info["event"] != "general":
            event = event_info["event"]
        else:
            event = detect_event(query)

        gender   = detect_gender(query)
        category = detect_category(query)
        color    = detect_color(query)
        fabric   = detect_fabric(query)

        context_parts = []

        event_tips = {
            "wedding": "Heavy embroidery, silk/velvet/net fabric. Deep jewel tones: maroon, navy, emerald.",
            "barat":   "Red, maroon or gold shades. Gharara, lehenga or heavily embroidered suit.",
            "mehndi":  "Yellow, orange, green or coral colors. Light chiffon or organza fabric.",
            "eid":     "Fresh pastels or bright colors. Lawn or cotton fabric. 3-piece suits trending.",
            "casual":  "Comfort first — cotton, lawn or khaddar. Simple prints or solid colors.",
            "formal":  "Structured silhouettes, chiffon or silk. Subtle embroidery or lace.",
            "party":   "Statement pieces — embellishments, sequins, bold colors. Chiffon or silk.",
            "winter":  "Khaddar, karandi or velvet. Deep tones: burgundy, bottle green, navy.",
        }
        gender_tips = {
            "women": "Women: suit, sharara, gharara, lehenga options.",
            "men":   "Men: shalwar kameez, kurta trouser or sherwani.",
            "kids":  "Kids: comfortable fabric essential — cotton or lawn.",
        }
        category_tips = {
            "shoes":   "Shoes: match occasion — heels for bridal, flats/khussa for casual.",
            "jewelry": "Jewelry: one statement piece, keep rest minimal.",
            "bags":    "Bags: match size and color to outfit — clutch for formal, tote for casual.",
        }

        if event in event_tips:
            context_parts.append(event_tips[event])
        context_parts.append(gender_tips.get(gender, gender_tips["women"]))
        if category in category_tips:
            context_parts.append(category_tips[category])
        if color:
            context_parts.append(f"User wants color: {color}.")
        if fabric:
            context_parts.append(f"User wants fabric: {fabric}.")
        if language == "roman_urdu":
            context_parts.append(
                "IMPORTANT: User wrote in Roman Urdu. "
                "Respond in Roman Urdu / mixed language as they wrote. "
                "Do not switch to full English."
            )

        enhanced = user_message.strip()
        if context_parts:
            enhanced += " | Context: " + " ".join(context_parts)
        return enhanced

    def format_response(self, result: dict, user_message: str = "") -> str:
        """
        Format recommendations as a fashion stylist response.
        Uses Groq if available, falls back to Python formatter.
        Language: Roman Urdu if user wrote in Roman Urdu, else English.
        """
        language = result.get("language", detect_language(user_message))
        roman    = language == "roman_urdu"
        products = result.get("brands", [])

        # Try Groq first
        if products and result.get("has_results"):
            groq_text = _call_groq(
                _groq_system_prompt(language),
                _groq_user_prompt(user_message, products, result),
            )
            if groq_text:
                return groq_text

        if not result.get("has_results") or not result.get("brands"):
            if roman:
                return "Is query ke liye koi matching products nahi mile. Directly brand websites check kar sakte hain."
            return "No matching products found for this query. Please check the brand websites directly."

        event    = result.get("event", "general")
        brands   = result.get("brands", [])
        category = result.get("category", "clothing")

        # Opening line
        if roman:
            event_intros = {
                "wedding": "Shadi ke liye outfit selection mein yeh options dekhein —",
                "barat":   "Barat ka din khaas hota hai, is liye yeh curated picks —",
                "mehndi":  "Mehndi ke liye rang aur fabric dono important hain —",
                "eid":     "Eid ke liye fresh aur festive options —",
                "casual":  "Casual wear ke liye comfortable aur stylish options —",
                "formal":  "Formal occasions ke liye yeh dekhein —",
                "party":   "Party mein standout karne ke liye —",
                "winter":  "Winter ke liye warm aur stylish options —",
                "general": "Aap ke liye curated suggestions —",
            }
        else:
            event_intros = {
                "wedding": "For your wedding outfit, here are the best options —",
                "barat":   "For the Barat day, these curated picks are perfect —",
                "mehndi":  "For Mehndi, color and fabric both matter —",
                "eid":     "For Eid, fresh and festive options —",
                "casual":  "For casual wear, comfortable yet stylish —",
                "formal":  "For formal occasions, polished looks —",
                "party":   "To stand out at the party —",
                "winter":  "For winter, warm and stylish options —",
                "general": "Here are curated suggestions for you —",
            }

        lines = [event_intros.get(event, event_intros["general"]), ""]

        seen_brands = set()
        count = 0
        for p in brands[:6]:
            name    = p.get("brand_name") or p.get("brand_id", "")
            logo    = p.get("brand_logo") or p.get("logo", "")
            title   = p.get("title", "")
            price   = p.get("price", 0)
            on_sale = p.get("on_sale", False)
            url     = p.get("product_url", "")
            rating  = p.get("rating", 4.0)
            source  = p.get("source", "shopify")
            count  += 1

            if source == "fallback":
                if name in seen_brands:
                    continue
                seen_brands.add(name)
                if roman:
                    sale_note = " (Sale chal rahi hai!)" if on_sale else ""
                    cat_desc = {
                        "shoes":    "Pakistan ke top shoe brands mein — heels, flats, bridal aur casual sab milta hai.",
                        "jewelry":  "Pakistani jewelry mein — bridal se casual tak sab collections available hain.",
                        "bags":     "Stylish bags aur clutches ke liye best option.",
                        "clothing": "Pakistan ke top fashion brands mein se ek.",
                    }
                else:
                    sale_note = " (Sale is live!)" if on_sale else ""
                    cat_desc = {
                        "shoes":    "One of Pakistan's top shoe brands — heels, flats, bridal and casual all available.",
                        "jewelry":  "Popular Pakistani jewelry brand — bridal to casual all collections available.",
                        "bags":     "Best option for stylish bags and clutches.",
                        "clothing": "One of Pakistan's top fashion brands.",
                    }
                lines.append(f"{count}. {logo} {name}{sale_note}")
                lines.append(f"   {cat_desc.get(category, cat_desc['clothing'])}")
                lines.append(f"   Link: {url}")
            else:
                price_str = f"PKR {int(price):,}" if price > 0 else ("Website par dekhein" if roman else "See website")
                sale_str  = (" — Sale price!" if not roman else " — Sale price!") if on_sale else ""
                lines.append(f"{count}. {logo} {name} — {title}")
                lines.append(f"   {price_str}{sale_str} | Rating: {rating}/5")
                lines.append(f"   Link: {url}")

            lines.append("")

        # Styling tip
        if roman:
            tips = {
                "wedding": "Tip: Outfit ke saath matching jewelry aur bridal shoes complete look banate hain.",
                "barat":   "Tip: Barat ke liye red ya maroon rakhen — antique gold jewelry perfect hai.",
                "mehndi":  "Tip: Mehndi pe light fabric rahein — comfortable bhi, photogenic bhi.",
                "eid":     "Tip: Fresh colors try karein. Statement earrings aur matching chappal.",
                "party":   "Tip: Ek statement piece rakhen — baqi accessories simple.",
                "winter":  "Tip: Shawl ya dupatta warm bhi hai, stylish bhi.",
            }
        else:
            tips = {
                "wedding": "Tip: Matching jewelry and bridal shoes complete the look. Dupatta styling matters too!",
                "barat":   "Tip: Keep red or maroon as dominant color — antique gold jewelry is a perfect complement.",
                "mehndi":  "Tip: Choose light fabric for Mehndi — you'll be sitting/moving a lot. Block heels are comfortable.",
                "eid":     "Tip: Try fresh colors for Eid. Statement earrings and matching footwear complete the look.",
                "party":   "Tip: One statement piece — keep other accessories minimal. Less is more!",
                "winter":  "Tip: A shawl or dupatta adds layering — both stylish and warm.",
            }
        if event in tips:
            lines.append(tips[event])

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    rec = BrandRecommender(auto_sync=False)

    # Clear and re-sync
    with sqlite3.connect(rec.db.db_path) as c:
        c.execute("DELETE FROM brand_products")
        c.commit()

    print("Syncing all brands...")
    rec.cron.sync_all()

    s = rec.db.stats()
    print(f"\nDB Stats: {s}\n")

    test_cases = [
        # (query, event_override, expected_notes)
        ("shadi ke liye red dress chahiye",       {"event": "wedding"}, "Roman Urdu, red, wedding"),
        ("eid ke liye lawn suit",                 {"event": "eid"},     "Roman Urdu, lawn, eid"),
        ("mehndi ke liye yellow gharara",         {"event": "mehndi"},  "Roman Urdu, yellow, mehndi"),
        ("mard ka kurta eid ke liye",             {"event": "eid"},     "Roman Urdu, men, eid"),
        ("girls eid dress",                       {"event": "eid"},     "English, kids, eid"),
        ("barat ke liye red shoes chahiye",       {"event": "barat"},   "Roman Urdu, shoes, barat"),
        ("shadi ke liye jewelry chahiye",         {"event": "wedding"}, "Roman Urdu, jewelry"),
        ("clutch bag chahiye party ke liye",      {"event": "party"},   "Roman Urdu, bags"),
        ("black formal suit for men",             {},                   "English, men, black, formal"),
        ("kala suit mard ke liye eid pe",         {"event": "eid"},     "Roman Urdu, kala=black, men"),
        ("yellow chiffon dress for mehndi",       {"event": "mehndi"},  "English, yellow, chiffon"),
    ]

    for query, event_info, notes in test_cases:
        result   = rec.recommend(query, event_info)
        enhanced = rec.enhance_prompt(query, event_info)
        response = rec.format_response(result, query)
        print(f"{'='*65}")
        print(f"Query    : {query}")
        print(f"Notes    : {notes}")
        print(f"Detected : color={result.get('detected_color')} | "
              f"fabric={result.get('detected_fabric')} | "
              f"event={result['event']} | gender={result['gender']} | "
              f"lang={result.get('language')}")
        print(f"Results  : {len(result['brands'])} brands")
        print(f"Response snippet:\n{response[:200]}")
        print()