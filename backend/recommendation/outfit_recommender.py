def recommend_outfit(body_type, weather, occasion):
    recommendations = []

    if body_type == "slim":
        recommendations.append("Slim-fit blazer")
    else:
        recommendations.append("Regular-fit shirt")

    if weather == "cold":
        recommendations.append("Jacket or Coat")
    else:
        recommendations.append("Light cotton wear")

    if occasion == "formal":
        recommendations.append("Formal trousers and leather shoes")
    else:
        recommendations.append("Casual jeans and sneakers")

    return {
        "body_type": body_type,
        "weather": weather,
        "occasion": occasion,
        "recommendations": recommendations
    }
