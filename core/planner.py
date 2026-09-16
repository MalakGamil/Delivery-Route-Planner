from models.trip import Trip

def plan(deliveries, capacity):
    sorted_deliveries = sorted(deliveries, key=lambda d: (d.priority, d.id))
    trips = []
    next_trip_id = 1

    for delivery in sorted_deliveries:
        trip = find_best_fit_same_area(trips, delivery)
        if trip is None:
            trip = find_best_fit_any_area(trips, delivery)
        if trip is None:
            trip = Trip(next_trip_id, capacity)
            next_trip_id += 1
            trips.append(trip)
        trip.add(delivery)
    return trips

def find_best_fit_same_area(trips, delivery):
    best_trip = None
    best_remaining_after = None
    for trip in trips:
        same_area = any(d.area == delivery.area for d in trip.deliveries)
        if not same_area:
            continue
        if not trip.can_accept(delivery):
            continue
        
        remaining_after = trip.remaining_capacity() - delivery.weight
        if best_remaining_after is None or remaining_after < best_remaining_after:
            best_remaining_after = remaining_after
            best_trip = trip
    return best_trip

def find_best_fit_any_area(trips, delivery):
    best_trip = None
    best_remaining_after = None
    for trip in trips:
        if not trip.can_accept(delivery):
            continue
        remaining_after = trip.remaining_capacity() - delivery.weight
        if best_remaining_after is None or remaining_after < best_remaining_after:
            best_remaining_after = remaining_after
            best_trip = trip

    return best_trip