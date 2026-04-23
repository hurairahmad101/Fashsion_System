"""
GlamourBot — Database Setup Script
Run: python3 create_db.py
Yeh script brands_cache.db banata hai aur Shopify brands se data sync karta hai.
"""

import os
import json
import time
import sqlite3
import requests
import re
from datetime import datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "brands_cache.db")

# ══════════════════════════════════════════════════════════════
# BRANDS REGISTRY
# ══════════════════════════════════════════════════════════════
BRANDS_REGISTRY = [
    # ── WOMEN ──
    {"id":"gulahmed",     "name":"Gul Ahmed",       "logo":"🌺", "gender":["women"], "category":["clothing"],            "rating":4.3, "is_shopify":True,  "domain":"www.gulahmedshop.com",   "sale_months":[3,4,6,9,10,12], "speciality":["lawn","eid","casual","formal","winter"],           "fetch_url":"https://www.gulahmedshop.com/products.json",                                     "gender_filter":"women"},
    {"id":"mariab",       "name":"Maria B",          "logo":"👑", "gender":["women"], "category":["clothing","jewelry","bags"], "rating":4.8, "is_shopify":True, "domain":"www.mariab.pk",         "sale_months":[1,6,7,12],      "speciality":["bridal","wedding","luxury","mehndi","walima"],     "fetch_url":"https://www.mariab.pk/products.json",                                            "gender_filter":"women"},
    {"id":"sanasafinaz",  "name":"Sana Safinaz",     "logo":"✨", "gender":["women"], "category":["clothing"],            "rating":4.6, "is_shopify":True,  "domain":"sanasafinaz.com",         "sale_months":[2,6,8,11],      "speciality":["luxury","lawn","formal","wedding"],                "fetch_url":"https://sanasafinaz.com/products.json",                                          "gender_filter":"women"},
    {"id":"alkaram",      "name":"Alkaram Studio",   "logo":"🎨", "gender":["women"], "category":["clothing"],            "rating":4.2, "is_shopify":True,  "domain":"www.alkaramstudio.com",   "sale_months":[3,6,9,12],      "speciality":["lawn","casual","pret","eid","winter"],            "fetch_url":"https://www.alkaramstudio.com/products.json",                                    "gender_filter":"women"},
    {"id":"nomiansari",   "name":"Nomi Ansari",      "logo":"🌸", "gender":["women"], "category":["clothing"],            "rating":4.7, "is_shopify":False, "domain":"nomiansari.com",          "sale_months":[1,7],           "speciality":["bridal","couture","mehndi","wedding","party"],     "nav_urls":{"women":"https://nomiansari.com"}},
    {"id":"hsy",          "name":"HSY",              "logo":"💎", "gender":["women"], "category":["clothing"],            "rating":4.9, "is_shopify":False, "domain":"hsy.com.pk",              "sale_months":[1,8],           "speciality":["bridal","couture","luxury","wedding","barat"],     "nav_urls":{"women":"https://hsy.com.pk"}},

    # ── MEN ──
    {"id":"bonanza",      "name":"Bonanza Satrangi", "logo":"🎪", "gender":["men"],   "category":["clothing"],            "rating":4.3, "is_shopify":True,  "domain":"www.bonanzasatrangi.com","sale_months":[3,6,9,12],      "speciality":["men kurta","shalwar kameez","eid","casual"],       "fetch_url":"https://www.bonanzasatrangi.com/products.json",                                  "gender_filter":"men"},
    {"id":"edenrobe",     "name":"Edenrobe",         "logo":"🌿", "gender":["men"],   "category":["clothing"],            "rating":4.2, "is_shopify":True,  "domain":"www.edenrobe.com",        "sale_months":[3,6,9,12],      "speciality":["men kurta","shalwar kameez","eid","casual"],       "fetch_url":"https://www.edenrobe.com/products.json",                                         "gender_filter":"men"},
    {"id":"sapphire_men", "name":"Sapphire Men",     "logo":"💙", "gender":["men"],   "category":["clothing"],            "rating":4.5, "is_shopify":True,  "domain":"pk.sapphireonline.pk",    "sale_months":[3,6,9,12],      "speciality":["men kurta","eid","casual","pret","formal"],        "fetch_url":"https://pk.sapphireonline.pk/products.json",                                     "gender_filter":"men"},
    {"id":"cambridge",    "name":"Cambridge",        "logo":"🎓", "gender":["men"],   "category":["clothing"],            "rating":4.4, "is_shopify":True,  "domain":"www.cambridge.com.pk",    "sale_months":[6,12],          "speciality":["formal","western","shirts","trousers","suits"],    "fetch_url":"https://www.cambridge.com.pk/products.json",                                     "gender_filter":"men"},
    {"id":"charcoal",     "name":"Charcoal",         "logo":"🖤", "gender":["men"],   "category":["clothing"],            "rating":4.3, "is_shopify":True,  "domain":"www.charcoalpk.com",      "sale_months":[6,12],          "speciality":["formal","western","casual","shirts","modern"],     "fetch_url":"https://www.charcoalpk.com/products.json",                                       "gender_filter":"men"},
    {"id":"junaidjamshed","name":"J. Junaid Jamshed", "logo":"👔", "gender":["men"],  "category":["clothing"],            "rating":4.4, "is_shopify":False, "domain":"jdot.pk",                 "sale_months":[3,6,9,12],      "speciality":["men kurta","shalwar kameez","eid","casual"],       "nav_urls":{"men":"https://www.jdot.pk/men"}},

    # ── KIDS ──
    {"id":"mariab_kids",  "name":"Maria B Kids",     "logo":"👧", "gender":["kids"],  "category":["clothing"],            "rating":4.8, "is_shopify":True,  "domain":"www.mariab.pk",           "sale_months":[1,6,7,12],      "speciality":["eid kids","festive","casual","formal"],            "fetch_url":"https://www.mariab.pk/collections/view-all-kids/products.json",                  "gender_filter":"kids"},
    {"id":"alkaram_kids", "name":"Alkaram Kids",     "logo":"🎨", "gender":["kids"],  "category":["clothing"],            "rating":4.2, "is_shopify":True,  "domain":"www.alkaramstudio.com",   "sale_months":[3,6,9,12],      "speciality":["eid kids","casual","festive"],                     "fetch_url":"https://www.alkaramstudio.com/collections/kids/products.json",                   "gender_filter":"kids"},
    {"id":"bonanza_kids", "name":"Bonanza Kids",     "logo":"🎪", "gender":["kids"],  "category":["clothing"],            "rating":4.3, "is_shopify":True,  "domain":"www.bonanzasatrangi.com", "sale_months":[3,6,9,12],      "speciality":["eid kids","casual","festive"],                     "fetch_url":"https://www.bonanzasatrangi.com/collections/kids/products.json",                 "gender_filter":"kids"},
    {"id":"sapphire_kids","name":"Sapphire Kids",    "logo":"💙", "gender":["kids"],  "category":["clothing"],            "rating":4.5, "is_shopify":True,  "domain":"pk.sapphireonline.pk",    "sale_months":[3,6,9,12],      "speciality":["eid kids","casual","festive"],                     "fetch_url":"https://pk.sapphireonline.pk/collections/kids/products.json",                    "gender_filter":"kids"},
    {"id":"babyhaven",    "name":"Baby Haven",       "logo":"👶", "gender":["kids"],  "category":["clothing"],            "rating":4.2, "is_shopify":False, "domain":"babyhavenpk.com",         "sale_months":[3,9],           "speciality":["baby clothes","toddler","kids casual","eid kids"], "nav_urls":{"kids":"https://www.babyhavenpk.com"}},
    {"id":"ethnicbypfl",  "name":"Ethnic by Outfitters","logo":"🏵️","gender":["kids"],"category":["clothing"],           "rating":4.1, "is_shopify":False, "domain":"ethnicbyoutfitters.com",  "sale_months":[3,6,9,12],      "speciality":["casual","eid kids","pret","everyday"],             "nav_urls":{"kids":"https://www.ethnicbyoutfitters.com/collections/kids"}},

    # ── SHOES ──
    {"id":"stylo",        "name":"Stylo Shoes",      "logo":"👠", "gender":["women","men","kids"], "category":["shoes"], "rating":4.3, "is_shopify":False, "domain":"stylo.pk",               "sale_months":[3,6,9,12],      "speciality":["heels","flats","formal shoes","casual shoes","bridal shoes"], "nav_urls":{"women":"https://www.stylo.pk/collections/women","men":"https://www.stylo.pk/collections/men","kids":"https://www.stylo.pk/collections/kids"}},
    {"id":"bata",         "name":"Bata Pakistan",    "logo":"👟", "gender":["women","men","kids"], "category":["shoes"], "rating":4.0, "is_shopify":False, "domain":"bata.com.pk",            "sale_months":[3,6,9,12],      "speciality":["casual shoes","formal shoes","everyday wear","kids shoes"],    "nav_urls":{"women":"https://www.bata.com.pk/collections/women","men":"https://www.bata.com.pk/collections/men"}},
    {"id":"borjan",       "name":"Borjan Shoes",     "logo":"👡", "gender":["women","men"],        "category":["shoes"], "rating":4.2, "is_shopify":False, "domain":"borjan.com.pk",          "sale_months":[3,6,9,12],      "speciality":["heels","formal shoes","bridal shoes","casual shoes"],          "nav_urls":{"women":"https://www.borjan.com.pk/collections/women","men":"https://www.borjan.com.pk/collections/men"}},
    {"id":"insignia",     "name":"Insignia",         "logo":"✨", "gender":["women"],              "category":["shoes"], "rating":4.4, "is_shopify":False, "domain":"insignia.com.pk",        "sale_months":[3,6,9,12],      "speciality":["heels","bridal shoes","formal shoes","clutch"],                "nav_urls":{"women":"https://www.insignia.com.pk/collections/footwear"}},
    {"id":"metro",        "name":"Metro Shoes",      "logo":"👞", "gender":["women","men","kids"], "category":["shoes"], "rating":4.1, "is_shopify":False, "domain":"metroshoes.net",         "sale_months":[3,6,9,12],      "speciality":["casual shoes","formal shoes","bridal shoes","kids shoes"],     "nav_urls":{"women":"https://www.metroshoes.net/collections/women","men":"https://www.metroshoes.net/collections/men"}},

    # ── JEWELRY ──
    {"id":"mariab_jewelry",     "name":"Maria B Jewelry",      "logo":"💍", "gender":["women"], "category":["jewelry"], "rating":4.8, "is_shopify":True,  "domain":"www.mariab.pk",        "sale_months":[1,6,7,12],  "speciality":["wedding","bridal","mehndi","party","formal"],   "fetch_url":"https://www.mariab.pk/collections/jewelry/products.json",                 "gender_filter":"women", "category_override":"jewelry"},
    {"id":"aghasnoor",          "name":"Agha Noor",             "logo":"🌟", "gender":["women"], "category":["jewelry"], "rating":4.5, "is_shopify":False, "domain":"aghasnoor.com",        "sale_months":[1,6,12],    "speciality":["bridal","wedding","mehndi","party","jewelry"],   "nav_urls":{"jewelry":"https://www.aghasnoor.com/collections/jewelry"}},
    {"id":"gulahmed_jewelry",   "name":"Gul Ahmed Jewelry",    "logo":"🌺", "gender":["women"], "category":["jewelry"], "rating":4.3, "is_shopify":True,  "domain":"www.gulahmedshop.com", "sale_months":[3,4,6,9,10,12], "speciality":["jewelry","casual","formal","eid"],           "fetch_url":"https://www.gulahmedshop.com/collections/accessories-jewelry/products.json","gender_filter":"women", "category_override":"jewelry"},
    {"id":"zarqjewels",         "name":"Zarq Jewels",           "logo":"💎", "gender":["women"], "category":["jewelry"], "rating":4.4, "is_shopify":False, "domain":"zarqjewels.com",       "sale_months":[6,12],      "speciality":["bridal","wedding","mehndi","party"],             "nav_urls":{"jewelry":"https://www.zarqjewels.com"}},

    # ── BAGS ──
    {"id":"mariab_bags",        "name":"Maria B Bags",         "logo":"👜", "gender":["women"], "category":["bags"],    "rating":4.8, "is_shopify":True,  "domain":"www.mariab.pk",        "sale_months":[1,6,7,12],  "speciality":["clutch","handbag","wedding","formal","party"],   "fetch_url":"https://www.mariab.pk/collections/bags/products.json",                    "gender_filter":"women", "category_override":"bags"},
    {"id":"gulahmed_bags",      "name":"Gul Ahmed Bags",       "logo":"🌺", "gender":["women"], "category":["bags"],    "rating":4.3, "is_shopify":True,  "domain":"www.gulahmedshop.com", "sale_months":[3,4,6,9,10,12], "speciality":["tote","handbag","casual","everyday"],        "fetch_url":"https://www.gulahmedshop.com/collections/accessories-tote-bags/products.json","gender_filter":"women","category_override":"bags"},
    {"id":"khaadi_bags",        "name":"Khaadi Bags",          "logo":"🌿", "gender":["women"], "category":["bags"],    "rating":4.5, "is_shopify":False, "domain":"pk.khaadi.com",        "sale_months":[3,4,6,9,10],"speciality":["tote","handbag","casual","everyday"],            "nav_urls":{"bags":"https://pk.khaadi.com/accessories.html"}},
    {"id":"sapphire_bags",      "name":"Sapphire Bags",        "logo":"💙", "gender":["women"], "category":["bags"],    "rating":4.5, "is_shopify":True,  "domain":"pk.sapphireonline.pk", "sale_months":[3,6,9,12],  "speciality":["handbag","tote","casual","formal"],              "fetch_url":"https://pk.sapphireonline.pk/collections/bags/products.json",              "gender_filter":"women", "category_override":"bags"},
]


# ══════════════════════════════════════════════════════════════
# DATABASE SETUP
# ══════════════════════════════════════════════════════════════
def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS brand_products (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id     TEXT NOT NULL,
            brand_name   TEXT,
            title        TEXT,
            price        REAL DEFAULT 0,
            color        TEXT,
            gender       TEXT,
            category     TEXT DEFAULT 'clothing',
            event_tags   TEXT DEFAULT '[]',
            fabric_tags  TEXT DEFAULT '[]',
            image_url    TEXT,
            product_url  TEXT,
            on_sale      INTEGER DEFAULT 0,
            rating       REAL DEFAULT 4.0,
            source       TEXT DEFAULT 'shopify',
            last_updated TEXT
        );

        CREATE TABLE IF NOT EXISTS brand_sync_log (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id         TEXT,
            sync_time        TEXT,
            status           TEXT,
            products_fetched INTEGER DEFAULT 0,
            error_msg        TEXT
        );

        CREATE TABLE IF NOT EXISTS brands_meta (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id    TEXT UNIQUE,
            brand_name  TEXT,
            logo        TEXT,
            gender      TEXT,
            category    TEXT,
            rating      REAL,
            is_shopify  INTEGER,
            domain      TEXT,
            sale_months TEXT,
            speciality  TEXT,
            nav_urls    TEXT,
            fetch_url   TEXT,
            created_at  TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_gender   ON brand_products(gender);
        CREATE INDEX IF NOT EXISTS idx_category ON brand_products(category);
        CREATE INDEX IF NOT EXISTS idx_brand_id ON brand_products(brand_id);
        CREATE INDEX IF NOT EXISTS idx_on_sale  ON brand_products(on_sale);
    """)
    conn.commit()
    print("[OK] Tables created.")


# ══════════════════════════════════════════════════════════════
# SEED BRANDS META
# ══════════════════════════════════════════════════════════════
def seed_brands_meta(conn):
    now = datetime.now().isoformat()
    for b in BRANDS_REGISTRY:
        conn.execute("""
            INSERT OR REPLACE INTO brands_meta
            (brand_id, brand_name, logo, gender, category, rating,
             is_shopify, domain, sale_months, speciality, nav_urls, fetch_url, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            b["id"], b["name"], b["logo"],
            json.dumps(b.get("gender", [])),
            json.dumps(b.get("category", [])),
            b["rating"], 1 if b["is_shopify"] else 0,
            b["domain"],
            json.dumps(b.get("sale_months", [])),
            json.dumps(b.get("speciality", [])),
            json.dumps(b.get("nav_urls", {})),
            b.get("fetch_url", ""),
            now
        ))
    conn.commit()
    print(f"[OK] {len(BRANDS_REGISTRY)} brands meta seeded.")


# ══════════════════════════════════════════════════════════════
# SHOPIFY FETCHER
# ══════════════════════════════════════════════════════════════
HEADERS = {"User-Agent": "Mozilla/5.0 (GlamourBot/1.0)"}

def extract_event_tags(tags, title):
    text = " ".join(tags) + " " + title.lower()
    event_keywords = {
        "wedding": ["wedding","bridal","barat","shadi","bride","nikkah","valima","walima"],
        "mehndi":  ["mehndi","henna","mayoun"],
        "eid":     ["eid","festive","3 piece","2 piece","lawn suit"],
        "casual":  ["casual","daily","everyday","basic"],
        "formal":  ["formal","office","professional","pret"],
        "party":   ["party","function","dinner","evening"],
        "winter":  ["winter","khaddar","karandi","wool"],
    }
    found = [ev for ev, kws in event_keywords.items() if any(k in text for k in kws)]
    if not found:
        if any(f in text for f in ["lawn","cotton","linen"]):       found = ["eid","casual"]
        elif any(f in text for f in ["chiffon","organza","net"]):   found = ["party","formal"]
        elif any(f in text for f in ["velvet","silk","jamawar"]):   found = ["wedding","formal"]
        elif any(f in text for f in ["khaddar","karandi"]):         found = ["winter","casual"]
    return found or ["eid","casual"]

def extract_fabric_tags(tags, title):
    text = " ".join(tags) + " " + title.lower()
    return [f for f in ["lawn","chiffon","silk","cotton","velvet","net","organza",
                         "khaddar","karandi","georgette","raw silk","jamawar",
                         "linen","dobby","jacquard"] if f in text]

def detect_color(tags, title):
    text = " ".join(tags) + " " + title.lower()
    for c in ["red","blue","green","yellow","pink","white","black","maroon","gold",
              "navy","peach","orange","purple","teal","brown","grey","cream",
              "ivory","coral","mint","lilac","rust","mustard"]:
        if c in text: return c
    return "multi"

def fetch_shopify(brand, limit=100):
    url = brand.get("fetch_url", f"https://{brand['domain']}/products.json")
    url = f"{url}?limit={limit}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        products = []
        for p in r.json().get("products", []):
            variant      = p.get("variants", [{}])[0]
            price        = float(variant.get("price", 0))
            compare      = variant.get("compare_at_price")
            on_sale      = compare is not None and float(compare or 0) > price
            image_url    = p["images"][0].get("src","") if p.get("images") else ""
            tags         = [t.lower() for t in p.get("tags", [])]
            title        = p.get("title","")
            gender       = brand.get("gender_filter", brand["gender"][0])
            category     = brand.get("category_override","clothing")
            products.append({
                "brand_name":  brand["name"],
                "title":       title,
                "price":       price,
                "color":       detect_color(tags, title),
                "gender":      gender,
                "category":    category,
                "event_tags":  json.dumps(extract_event_tags(tags, title)),
                "fabric_tags": json.dumps(extract_fabric_tags(tags, title)),
                "image_url":   image_url,
                "product_url": f"https://{brand['domain']}/products/{p.get('handle','')}",
                "on_sale":     1 if on_sale else 0,
                "rating":      brand["rating"],
                "source":      "shopify",
            })
        return products
    except Exception as e:
        return []


# ══════════════════════════════════════════════════════════════
# SYNC ALL BRANDS
# ══════════════════════════════════════════════════════════════
def sync_all(conn):
    now = datetime.now().isoformat()
    shopify_brands = [b for b in BRANDS_REGISTRY if b["is_shopify"]]
    fallback_brands = [b for b in BRANDS_REGISTRY if not b["is_shopify"]]

    total_synced = 0

    print(f"\n[Shopify] Syncing {len(shopify_brands)} brands...")
    for b in shopify_brands:
        print(f"  -> {b['name']}...", end=" ", flush=True)
        products = fetch_shopify(b)
        if products:
            conn.execute("DELETE FROM brand_products WHERE brand_id = ?", (b["id"],))
            conn.executemany("""
                INSERT INTO brand_products
                (brand_id, brand_name, title, price, color, gender, category,
                 event_tags, fabric_tags, image_url, product_url, on_sale, rating, source, last_updated)
                VALUES (:brand_id_val,:brand_name,:title,:price,:color,:gender,:category,
                        :event_tags,:fabric_tags,:image_url,:product_url,:on_sale,:rating,:source,:last_updated)
            """, [{**p, "brand_id_val": b["id"], "last_updated": now} for p in products])
            conn.execute("INSERT INTO brand_sync_log (brand_id,sync_time,status,products_fetched) VALUES (?,?,?,?)",
                         (b["id"], now, "success", len(products)))
            conn.commit()
            print(f"[OK] {len(products)} products")
            total_synced += len(products)
        else:
            conn.execute("INSERT INTO brand_sync_log (brand_id,sync_time,status,error_msg) VALUES (?,?,?,?)",
                         (b["id"], now, "failed", "No products returned"))
            conn.commit()
            print("[!!] No data (CORS/timeout)")
        time.sleep(0.8)

    print(f"\n[Fallback] Seeding {len(fallback_brands)} non-Shopify brands...")
    for b in fallback_brands:
        nav = b.get("nav_urls", {})
        nav_url = list(nav.values())[0] if nav else f"https://{b['domain']}"
        gender_list = b.get("gender", ["women"])
        for g in gender_list:
            conn.execute("""
                INSERT OR IGNORE INTO brand_products
                (brand_id, brand_name, title, price, color, gender, category,
                 event_tags, fabric_tags, image_url, product_url, on_sale, rating, source, last_updated)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                b["id"], b["name"], f"{b['name']} - Visit Website",
                0, "multi", g, b["category"][0],
                json.dumps(b.get("speciality",[])),
                json.dumps([]),
                "", nav_url, 0, b["rating"], "fallback", now
            ))
        conn.execute("INSERT INTO brand_sync_log (brand_id,sync_time,status,products_fetched) VALUES (?,?,?,?)",
                     (b["id"], now, "seeded_fallback", len(gender_list)))
        conn.commit()
        print(f"  -> {b['name']} seeded (fallback)")

    return total_synced


# ══════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════
def print_stats(conn):
    r = lambda q: conn.execute(q).fetchone()[0]

    q_women   = "SELECT COUNT(*) FROM brand_products WHERE gender='women'"
    q_men     = "SELECT COUNT(*) FROM brand_products WHERE gender='men'"
    q_kids    = "SELECT COUNT(*) FROM brand_products WHERE gender='kids'"
    q_shoes   = "SELECT COUNT(*) FROM brand_products WHERE category='shoes'"
    q_jewelry = "SELECT COUNT(*) FROM brand_products WHERE category='jewelry'"
    q_bags    = "SELECT COUNT(*) FROM brand_products WHERE category='bags'"
    q_sale    = "SELECT COUNT(*) FROM brand_products WHERE on_sale=1"
    q_meta    = "SELECT COUNT(*) FROM brands_meta"

    print("\n" + "="*50)
    print("   DATABASE STATS")
    print("="*50)
    print(f"  Total products : {r('SELECT COUNT(*) FROM brand_products'):,}")
    print(f"  Women          : {r(q_women):,}")
    print(f"  Men            : {r(q_men):,}")
    print(f"  Kids           : {r(q_kids):,}")
    print(f"  Shoes          : {r(q_shoes):,}")
    print(f"  Jewelry        : {r(q_jewelry):,}")
    print(f"  Bags           : {r(q_bags):,}")
    print(f"  On Sale        : {r(q_sale):,}")
    print(f"  Brands meta    : {r(q_meta):,}")
    print("="*50)

    print("\n  SYNC LOG (last 10):")
    rows = conn.execute("""
        SELECT brand_id, status, products_fetched, sync_time
        FROM brand_sync_log ORDER BY id DESC LIMIT 10
    """).fetchall()
    for row in rows:
        if row[1] == "success":
            icon = "[OK]"
        elif "fallback" in row[1]:
            icon = "[FB]"
        else:
            icon = "[!!]"
        print(f"  {icon} {row[0]:<22} {row[1]:<20} {row[2]:>4} products")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 46)
    print("   GlamourBot - Database Setup Script")
    print("=" * 46)
    print()
    print(f"DB Path: {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("[1] Initializing tables...")
    init_db(conn)

    print("[2] Seeding brands metadata...")
    seed_brands_meta(conn)

    print("[3] Syncing products from Shopify...")
    total = sync_all(conn)

    print_stats(conn)
    conn.close()

    print(f"\n[DONE] brands_cache.db ready - {total} live products synced.")
    print(f"File: {DB_PATH}")
    print("\nAb app.py run :  uvicorn app:app --reload\n")