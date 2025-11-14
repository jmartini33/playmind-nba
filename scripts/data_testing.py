import json, re
p = "data/structured/0022500142_parsed.json"

with open(p) as f:
    data = json.load(f)

# What we consider FG attempts in the parsed output
def is_fg_attempt(evt):
    return any([
        evt.startswith("SHOT_"),
        evt.startswith("LAYUP_"),
        evt.startswith("DUNK_"),
        evt.startswith("3PT_"),
        evt.startswith("BLOCK_")
    ])

# Current logic replication: counts only when HoA == "AWAY"
curr = [e for e in data if e["HoA"] == "AWAY" and is_fg_attempt(e["event_type"])]

# Kings FG attempts using team field as truth
kings_fg = [e for e in data if e["team"] == "Kings" and is_fg_attempt(e["event_type"])]

print("Current counted (HoA==AWAY):", len(curr))
print("Kings FG attempts (by team):", len(kings_fg))
# Show which Kings attempts were missed by current logic
missed = [e for e in kings_fg if e not in curr]
print("Missed entries:", len(missed))
for e in missed:
    print(f'{e["period"]} {e["time"]} | {e["event_type"]} | {e["player"]} | {e["description"]}')