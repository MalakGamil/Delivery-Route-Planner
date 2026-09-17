# Delivery Route Planner

A command-line program that reads delivery requests from a JSON file and organizes them into vehicle trips, respecting capacity limits, priority ordering, and area grouping.

---

## How to Run

```bash
python main.py deliveries.json
python main.py deliveries.json 15
```

- First argument: path to the JSON input file
- Second argument (optional): vehicle capacity in kg — defaults to 10

---

## Input Format

The input must be a JSON file with the following structure:

```json
{
  "deliveries": [
    {"id": 1, "area": "Maadi", "priority": 1, "weight": 2.0},
    {"id": 2, "area": "Zamalek", "priority": 2, "weight": 5.5}
  ]
}
```

Each delivery must have:
- `id`: a unique positive integer
- `area`: a non-empty string
- `priority`: a positive integer (lower = more urgent)
- `weight`: a positive number no greater than the vehicle capacity

---

## Project Structure

```
delivery_planner/
│
├── models/
│   ├── delivery.py       # Delivery data object
│   └── trip.py           # Trip object with capacity logic
│
├── core/
│   ├── parser.py         # Reads and parses the JSON file
│   ├── validator.py      # Validates raw input into Delivery objects
│   ├── planner.py        # Groups deliveries into trips
│   └── formatter.py      # Prints results and summary
│
├── deliveries.json        # Sample input file
├── main.py               # Entry point
└── README.md
```

---

## Reasoning Questions

### 1. Explain your solution approach

The program follows a pipeline of four stages: parsing, validation, planning, and formatting. Each stage has a single responsibility and doesn't know about the others. This isn't a formal pattern implementation — the task doesn't justify that complexity — but the separation means changing the input format only affects the parser, and changing the output only affects the formatter. This maps naturally to the Open/Closed principle: the planner is open for extension (new planning strategies) but closed to changes caused by unrelated parts like input format or output style.

I used classes for `Delivery` and `Trip` because they have meaningful state and behavior. `Trip` owns its own capacity logic — `can_accept()` and `add()` live there, not in the planner. This is a deliberate application of Single Responsibility: the planner decides *which* trip a delivery goes to, and the trip decides *whether* it can accept it. If the capacity rule ever changes, there is one place to update.

The planner itself is a plain function, not a class, because it has no state to maintain between calls.

For planning, deliveries are sorted by priority ascending, with ID as a tiebreaker to guarantee deterministic output — the same input always produces the same result. Same-area trips are preferred using an area index for O(1) lookup. If no same-area trip fits, we fall back to a best-fit search over all open trips. If nothing fits, a new trip is opened.

---

### 2. What was the most difficult part?

The hardest part was balancing two conflicting requirements: processing deliveries in priority order while keeping same-area deliveries together. Satisfying both perfectly isn't always possible, so the real challenge was deciding which takes precedence and being consistent about it — and doing that without making the search expensive.

I resolved it by sorting on priority first to guarantee urgency ordering, then using an area index to find same-area trips in O(1). This way area grouping is honored whenever capacity allows, without adding a separate costly pass over the data. The tension between these two requirements is also what makes the algorithm produce suboptimal grouping in some cases, which is explained in question 3.

---

### 3. Are there situations where your algorithm may not produce the best possible grouping?

Yes. The greedy algorithm makes locally optimal decisions at each step and doesn't look ahead, so it can't always produce the best grouping.

Two cases where this happens:

**Case 1 — Same area, different priorities:**

```
ID2:  Maadi,   priority 1, weight 2.0
ID4:  Zamalek, priority 1, weight 7.0
ID14: Zamalek, priority 2, weight 3.0
```

After sorting, ID4 is processed before ID14. At that point the only open trip has 2kg used, so ID4 (7kg) fills it to 9kg. When ID14 arrives, that trip is too full. Result: Zamalek is split across two trips.

The better grouping would be:
```
Trip: Zamalek(7) + Zamalek(3) = 10kg
```
But the greedy algorithm can't achieve this because it would require delaying ID4 until ID14 is known — which breaks priority ordering.

**Case 2 — Area grouping broken by a mixed-area trip:**

```
ID1:  Nasr City, priority 2, weight 4.5  → placed in Trip2 with Dokki
ID3:  Nasr City, priority 3, weight 1.2  → Trip2 is full, placed in Trip5 with Zamalek
```

ID3 and ID1 are the same area but end up in different trips because by the time ID3 is processed, the trip holding ID1 is already full.

Both cases are natural consequences of greedy decision-making. A globally optimal solution would require backtracking or lookahead, which adds complexity not justified by the scope of this task.

---

### 4. If the input contained 1,000,000 delivery requests, what part of your solution might become slow or memory-intensive?

Two parts would not scale cleanly:

**Memory:** The program currently loads the entire JSON file into memory before processing anything. One million delivery objects held in memory at once would be expensive. A streaming approach — reading and processing one delivery at a time — would fix this, but it would require rethinking the sorting step since you can't sort a stream without buffering it.

**Sorting:** Sorting one million records is O(n log n), which is manageable but becomes noticeable at that scale.

**Fallback trip search:** The area index keeps same-area lookup at O(1), but the fallback search over all open trips is O(t) where t is the number of open trips. In a worst case where no deliveries share areas, t grows proportionally to n, making the overall complexity approach O(n²). Maintaining a priority queue of open trips ordered by remaining capacity would reduce each fallback lookup to O(log t).

---

### 5. What would you improve if you had another day to work on the solution?

I would focus on three things:

First, streaming input instead of loading the full file — this is the most impactful change for scalability.

Second, replacing the fallback linear search with a priority queue ordered by remaining capacity, reducing the worst-case complexity from O(n²) to O(n log n).

Third, adding more systematic unit tests that target the planner logic directly — specifically the cases where priority and area grouping conflict — rather than relying only on end-to-end runs.

---

## Extension — Configurable Capacity + Trip Summary

I added two things beyond what was required.

**Configurable capacity:**

```bash
python main.py deliveries.json 15
```

The capacity defaults to 10kg but can be set at runtime. I added this because hardcoding 10kg ties the planner to one vehicle type, and changing it would mean digging into the code. Making it a parameter required touching only `main.py` — the planning logic didn't change at all, which I think is a good sign that the separation is working.

**Trip summary in the output:**

After the trips, the program prints total trips, total weight across all trips, and average capacity utilization as a percentage. I added this because without it, you'd have to count the trips yourself and do the math manually to know how efficiently the vehicle capacity was used. It also made it easier to spot problems while testing — if utilization looked off, it usually meant the algorithm was making a bad grouping decision somewhere.

---

## Known Decisions and Limitations

- **First rejection reason wins:** if a delivery has a duplicate ID and an invalid weight, only the duplicate ID is reported.
- **Rejected deliveries don't register their ID:** if a delivery is rejected for a non-ID reason, its ID is not added to the seen-IDs set. This means a later duplicate of that ID won't be flagged as a duplicate.
- **Capacity validation happens at startup:** an invalid capacity (zero or negative) is caught in `main.py` before any processing begins.
- **Mixed-area trips are allowed:** the PDF does not prohibit trips containing multiple areas, and forcing single-area trips would waste capacity. Area grouping is a preference, not a hard constraint.
- **Priority ordering does not mean trips are single-priority:** priority determines processing order, not trip composition. A lower-priority delivery may share a trip with a higher-priority one if capacity allows.
- **Greedy, not optimal:** the algorithm does not guarantee the minimum number of trips or the best possible area grouping. It guarantees that no hard constraints are violated and that higher-priority deliveries are processed first.