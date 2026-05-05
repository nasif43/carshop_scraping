from config import IMPEL_CDN_PREFIX, ALGOLIA_IMAGE_CDN_PREFIX

def parse_algolia_hit(hit):
    car_name = " ".join(filter(None, [
        str(hit.get("make_year", "")),
        hit.get("make", ""),
        hit.get("model", ""),
        hit.get("car_trim", "")
    ])).strip()

    images = hit.get("images", [])
    first_image_key = images[0] if images else None
    first_image_url = None
    # Only construct URL if Algolia CDN prefix is known
    if first_image_key and ALGOLIA_IMAGE_CDN_PREFIX:
        first_image_url = f"{ALGOLIA_IMAGE_CDN_PREFIX}/{first_image_key}"

    return {
        "vin": hit.get("vin"),
        "car_name": car_name,
        "make": hit.get("make"),
        "model": hit.get("model"),
        "year": hit.get("make_year"),
        "trim": hit.get("car_trim"),
        "price": hit.get("price"),
        "mileage": hit.get("odometer"),
        "first_image_key": first_image_key,
        "first_image_url": first_image_url,
        "engine": hit.get("engine"),
        "transmission": hit.get("transmission"),
        "drivetrain": hit.get("drivetrain"),
        "fuel_type": hit.get("fuel_type"),
        "city_mpg": hit.get("city_mpg"),
        "highway_mpg": hit.get("highway_mpg"),
        "exterior_color": hit.get("exterior_color"),
        "interior_color": hit.get("interior_color"),
        "parsed_features": hit.get("parsed_features", []),
        "features_raw": hit.get("features"),
        "dealership": hit.get("dealership"),
        "stock_number": hit.get("stock_number"),
        "is_cpo": hit.get("cpo"),
        "impel_enabled": hit.get("impel_enabled"),
        "has_vehicle_details": hit.get("has_vehicle_details"),
    }

def parse_impel_details(impel_data):
    if not impel_data:
        return {}

    result = {
        "impel_has_details": True,
    }

    # Handle vehicle_details if present (user-reported structure)
    vehicle_details = impel_data.get("vehicle_details", {})
    if vehicle_details:
        result.update({
            "engine_details": vehicle_details.get("engine_details", {}),
            "standard_specifications": vehicle_details.get("standard_specifications", {}),
            "standard_generic_equipments": vehicle_details.get("standard_generic_equipments", {}),
            "epa_fuel_efficiency": vehicle_details.get("epa_fuel_efficiency_details", {}),
            "safety_details": vehicle_details.get("safety_details", []),
            "convenience_details": vehicle_details.get("convenience_details", []),
            "warranty_details": vehicle_details.get("warranty_details", []),
            "options_and_packages": vehicle_details.get("options_and_packages", []),
        })

    # Handle actual API response structure
    cdn_image_prefix = impel_data.get("cdn_image_prefix")
    if cdn_image_prefix and isinstance(cdn_image_prefix, str) and cdn_image_prefix.startswith("//"):
        cdn_image_prefix = "https:" + cdn_image_prefix
    result["cdn_image_prefix"] = cdn_image_prefix

    thumb = impel_data.get("thumb")
    if thumb and isinstance(thumb, str):
        if thumb.startswith("//"):
            thumb = "https:" + thumb
        result["impel_thumb"] = thumb
        result["first_image_url"] = thumb  # Use Impel thumb as image URL

    result["s3_folder"] = impel_data.get("s3_folder", "")
    result["s3_prefix"] = impel_data.get("s3_prefix", "")
    result["spin_placeholder"] = impel_data.get("spin_placeholder", {})
    result["wa_products"] = impel_data.get("wa_products", {})

    # Extract feature hotspots if available
    info = impel_data.get("info", {})
    options = info.get("options", {})
    hotspots = options.get("closeup_tags", {})
    result["impel_hotspots"] = hotspots

    return result


def parse_vehicle_details(ridemotive_data):
    if not ridemotive_data or "vehicle_details" not in ridemotive_data:
        return {}

    vehicle_details = ridemotive_data.get("vehicle_details", {})
    if not vehicle_details:
        return {}

    result = {
        "ridemotive_has_details": True,
        "vehicle_id_ridemotive": vehicle_details.get("vehicle_id"),
    }

    # Engine details
    engine_details = vehicle_details.get("engine_details", {})
    if engine_details:
        result["engine_details"] = {
            "name": engine_details.get("name"),
            "ice_cylinders": engine_details.get("ice_cylinders"),
            "ice_displacement": engine_details.get("ice_displacement"),
            "ice_max_hp": engine_details.get("ice_max_hp"),
            "ice_max_torque": engine_details.get("ice_max_torque"),
            "ice_aspiration": engine_details.get("ice_aspiration"),
            "fuel_type": engine_details.get("fuel_type"),
            "ice_compression": engine_details.get("ice_compression"),
            "oil_capacity": engine_details.get("oil_capacity"),
        }

    # Standard specifications
    std_specs = vehicle_details.get("standard_specifications", {})
    if std_specs:
        result["standard_specifications"] = std_specs

    # Standard generic equipments
    std_equip = vehicle_details.get("standard_generic_equipments", {})
    if std_equip:
        result["standard_generic_equipments"] = std_equip

    # EPA fuel efficiency
    epa = vehicle_details.get("epa_fuel_efficiency_details", {})
    if epa:
        result["epa_fuel_efficiency"] = {
            "city": epa.get("city"),
            "highway": epa.get("highway"),
            "combined": epa.get("combined"),
            "fuel_grade": epa.get("fuel_grade"),
        }

    return result

def merge_vehicle_data(algolia_data, impel_data=None, ridemotive_data=None):
    merged = algolia_data.copy()
    if impel_data:
        merged.update(impel_data)
    if ridemotive_data:
        merged.update(ridemotive_data)
    return merged
