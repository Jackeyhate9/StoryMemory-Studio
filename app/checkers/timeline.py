from collections import defaultdict


def find_character_location_conflicts(events: list[dict]) -> list[dict]:
    by_key = defaultdict(list)
    for event in events:
        for character in event.get("characters", []) or []:
            by_key[(event.get("story_time"), character)].append(event)
    conflicts = []
    for (story_time, character), items in by_key.items():
        locations = {x.get("location") for x in items if x.get("location")}
        if story_time and len(locations) > 1:
            conflicts.append({"story_time": story_time, "character": character, "locations": sorted(locations), "events": items})
    return conflicts

