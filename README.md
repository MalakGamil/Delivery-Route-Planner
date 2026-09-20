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



**Fallback groups same-area deliveries with a different area:**

```
ID1: Maadi,   priority 1, weight 8.0
ID2: Zamalek, priority 1, weight 6.0
ID3: Maadi,   priority 2, weight 3.0
```

After sorting by (priority, area, id): Maadi(8) → Zamalek(6) → Maadi(3).

Maadi(8) opens Trip1. Zamalek(6) can't fit in Trip1, so it opens Trip2. When Maadi(3) arrives, it checks the Maadi area index Trip1 is full (8+3=11kg). The fallback finds Trip2 has room (6+3=9kg) and places it there. Result: both Maadi deliveries end up in different trips.

The same-area trip was full, but another trip had room. The fallback chose better trip utilization over keeping the delivery with its area Maadi(3) could have opened a new Trip3 instead. The algorithm prefers filling existing trips over opening new ones. That's usually the right call, but here it trades grouping quality for trip efficiency.

**Capacity prevents grouping:**

```
ID1: Maadi, priority 1, weight 6.0
ID2: Maadi, priority 1, weight 6.0
```

Same area, same priority, but 6+6=12kg doesn't fit in one trip. This isn't the algorithm's fault the hard constraint is what separates them. I mention it because it's easy to look at the output and think the grouping broke, when really the capacity just didn't allow it.

**Area tiebreaker can delay a lower-id delivery:**

When two deliveries share the same priority, the one whose area name comes first alphabetically gets processed first regardless of id. So a delivery with id=1 going to Zamalek will be processed after id=2 going to Maadi, even though id=1 came first in the input. This is a deliberate trade-off: the PDF explicitly asks for same-area grouping where reasonably possible, and the area tiebreaker supports that without extra logic.

**Greedy doesn't minimize trips:**

The algorithm never looks ahead. It makes the locally best decision at each step, which means it can open a new trip when a different ordering might have avoided it. A globally optimal solution would require backtracking, which is a much harder problem and not what the task is asking for.

**Item ordering affects packing outcomes:**

The sort fixes the processing order by (priority, area, id). This guarantees deterministic output but is not necessarily the order that minimizes wasted space. Sorting heaviest-first within the same priority would sometimes reduce the number of trips opened, because large items placed early leave smaller gaps that smaller items can fill cleanly. The current order trades that potential efficiency for predictability and simplicity.

---

### 4. If the input contained 1,000,000 delivery requests, what part of your solution might become slow or memory-intensive?

Two things would hurt at that scale.

The first is memory. The program loads the entire JSON file before doing anything. A million delivery objects in memory at once is expensive. The fix is streaming read and process one delivery at a time but that conflicts with sorting, since you can't sort a stream without buffering it. So at scale, sorting and memory become a linked problem.

The second is the fallback search. The area index gives same-area lookups cheaply, but when no same-area trip fits, I scan every open trip to find the best one. In the worst case a million deliveries all going to different areas the number of open trips grows with n and scanning all of them for each delivery pushes complexity toward O(n²).

A `SortedList` keyed by remaining capacity could reduce the cost of finding a candidate trip in the fallback. The improvement over the current O(t) scan is real, but the exact gain depends on how trips are updated after each insertion each add requires a remove and reinsert to maintain order, which adds its own cost. I left it out because the current scale doesn't need it and it adds an external dependency, but it's the obvious next step.

---

### 5. What would you improve if you had another day?

The `SortedList` for the fallback search is the biggest algorithmic improvement available.

After that, streaming input to reduce peak memory, even if sorting still needs buffering.

Then more targeted tests for the planning logic itself specifically the cases where priority and area conflict rather than relying only on end-to-end runs.

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

Normalizing is the right thing to do for grouping, but it's the wrong thing to show the user printing `nasr city` in the output looks like a bug even when the grouping is correct. So each `Delivery` keeps both: `area` is the normalized key the planner groups on, and `area_display` is the cleaned-up original ("Nasr City") that the formatter prints. The normalization only ever affects matching, never presentation.

**Priority is not a positive integer:**
Reject it. Can't sort without a valid number. Priority 0 is also rejected — the PDF implies priorities start at 1, and 0 as "highest priority" would be ambiguous.

**Weight is NaN or Infinity:**
Reject it. Python's json parser accepts these as valid floats, but they're not real weights. We use `math.isfinite()` to catch them explicitly.

**Weight is zero or negative:**
Reject it. A delivery with no weight is almost certainly a data error.

**Floating-point weights that should fill a trip exactly:**
Weights come in as floats, and floats don't add up the way decimal numbers do. `4.9 + 3.2 + 1.9` is exactly 10.0 on paper, but in binary floating point it comes out as `10.000000000000002`. A plain `total + weight <= capacity` check rejects that third package and opens a second trip for it, so a trip that should have been full at 100% ends up split across two vehicles for a rounding error of 2e-15.

This isn't a rare case. Any set of weights written with one decimal place can trigger it, and delivery weights almost always look like that. `can_accept()` rounds the sum to 9 decimal places before comparing, which absorbs the accumulated error while staying far more precise than any real scale. I chose rounding over an epsilon tolerance (`<= capacity + 1e-9`) because rounding keeps the comparison itself exact and reads more obviously as "compare these as decimal numbers." Storing weights as integer grams internally would be the fully correct fix, but it means converting on input and output everywhere, which felt like the wrong trade for this size of program.



**Capacity is zero or negative:**
Exit immediately at startup. There's no point processing anything with an invalid vehicle configuration.

**Missing "deliveries" key:**
Exit with a clear error. Silently returning "no deliveries" when the key is just misspelled would be confusing and hard to debug.

---

## Extension — Utilization Reporting (with configurable capacity)

**What it does**

```bash
python main.py deliveries.json        # default 10kg vehicle
python main.py deliveries.json 15     # 15kg vehicle
```

Every trip is reported with its load against capacity, the run ends with total trips and average utilization, and the complete result including the rejected deliveries and the reason each one was rejected is written to `output.json`.

```
Trip 2 - 9.5/10kg
  - #8 Maadi, priority 1, 6.0kg
  - #5 Maadi, priority 2, 3.5kg

Total trips: 5
Average utilization: 42.2/50kg (84.4%)
```

**Why I chose this**

The requirements contain one line that isn't a rule: deliveries should be grouped by area *"where reasonably possible."* Everything else in the task is checkable. A trip either exceeds 10kg or it doesn't. A delivery either appears exactly once or it doesn't. But "reasonably possible" is a judgment call, and the algorithm makes that call dozens of times per run every time it decides whether to squeeze a delivery into an existing trip or open a new one.

A program that prints only the trip list gives you no way to evaluate those decisions. You can see *what* it chose, but not whether the choice was any good. Utilization is the number that makes it visible: 84.4% across 5 trips says the packing is tight; the same 5 trips at 60% would say the planner is opening vehicles it doesn't need.

That number is also what let me find the real limitation documented in question 3. I could see the two Maadi deliveries land in different trips, and utilization told me it wasn't a capacity problem the trips weren't full, so the fallback had made a bad call. Without the summary I'd have been guessing at my own algorithm's behaviour rather than reading it.

Configurable capacity is part of the same idea rather than a separate feature. A single hardcoded 10kg gives you exactly one data point. Being able to re-run the same deliveries against a different vehicle size is what turns the output into something you can compare against itself, and it costs one argument in `main.py` because the planner already takes capacity as a parameter.

`output.json` exists so the results are consumable by something other than a human reading a terminal. A real planner would be one step in a pipeline, and parsing printed text is the wrong way to get data out of a program that already has it structured.

**What I deliberately left out**

Multiple vehicle types, distances between areas, and time windows are all things a real delivery planner needs, and all of them would have made this a different and much larger problem than the one that was asked. I preferred a small feature that makes the existing solution easier to judge over a large one that makes it harder to read.