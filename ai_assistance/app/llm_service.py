import os
import json
from typing import Optional
from groq import Groq
from .schemas import (
    CareInstructionRequest,
    CareInstructionResponse,
    CareAction,
    VacationCareRequest,
    VacationCareResponse,
    WateringScheduleItem
)
from .prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    VACATION_SYSTEM_PROMPT,
    build_vacation_user_prompt
)


class GroqLLMService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=self.api_key)
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def generate_instruction(self, request: CareInstructionRequest) -> CareInstructionResponse:
        user_prompt = build_user_prompt(
            plant_name=request.plant_name,
            species=request.species,
            location=request.location,
            specific_spot=request.specific_spot,
            action=request.action.value,
            amount_ml=request.amount_ml,
            notes=request.notes or "",
            timestamp=request.timestamp.isoformat()
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt + "\n\nReturn valid JSON with an 'instruction' field."}
            ],
            temperature=0.1,
            max_tokens=150,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        
        try:
            parsed = json.loads(content)
            instruction = parsed.get("instruction", "").strip()
            if not instruction:
                raise ValueError("Empty instruction")
        except (json.JSONDecodeError, AttributeError, ValueError):
            instruction = self._fallback_instruction(request)

        return CareInstructionResponse(
            instruction=instruction,
            plant_name=request.plant_name,
            species=request.species,
            location=request.location,
            specific_spot=request.specific_spot,
            action=request.action,
            amount_ml=request.amount_ml,
            notes=request.notes,
            timestamp=request.timestamp
        )

    def generate_vacation_care(self, request: VacationCareRequest) -> VacationCareResponse:
        plants_data = [
            {
                "plant_name": p.plant_name,
                "species": p.species,
                "location": p.location,
                "specific_spot": p.specific_spot,
                "frequency_days": p.frequency_days,
                "amount_ml": p.amount_ml,
                "last_watered": p.last_watered.isoformat(),
                "notes": p.notes or "",
                "base_frequency_days": p.base_frequency_days,
                "pet_safety": p.pet_safety,
                "toxic_cats": p.toxic_cats,
                "toxic_dogs": p.toxic_dogs,
                "placement_tip": p.placement_tip,
            }
            for p in request.plants
        ]

        user_prompt = build_vacation_user_prompt(
            vacation_start=request.vacation_start.isoformat(),
            vacation_end=request.vacation_end.isoformat(),
            plants=plants_data,
            risk_level=request.risk_level,
            additional_notes=request.additional_notes or "",
            season=request.season,
            season_factor=request.season_factor,
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": VACATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        try:
            parsed = json.loads(content)
            caretaker_message = parsed.get("caretaker_message", "").strip()
            if not caretaker_message:
                raise ValueError("Empty caretaker_message")
        except (json.JSONDecodeError, AttributeError, ValueError):
            caretaker_message = self._fallback_vacation_message(request)

        return VacationCareResponse(
            caretaker_message=caretaker_message,
            vacation_start=request.vacation_start,
            vacation_end=request.vacation_end,
            plant_count=len(request.plants),
            risk_level=request.risk_level
        )

    def _fallback_instruction(self, request: CareInstructionRequest) -> str:
        parts = [
            f"{request.action.value.capitalize()} the {request.plant_name} ({request.species})",
            f"in the {request.location} at the {request.specific_spot}"
        ]
        if request.amount_ml is not None:
            parts.append(f"with {request.amount_ml} ml")
        if request.notes:
            parts.append(request.notes)
        return " ".join(parts) + "."

    def _fallback_vacation_message(self, request: VacationCareRequest) -> str:
        start = request.vacation_start.strftime("%B %d")
        end = request.vacation_end.strftime("%B %d")
        parts = [f"From {start} to {end}:"]
        if request.season and request.season_factor:
            change = round(abs(request.season_factor - 1) * 100)
            direction = "less often" if request.season_factor > 1 else "more often"
            parts.append(f"{request.season} adjustments apply: water about {change}% {direction}.")
        
        for p in request.plants:
            plant_parts = [
                f"Water {p.plant_name} ({p.species}) in {p.location} at {p.specific_spot}",
                f"every {p.frequency_days} days with {p.amount_ml} ml",
                f"(last watered {p.last_watered.strftime('%B %d')})"
            ]
            if p.notes:
                plant_parts.append(p.notes)
            parts.append(" ".join(plant_parts) + ".")
            if p.pet_safety in {"mild", "toxic"}:
                parts.append(
                    f"Wear gloves when handling {p.plant_name}, wash hands afterward, "
                    "and keep it away from pets."
                )
        
        return " ".join(parts)


_llm_service: Optional[GroqLLMService] = None


def get_llm_service() -> GroqLLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = GroqLLMService()
    return _llm_service
