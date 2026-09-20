import json

def format_output(trips, invalid_deliveries):
    output = {
        "trips": [
            {
                "trip_id": trip.id,
                "total_weight": trip.total_weight,
                "capacity": trip.capacity,
                "utilization_percent": round(100 * trip.total_weight / trip.capacity, 1),
                "deliveries": [
                    {
                        "id": d.id,
                        "area": d.area_display,
                        "priority": d.priority,
                        "weight": d.weight
                    }
                    for d in trip.deliveries
                ]
            }
            for trip in trips
        ],
        "summary": {
            "total_trips": len(trips),
            "total_weight": round(sum(t.total_weight for t in trips), 2),
            "total_capacity": round(sum(t.capacity for t in trips), 2),
            "average_utilization_percent": round(
                100 * sum(t.total_weight for t in trips) / sum(t.capacity for t in trips), 1
            ) if trips else 0
        },
        "rejected_deliveries": [
            {
                "id": raw.get("id", "?") if isinstance(raw, dict) else "?",
                "area": (raw.get("area") or "N/A") if isinstance(raw, dict) else "N/A",
                "weight": raw.get("weight", "?") if isinstance(raw, dict) else "?",
                "reason": reason
            }
            for raw, reason in invalid_deliveries
        ]
    }

    if not trips and not invalid_deliveries:
        print("No deliveries to process.")
    elif not trips:
        print("No valid deliveries to process.")
    else:
        for trip in trips:
            print(f"Trip {trip.id} - {round(trip.total_weight, 2)}/{trip.capacity}kg")
            for d in trip.deliveries:
                print(f"  - #{d.id} {d.area_display}, priority {d.priority}, {d.weight}kg")
        print()
        print(f"Total trips: {len(trips)}")
        total_w = sum(t.total_weight for t in trips)
        total_c = sum(t.capacity for t in trips)
        print(f"Average utilization: {round(total_w, 2)}/{total_c}kg "
              f"({100 * total_w / total_c:.1f}%)")

    if invalid_deliveries:
        print()
        print("Rejected deliveries:")
        for raw, reason in invalid_deliveries:
            if isinstance(raw, dict):
                area_display = raw.get("area") or "N/A"
                print(f"  - #{raw.get('id', '?')} {area_display}, "
                      f"weight {raw.get('weight', '?')}kg -> {reason}")
            else:
                print(f"  - {raw} -> {reason}")

    with open("output.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nOutput saved to output.json")