class Trip:
    def __init__(self, trip_id, capacity):
        self.id = trip_id
        self.capacity = capacity
        self.deliveries = []
        self.total_weight = 0
 
    def remaining_capacity(self):
        return self.capacity - self.total_weight
 
    def can_accept(self, delivery):
        return round(self.total_weight + delivery.weight, 9) <= self.capacity
 
    def add(self, delivery):
        if not self.can_accept(delivery):
            raise ValueError(f"Adding delivery {delivery.id} exceeds trip capacity")
        self.deliveries.append(delivery)
        self.total_weight += delivery.weight