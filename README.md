# Delivery Route Planner

A command-line program that reads delivery requests from a JSON file and organizes them into vehicle trips, respecting capacity limits, priority ordering, and area grouping.

---

## How to Run

```bash
python main.py deliveries.json
python main.py deliveries.json 15
```

- First argument: path to the JSON input file
- Second argument (optional): vehicle capacity in kg defaults to 10

---

## Input Format

```json
{
  "deliveries": [
    {"id": 1, "area": "Maadi", "priority": 1, "weight": 2.0},
    {"id": 2, "area": "Zamalek", "priority": 2, "weight": 5.5}
  ]
}
```

Each delivery needs four fields:
- `id` — unique positive integer
- `area` — non-empty string, case-insensitive ("Maadi" and "maadi" are the same)
- `priority` — positive integer, lower means more urgent
- `weight` — positive number, can't exceed vehicle capacity

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

The program runs in four stages: parsing, validation, planning, and formatting. Each stage does one thing and doesn't know about the others. This isn't a formal pattern the task doesn't need that level of structure but the split means if I change the input format, I only touch the parser, and if I change how results look, I only touch the formatter. The planner never sees a JSON line or a print statement. This is the Open/Closed principle in practice: the planner is closed to changes in how data arrives or how results are shown, but open to a different planning strategy if needed later.

I used classes for `Delivery` and `Trip` because they have something real to own. `Delivery` just holds the four fields. `Trip` owns the capacity logic `can_accept()` and `add()` live there, not in the planner. The planner never does weight arithmetic directly; it asks the trip "can you take this?" and the trip answers. That's Single Responsibility: one class, one reason to change. If the capacity rule changes, there's one place to fix it.

The planner is a plain function because it has no state between calls  making it a class would just be adding noise.

For the planning itself: sort by priority first, then area name, then id. The area in the middle is the key decision when two deliveries share the same priority, putting area before id means same-area deliveries end up next to each other after sorting, which improves grouping without extra logic. The id at the end keeps the output deterministic.

From there it's a greedy pass. For each delivery, I first look for a trip already serving the same area that still has room using a dict that maps each area to its trips, so I don't scan everything. If no same-area trip works, I fall back to any trip with room and pick the one that will be most full after adding this delivery. If nothing fits, I open a new trip.

---

### 2. What was the most difficult part?

Priority ordering and area grouping pull against each other, and there's no way to always satisfy both.

If I sort strictly by priority, same-area deliveries get separated whenever a higher-priority delivery from a different area falls between them. If I group by area first, I might process a lower-priority delivery before a higher-priority one from somewhere else.

I decided priority comes first because urgency is the harder requirement. Area grouping is a preference, not a constraint. But I wanted to recover as much grouping as possible, so I added area as a tiebreaker in the sort: when two deliveries share the same priority, they're ordered by area name, which naturally clusters same-area deliveries together without touching the planning logic.

The other challenge was keeping the search efficient. Scanning every trip for every delivery gets slow when there are many trips. The area index fixes same-area lookup, and best-fit keeps trips as full as possible so fewer get opened overall.

---

### 3. Are there situations where your algorithm may not produce the best possible grouping?



**Same area split across priorities:**

```
ID2:  Maadi,   priority 1, weight 2.0
ID4:  Zamalek, priority 1, weight 7.0
ID14: Zamalek, priority 2, weight 3.0
```

After sorting by (priority, area, id): ID2 Maadi → ID4 Zamalek → ID14 Zamalek.

ID4 goes into the only open trip (2kg used), filling it to 9kg. When ID14 arrives, that trip is too full. Result: two Zamalek deliveries in different trips even though 7+3=10kg fits perfectly in one.

To fix this I'd need to delay ID4 until I know ID14 is coming which means processing a priority-2 delivery before a priority-1 one. That's not a trade-off I'm willing to make.

**Capacity prevents grouping:**

```
ID1: Maadi, priority 1, weight 6.0
ID2: Maadi, priority 1, weight 6.0
```

Same area, same priority, but 6+6=12kg doesn't fit in one trip. This isn't the algorithm's fault — the hard constraint is what separates them. I mention it because it's easy to look at the output and think the grouping broke, when really the capacity just didn't allow it.

**Fallback mixes areas when it doesn't have to:**

When no same-area trip fits, the fallback puts the delivery in any trip with room — even if opening a new trip would give better grouping later. This reduces the total number of trips but can put two different areas together when there was no real need to. I decided efficiency matters more here, but it's worth knowing it happens.

**Area tiebreaker can delay a lower-id delivery:**

When two deliveries share the same priority, the one whose area name comes first alphabetically gets processed first regardless of id. So a delivery with id=1 going to Zamalek will be processed after id=2 going to Maadi, even though id=1 came first in the input. This is a deliberate trade-off: the PDF explicitly asks for same-area grouping where reasonably possible, and the area tiebreaker supports that without extra logic.

**Greedy doesn't minimize trips:**

The algorithm never looks ahead. It makes the locally best decision at each step, which means it can open a new trip when a different ordering might have avoided it. A globally optimal solution would require backtracking, which is a much harder problem and not what the task is asking for.

---

### 4. If the input contained 1,000,000 delivery requests, what part of your solution might become slow or memory-intensive?

Two things would hurt at that scale.

The first is memory. The program loads the entire JSON file before doing anything. A million delivery objects in memory at once is expensive. The fix is streaming read and process one delivery at a time but that conflicts with sorting, since you can't sort a stream without buffering it. So at scale, sorting and memory become a linked problem.

The second is the fallback search. The area index gives same-area lookups cheaply, but when no same-area trip fits, I scan every open trip to find the best one. In the worst case a million deliveries all going to different areas the number of open trips grows with n and scanning all of them for each delivery pushes complexity toward O(n²).

The right fix is a data structure that keeps trips sorted by remaining capacity and supports finding the first trip that fits a given weight in O(log t) instead of O(t). Python's `sortedcontainers.SortedList` does this and would bring the worst case down to O(n log n). I left it out because the current scale doesn't need it and it adds an external dependency, but it's the obvious next step.

---

### 5. What would you improve if you had another day?

The `SortedList` for the fallback search is the biggest algorithmic improvement available.

After that, streaming input to reduce peak memory, even if sorting still needs buffering.

Then more targeted tests for the planning logic itself — specifically the cases where priority and area conflict — rather than relying only on end-to-end runs.

---

## Edge Cases and Decisions

These are the cases the program handles and why each decision was made.

**No deliveries:**
Print a message and exit cleanly. It's valid input, just empty.

**Package heavier than capacity:**
Reject it and report it, but keep processing the rest. One bad delivery shouldn't stop everything else.

**Weight exactly equal to capacity:**
Valid. The rule is `<=` not `<`. Worth mentioning because it's easy to write the wrong comparison.

**Adding next package would exceed capacity:**
Don't reject the delivery find another trip with room, or open a new one. The delivery is valid; it just doesn't fit here.

**Multiple deliveries with the same priority:**
Sort by area name first, then id. Area grouping is an explicit requirement, and putting it before id means same-area deliveries cluster together naturally. The id keeps the result deterministic when areas also match.



**Missing id:**
Reject it. Can't track a delivery without an identifier.

**Duplicate id:**
Reject the second one, keep the first. An id is supposed to be unique if there's a duplicate, we don't know which one is right, so we take the first and report the rest.

**Id is not a positive integer:**
Reject it. A float like 1.5 or a boolean like True technically passes an `isinstance(x, int)` check in Python because bool is a subclass of int so we check for both explicitly.

**Area is empty or missing:**
Reject it. Area is part of the grouping logic; without it the algorithm can't do its job.

**Area case sensitivity and whitespace:**
Normalize with `" ".join(area.split()).lower()`. This strips leading and trailing whitespace, collapses internal spaces ("Nasr  City" becomes "Nasr City"), and lowercases everything. Without this, a double space in the input would silently break grouping the area index would treat "Nasr  City" and "Nasr City" as different areas and put the deliveries in separate trips with no warning.

**Priority is not a positive integer:**
Reject it. Can't sort without a valid number. Priority 0 is also rejected — the PDF implies priorities start at 1, and 0 as "highest priority" would be ambiguous.

**Weight is NaN or Infinity:**
Reject it. Python's json parser accepts these as valid floats, but they're not real weights. We use `math.isfinite()` to catch them explicitly.

**Weight is zero or negative:**
Reject it. A delivery with no weight is almost certainly a data error.

**Capacity is zero or negative:**
Exit immediately at startup. There's no point processing anything with an invalid vehicle configuration.

**Missing "deliveries" key:**
Exit with a clear error. Silently returning "no deliveries" when the key is just misspelled would be confusing and hard to debug.

---

## Extension — Configurable Capacity + Trip Summary

**Configurable capacity:**

```bash
python main.py deliveries.json 15
```

Defaults to 10kg but can be changed at runtime. Hardcoding 10kg ties the planner to one vehicle type. Making it a parameter meant touching only `main.py` — the planning logic didn't change, which confirms the separation is working.

**Trip summary and output file:**

After the trips, the program prints total trips, total weight, and average capacity utilization. It also saves the full result to `output.json`. I added both because without them you'd have to count and calculate manually to know how efficiently the capacity was used and having a machine-readable output means the results can feed into another system without parsing the printed text.