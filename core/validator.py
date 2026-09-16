from models.delivery import Delivery


def validate(raw_deliveries, capacity):
    valid = []
    invalid = []
    seen_ids = set()

    for raw in raw_deliveries:
        delivery_id = raw.get("id")
        area = raw.get("area")
        priority = raw.get("priority")
        weight = raw.get("weight")

        if delivery_id is None:
            invalid.append((raw, "missing id"))
            continue
        if delivery_id in seen_ids:
            invalid.append((raw, f"duplicate id {delivery_id}"))
            continue

        if not area or not isinstance(area, str):
            invalid.append((raw, "missing or invalid area"))
            continue

        if not isinstance(priority, int) or priority <= 0:
            invalid.append((raw, "priority must be a positive whole number"))
            continue

        if not isinstance(weight, (int, float)) or weight <= 0:
            invalid.append((raw, "weight must be a positive number"))
            continue
        
        if weight > capacity:
            invalid.append((raw, f"weight {weight}kg exceeds vehicle capacity ({capacity}kg)"))
            continue
        
        seen_ids.add(delivery_id)
        valid.append(Delivery(delivery_id, area, priority, weight))

    return valid, invalid