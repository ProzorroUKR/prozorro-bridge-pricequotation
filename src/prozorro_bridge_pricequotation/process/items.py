requirement_keys = ("minValue", "maxValue", "expectedValue")


async def get_tender_items(tender: dict, profile: dict) -> list:
    items = []

    for item in tender["items"]:
        if "additionalClassifications" in profile.get("data"):
            item["additionalClassifications"] = profile.get("data", {}).get("additionalClassifications")
        unit = profile.get("data", {}).get("unit")
        classification = profile.get("data", {}).get("classification")
        item.update({"unit": unit, "classification": classification})
        items.append(item)

    return items
