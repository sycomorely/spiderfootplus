import json

def filter_data_center_locations(input_file, output_file):
    data_centers = []
    json_block = ""

    with open(input_file, 'r', encoding='utf-16') as file:  # Or utf-8-sig or utf-8
        for line in file:
            line = line.strip()
            if line.startswith("{"):
                json_block = line
            elif line.endswith("}"):
                json_block += " " + line
                try:
                    data = json.loads(json_block)
                    if data.get("status") == "success":
                        location_info = {
                            "continent": data.get("continent"),
                            "country": data.get("country"),
                            "region": data.get("region"),
                            "regionName": data.get("regionName"),
                            "city": data.get("city"),
                            "zip": data.get("zip"),
                            "lat": data.get("lat"),
                            "lon": data.get("lon"),
                            "timezone": data.get("timezone"),
                            "isp": data.get("isp"),
                            "org": data.get("org"),
                            "as": data.get("as"),
                            "query": data.get("query")
                        }
                        data_centers.append(location_info)
                except json.JSONDecodeError:
                    pass
                json_block = ""  # Clear after processing one object
            elif json_block:
                json_block += " " + line  # Continue building the JSON object

    with open(output_file, 'w', encoding='utf-8') as out_file:
        json.dump(data_centers, out_file, indent=4)

    print(f"Exported {len(data_centers)} data center locations to '{output_file}'")

# --- Run ---
input_file = 'result.json'
output_file = 'filtered_result_success.json'

filter_data_center_locations(input_file, output_file)