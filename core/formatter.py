
def format_output(trips, invalid_deliveries):
    if not trips and not invalid_deliveries:
        print("No deliveries to process.")
    elif not trips:
        print("No valid deliveries to process.")
    else:
        for trip in trips:
            print(f"Trip {trip.id} - {trip.total_weight}/{trip.capacity}kg")
            for d in trip.deliveries:
                print(f"  - #{d.id} {d.area}, priority {d.priority}, {d.weight}kg")
        print()
        print(f"Total trips: {len(trips)}")

        total_utilization = sum(t.total_weight for t in trips)
        total_capacity = sum(t.capacity for t in trips)
        print(f"Average utilization: {total_utilization}/{total_capacity}kg "
              f"({100 * total_utilization / total_capacity:.1f}%)")

    if invalid_deliveries:
        print()
        print("Rejected deliveries:")
        for raw, reason in invalid_deliveries:
            print(f"  - {raw} -> {reason}")