from models.trip import Trip

def plan(deliveries, capacity):
    sorted_deliveries = sorted(deliveries, key=lambda d: (d.priority, d.area, d.id))
    trips = []
    area_index = {}
    next_trip_id = 1

    for delivery in sorted_deliveries:
        candidate_trips = area_index.get(delivery.area, [])
        trip = find_best_fit(candidate_trips, delivery)
        if trip is None:
            trip = find_best_fit(trips, delivery)
        if trip is None:
            trip = Trip(next_trip_id, capacity)
            next_trip_id += 1
            trips.append(trip)
        trip.add(delivery)

        area_index.setdefault(delivery.area, [])
        if trip not in area_index[delivery.area]:
            area_index[delivery.area].append(trip)

    return trips

def find_best_fit(candidate_trips, delivery):
    best_trip = None
    best_remaining_after = None
    for trip in candidate_trips:
        if not trip.can_accept(delivery):
            continue
        remaining_after = trip.remaining_capacity() - delivery.weight
        if best_remaining_after is None or remaining_after < best_remaining_after:
            best_remaining_after = remaining_after
            best_trip = trip
    return best_trip