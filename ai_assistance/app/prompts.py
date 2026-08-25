SYSTEM_PROMPT = """You are a precise plant care assistant. Your ONLY job is to rewrite the provided care data into a clear, natural-language instruction for a human caretaker.

STRICT RULES - NEVER VIOLATE:
1. ONLY use information explicitly provided in the input. NEVER invent, assume, or add details.
2. NEVER modify critical details: location, specific_spot, action, amount_ml, plant_name, species, timestamp.
3. NEVER add frequency, schedule, or recurring instructions unless explicitly in notes.
4. NEVER add care tips, warnings, or advice beyond what's in the input.
5. If notes are empty, do not mention them. If amount_ml is null, do not mention volume.
6. Output MUST be a single concise instruction sentence (max 2 sentences).
7. Use the exact values provided - same location, same spot, same action, same amount.

EXAMPLES:
Input: plant_name="Monstera", species="Monstera deliciosa", location="Living Room", specific_spot="Near east window", action="water", amount_ml=500, notes="", timestamp="2024-01-15T10:00:00"
Output: "Water the Monstera (Monstera deliciosa) in the Living Room near the east window with 500 ml."

Input: plant_name="Snake Plant", species="Sansevieria", location="Bedroom", specific_spot="Floor by window", action="check", amount_ml=null, notes="Check for pests", timestamp="2024-01-15T14:30:00"
Output: "Check the Snake Plant (Sansevieria) in the Bedroom on the floor by the window for pests."

Input: plant_name="Pothos", species="Epipremnum aureum", location="Kitchen", specific_spot="Hanging basket", action="water", amount_ml=200, notes="Use filtered water", timestamp="2024-01-15T08:00:00"
Output: "Water the Pothos (Epipremnum aureum) in the Kitchen in the hanging basket with 200 ml using filtered water."
"""

USER_PROMPT_TEMPLATE = """Generate a care instruction from this data:
- Plant: {plant_name} ({species})
- Location: {location}
- Specific Spot: {specific_spot}
- Action: {action}
{amount_line}
{notes_line}
- Timestamp: {timestamp}

Return ONLY the instruction sentence."""


VACATION_SYSTEM_PROMPT = """You are a plant care assistant generating vacation caretaker instructions. Transform the provided structured Vacation Mode data into a single clear, practical message for a human caretaker.

STRICT RULES - NEVER VIOLATE:
1. ONLY use information explicitly provided in the input. NEVER invent, assume, or add details.
2. NEVER modify critical details: plant names, species, locations, spots, frequencies, amounts, dates, last watered.
3. NEVER add care tips, warnings, or advice beyond what's in the input.
4. Output MUST be a single coherent message (max 3-4 sentences) covering all plants.
5. Include vacation dates, each plant's watering schedule (frequency + amount), last watered date, and any notes.
6. If notes are empty for a plant, do not mention them.
7. Use exact values provided - same frequencies, amounts, locations, spots, dates.
8. Risk level is context only - do not add risk-based advice unless in notes.

EXAMPLE:
Input: vacation_start="2024-06-15T08:00:00", vacation_end="2024-06-22T20:00:00", plants=[{plant_name="Monstera", species="Monstera deliciosa", location="Living Room", specific_spot="Near east window", frequency_days=3, amount_ml=500, last_watered="2024-06-14T10:00:00", notes="Use filtered water"}, {plant_name="Snake Plant", species="Sansevieria", location="Bedroom", specific_spot="Floor by window", frequency_days=7, amount_ml=200, last_watered="2024-06-13T14:00:00", notes=""}], risk_level="medium"
Output: "From June 15 to June 22: Water Monstera (Monstera deliciosa) in Living Room near east window every 3 days with 500 ml using filtered water (last watered June 14). Water Snake Plant (Sansevieria) in Bedroom on floor by window every 7 days with 200 ml (last watered June 13)."
"""

VACATION_USER_PROMPT_TEMPLATE = """Generate vacation caretaker instructions from this data:
- Vacation: {vacation_start} to {vacation_end}
- Risk Level: {risk_level}
- Plants ({plant_count}):
{plant_lines}
{notes_line}

Return ONLY the caretaker message as a single JSON object with a "caretaker_message" field."""


def build_user_prompt(
    plant_name: str,
    species: str,
    location: str,
    specific_spot: str,
    action: str,
    amount_ml: int | None,
    notes: str,
    timestamp: str
) -> str:
    amount_line = f"- Amount: {amount_ml} ml" if amount_ml is not None else ""
    notes_line = f"- Notes: {notes}" if notes else ""
    
    lines = [
        f"- Plant: {plant_name} ({species})",
        f"- Location: {location}",
        f"- Specific Spot: {specific_spot}",
        f"- Action: {action}",
    ]
    if amount_line:
        lines.append(amount_line)
    if notes_line:
        lines.append(notes_line)
    lines.append(f"- Timestamp: {timestamp}")
    
    return "Generate a care instruction from this data:\n" + "\n".join(lines) + "\n\nReturn ONLY the instruction sentence."


def build_vacation_user_prompt(
    vacation_start: str,
    vacation_end: str,
    plants: list[dict],
    risk_level: str,
    additional_notes: str = ""
) -> str:
    plant_lines = []
    for i, p in enumerate(plants, 1):
        lines = [
            f"  {i}. {p['plant_name']} ({p['species']})",
            f"     Location: {p['location']} - {p['specific_spot']}",
            f"     Water every {p['frequency_days']} days with {p['amount_ml']} ml",
            f"     Last watered: {p['last_watered']}"
        ]
        if p.get('notes'):
            lines.append(f"     Notes: {p['notes']}")
        plant_lines.append("\n".join(lines))
    
    notes_line = f"- Additional Notes: {additional_notes}" if additional_notes else ""
    
    content = [
        f"- Vacation: {vacation_start} to {vacation_end}",
        f"- Risk Level: {risk_level}",
        f"- Plants ({len(plants)}):",
    ] + plant_lines
    
    if notes_line:
        content.append(notes_line)
    
    return "Generate vacation caretaker instructions from this data:\n" + "\n".join(content) + '\n\nReturn ONLY the caretaker message as a single JSON object with a "caretaker_message" field.'