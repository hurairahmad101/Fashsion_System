"""
Pakistan Fashion & Festival Knowledge Base Tools
"""

PAKISTAN_FESTIVALS = {
    "eid ul fitr": {
        "name": "Eid ul Fitr",
        "season": "End of Ramadan (varies by Islamic calendar)",
        "fashion": {
            "women": [
                "Kurta shalwar in pastel shades like mint green, baby pink, lavender",
                "Anarkali frocks with heavy embroidery (gota, zardozi, thread work)",
                "Gharara or sharara sets for a traditional look",
                "Lawn fabric for daytime, chiffon/silk for evening gatherings",
                "Dupatta styling: pinned on one shoulder or draped on head",
                "Popular colors: ivory, peach, soft gold, sage green",
                "Brands: Khaadi, Gul Ahmed, Nishat, Sana Safinaz Eid collections"
            ],
            "men": [
                "Shalwar kameez in white, cream, or pastel shades",
                "Waistcoat (waskat) adds elegance for Eid namaz",
                "Kurta with churidar pajama for a classic look",
                "Fabric: cotton lawn for comfort, silk/khaddar for premium look",
                "Khussa shoes or sandals",
                "Popular brands: Junaid Jamshed, Gul Ahmed Men, Alkaram Men"
            ],
            "accessories": ["Bangles (chooriyan)", "Earrings", "Clutch bags", "Khussa/heels", "Light perfume (attar)"],
            "tips": "Eid fashion in Pakistan is vibrant and colorful. Women often wear heavily embroidered outfits for Chaand Raat and switch to fresh, lighter outfits on Eid morning."
        }
    },
    "eid ul adha": {
        "name": "Eid ul Adha",
        "season": "Islamic month of Dhul Hijjah",
        "fashion": {
            "women": [
                "Deep, rich colors: maroon, dark green, royal blue, mustard",
                "Heavy cotton or khaddar for practicality (outdoor activities)",
                "Embroidered kurta with plain trousers",
                "Silk or semi-formal for family gatherings",
                "Avoid very light colors due to outdoor slaughter activities"
            ],
            "men": [
                "Practical shalwar kameez for morning Qurbani",
                "Classic white for Eid prayers",
                "Khaddar or cotton fabric for durability",
                "Sandals or simple shoes"
            ],
            "tips": "Eid ul Adha fashion focuses more on practicality. Rich, earthy tones are preferred."
        }
    },
    "basant": {
        "name": "Basant (Kite Festival)",
        "season": "Spring (February/March) - mainly Lahore",
        "fashion": {
            "women": [
                "Bright yellow is the SIGNATURE color of Basant",
                "Yellow shalwar kameez, lehenga, or kurta",
                "Mustard, orange, green also popular",
                "Light fabrics like lawn, chiffon, cotton",
                "Casual, playful outfits since it's an outdoor rooftop festival",
                "Flower accessories in hair"
            ],
            "men": [
                "Yellow or bright colored kurtas",
                "Casual shalwar kameez",
                "Comfortable clothes for flying kites"
            ],
            "tips": "Basant in Lahore is famous for yellow outfits. Rooftop parties call for festive yet comfortable clothes."
        }
    },
    "independence day": {
        "name": "Pakistan Independence Day (14th August)",
        "season": "14th August every year",
        "fashion": {
            "women": [
                "Green and white outfits - Pakistan's national colors",
                "White or green shalwar kameez with crescent & star embroidery",
                "Pakistani flag accessories and jewelry",
                "Casual western or eastern fusion in green/white"
            ],
            "men": [
                "White shalwar kameez (national dress)",
                "Green kurta or green-white combination",
                "Pakistani flag badges and accessories"
            ],
            "tips": "Patriotic fashion dominates. Green and white combinations are everywhere. Many wear national dress (shalwar kameez)."
        }
    },
    "wedding season": {
        "name": "Wedding Season (Shaadi)",
        "season": "October to February (peak), also April-May",
        "fashion": {
            "mehndi": [
                "Bright yellows, oranges, pinks for mehndi function",
                "Gharara or lehenga choli for bride",
                "Embroidered kurtas for guests",
                "Jewelry: jhumkas, bangles, maang tikka"
            ],
            "barat": [
                "Bride: Red or maroon bridal lehenga/gharara with heavy gold embroidery",
                "Groom: Sherwani (black, ivory, navy) with turban (sehra)",
                "Guests: Formal shalwar kameez, saree, or formal western",
                "Heavy jewelry: polki, kundan, gold sets"
            ],
            "valima": [
                "Bride: Lighter colors - pink, peach, mint, gold",
                "Groom: Light colored sherwani or shalwar kameez",
                "Guests: Semi-formal attire"
            ],
            "tips": "Pakistani weddings are multi-day events. Each function has distinct dress codes. Brands like HSY, Elan, Faraz Manan, Maria B are popular for bridal wear."
        }
    },
    "navratri": {
        "name": "Navratri (Celebrated by Hindu Pakistanis)",
        "season": "October (9 nights)",
        "fashion": {
            "women": [
                "Garba/Dandiya outfits: Chaniya choli",
        "Bright colors: red, green, yellow, blue for each night",
        "Mirror work (shisha) embroidery",
        "Traditional Sindhi/Rajasthani influenced designs"
            ],
            "tips": "Celebrated mainly in Sindh and parts of Punjab by the Hindu community."
        }
    },
    "christmas": {
        "name": "Christmas (Celebrated by Christian Pakistanis)",
        "season": "25th December",
        "fashion": {
            "women": [
                "Colorful shalwar kameez or western clothes",
                "Red and green colors popular",
                "Church-appropriate modest attire",
                "Mix of eastern and western fashion"
            ],
            "tips": "Pakistan's Christian community (mainly in Lahore, Karachi, Islamabad) celebrates with festive gatherings."
        }
    }
}

PAKISTANI_DESIGNERS = {
    "bridal": ["HSY (Hassan Sheheryar Yasin)", "Faraz Manan", "Elan by Khadijah Shah", "Maria B", "Sana Safinaz", "Asim Jofa"],
    "lawn_pret": ["Gul Ahmed", "Khaadi", "Alkaram Studio", "Nishat Linen", "Sapphire", "Zara Shahjahan"],
    "menswear": ["Junaid Jamshed", "Cambridge", "Gul Ahmed Men", "Breakout"],
    "luxury": ["Ali Xeeshan", "Nomi Ansari", "Tena Durrani", "Shamaeel Ansari"],
    "contemporary": ["Generation", "Limelight", "Ideas by Gul Ahmed", "Bonanza Satrangi"]
}

FASHION_TRENDS_PAKISTAN = {
    "current_trends": [
        "Digital print lawn with abstract patterns",
        "Pret-a-porter (ready-to-wear) rise over stitched",
        "Fusion: Eastern silhouettes with western cuts",
        "Sustainable and eco-friendly fabrics",
        "Maximalist embroidery on minimal cuts",
        "Wide-leg trousers paired with short kurtas",
        "Dupatta as a cape or belt"
    ],
    "regional_styles": {
        "lahore": "Bold colors, heavy embroidery, fashion-forward, love for lawn",
        "karachi": "More western-influenced, coastal, fast fashion, urban chic",
        "islamabad": "Conservative yet stylish, formal, sophisticated",
        "peshawar": "Traditional Pashtun dress, vibrant colors, handwoven fabrics",
        "quetta": "Balochi embroidery, mirror work, tribal patterns",
        "sindh": "Ajrak prints, sindhi caps, colorful tarkashi embroidery"
    }
}


def get_festival_fashion(festival_name: str) -> str:
    """Get fashion advice for a specific Pakistani festival"""
    festival_name_lower = festival_name.lower()
    
    # Search for matching festival
    for key, data in PAKISTAN_FESTIVALS.items():
        if key in festival_name_lower or festival_name_lower in key:
            result = f"🎉 **{data['name']}** Fashion Guide\n\n"
            result += f"📅 Season: {data['season']}\n\n"
            
            if "women" in data["fashion"]:
                result += "👗 **Women's Fashion:**\n"
                for item in data["fashion"]["women"]:
                    result += f"• {item}\n"
                result += "\n"
            
            if "men" in data["fashion"]:
                result += "👔 **Men's Fashion:**\n"
                for item in data["fashion"]["men"]:
                    result += f"• {item}\n"
                result += "\n"
            
            if "accessories" in data["fashion"]:
                result += "💎 **Accessories:** " + ", ".join(data["fashion"]["accessories"]) + "\n\n"
            
            if "tips" in data["fashion"]:
                result += f"💡 **Tip:** {data['fashion']['tips']}"
            
            return result
    
    return None


def get_designer_info(category: str = None) -> str:
    """Get information about Pakistani fashion designers"""
    if category:
        category_lower = category.lower()
        for key, designers in PAKISTANI_DESIGNERS.items():
            if key in category_lower or category_lower in key:
                return f"🎨 **Top Pakistani {key.replace('_', ' ').title()} Designers:**\n" + "\n".join([f"• {d}" for d in designers])
    
    result = "🎨 **Pakistani Fashion Designers by Category:**\n\n"
    for category, designers in PAKISTANI_DESIGNERS.items():
        result += f"**{category.replace('_', ' ').title()}:**\n"
        result += "\n".join([f"• {d}" for d in designers]) + "\n\n"
    return result


def get_fashion_trends() -> str:
    """Get current Pakistani fashion trends"""
    result = "✨ **Current Pakistani Fashion Trends:**\n\n"
    result += "**Trending Now:**\n"
    for trend in FASHION_TRENDS_PAKISTAN["current_trends"]:
        result += f"• {trend}\n"
    
    result += "\n**Regional Fashion Styles:**\n"
    for city, style in FASHION_TRENDS_PAKISTAN["regional_styles"].items():
        result += f"• **{city.title()}:** {style}\n"
    
    return result


def get_all_festivals() -> str:
    """List all Pakistani festivals and their fashion overview"""
    result = "🇵🇰 **Pakistani Festivals & Their Fashion:**\n\n"
    for key, data in PAKISTAN_FESTIVALS.items():
        result += f"🎊 **{data['name']}** ({data['season']})\n"
        if "tips" in data["fashion"]:
            result += f"   {data['fashion']['tips'][:100]}...\n\n"
    return result
