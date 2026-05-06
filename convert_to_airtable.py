import json
import argparse
import sys
import csv

def flatten_record(record):
    output = {}

    # 1. Core Identity
    output["car_name"] = record.get("car_name")
    output["vin"] = record.get("vin")
    output["make"] = record.get("make")
    output["model"] = record.get("model")
    output["year"] = record.get("year")
    output["trim"] = record.get("trim")
    output["stock_number"] = record.get("stock_number")
    output["is_cpo"] = record.get("is_cpo", False)

    # 2. Pricing/Mileage
    output["price"] = record.get("price")
    output["mileage"] = record.get("mileage")

    # 3. Media
    output["first_image_url"] = record.get("first_image_url")
    output["impel_thumb_url"] = record.get("impel_thumb")

    # 4. Core Specs (Disambiguated)
    output["engine_description"] = record.get("engine")
    output["transmission"] = record.get("transmission")
    output["drivetrain"] = record.get("drivetrain")
    output["algolia_city_mpg"] = record.get("city_mpg")
    output["algolia_highway_mpg"] = record.get("highway_mpg")
    output["fuel_type"] = record.get("fuel_type")
    output["exterior_color"] = record.get("exterior_color")
    output["interior_color"] = record.get("interior_color")

    # 5. Features (Flatten array to string)
    parsed_features = record.get("parsed_features", [])
    output["features"] = ", ".join(parsed_features) if parsed_features else ""

    # 6. Extended Specs (Flatten nested objects)
    # Engine details
    engine_details = record.get("engine_details", {})
    output["engine_cylinders"] = engine_details.get("ice_cylinders")
    output["engine_displacement"] = engine_details.get("ice_displacement")
    output["engine_hp"] = engine_details.get("ice_max_hp")
    output["engine_torque"] = engine_details.get("ice_max_torque")
    output["engine_aspiration"] = engine_details.get("ice_aspiration")
    output["engine_compression"] = engine_details.get("ice_compression")
    output["engine_oil_capacity"] = engine_details.get("oil_capacity")

    # EPA efficiency
    epa = record.get("epa_fuel_efficiency", {})
    output["epa_city_mpg"] = epa.get("city")
    output["epa_highway_mpg"] = epa.get("highway")
    output["epa_combined_mpg"] = epa.get("combined")
    output["epa_fuel_grade"] = epa.get("fuel_grade")

    # Standard specifications (flatten dict to string)
    std_specs = record.get("standard_specifications", {})
    output["standard_specs"] = ", ".join([f"{k}: {v}" for k, v in std_specs.items()]) if std_specs else ""

    # Safety features (flatten array to string)
    safety = record.get("safety_details", [])
    output["safety_features"] = ", ".join(safety) if safety else ""

    # 7. Dealership
    output["dealership"] = record.get("dealership")

    return output

def main():
    parser = argparse.ArgumentParser(description="Convert scraped JSONL to Airtable-friendly CSV format")
    parser.add_argument("--input", default="carshop_inventory.jsonl", help="Input JSONL file path")
    parser.add_argument("--output", default="carshop_inventory_airtable.csv", help="Output CSV file path (Airtable-compatible)")
    args = parser.parse_args()

    records = []
    processed = 0
    errors = 0

    # Read and process all input records
    with open(args.input, "r", encoding="utf-8") as infile:
        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                flattened = flatten_record(record)
                records.append(flattened)
                processed += 1
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}", file=sys.stderr)
                errors += 1
            except Exception as e:
                print(f"Error processing line {line_num}: {e}", file=sys.stderr)
                errors += 1

    if not records:
        print("No records to write.")
        return

    # Define CSV fieldnames in logical order
    fieldnames = [
        # Core Identity
        "car_name", "vin", "make", "model", "year", "trim", "stock_number", "is_cpo",
        # Pricing/Mileage
        "price", "mileage",
        # Media
        "first_image_url", "impel_thumb_url",
        # Core Specs
        "engine_description", "transmission", "drivetrain", "algolia_city_mpg", "algolia_highway_mpg", "fuel_type", "exterior_color", "interior_color",
        # Features
        "features",
        # Extended Specs
        "engine_cylinders", "engine_displacement", "engine_hp", "engine_torque", "engine_aspiration", "engine_compression", "engine_oil_capacity",
        "epa_city_mpg", "epa_highway_mpg", "epa_combined_mpg", "epa_fuel_grade", "standard_specs", "safety_features",
        # Dealership
        "dealership"
    ]

    # Write output as CSV (Airtable-compatible)
    with open(args.output, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(records)

    print(f"Conversion complete: {processed} records processed, {errors} errors")
    print(f"Output saved to: {args.output}")

if __name__ == "__main__":
    main()
