import uuid
from datetime import datetime, timezone
from typing import Optional
from .schemas import VacationModeRequest, VacationModeResponse, RiskLevel
from .ai_client import AIAssistanceClient


class VacationService:
    def __init__(self, ai_client: Optional[AIAssistanceClient] = None):
        self.ai_client = ai_client or AIAssistanceClient()

    def create_vacation_plan(self, request: VacationModeRequest) -> VacationModeResponse:
        return VacationModeResponse(
            vacation_id=str(uuid.uuid4())[:8],
            vacation_start=request.vacation_start,
            vacation_end=request.vacation_end,
            plant_count=len(request.plants),
            risk_level=request.risk_level,
            watering_schedule=request.plants,
            caretaker_message=None,
            created_at=datetime.now(timezone.utc)
        )

    async def generate_full_plan(self, request: VacationModeRequest) -> VacationModeResponse:
        response = self.create_vacation_plan(request)
        caretaker_message = await self.ai_client.generate_caretaker_message(request)
        response.caretaker_message = caretaker_message or self._fallback_message(request)
        return response

    def _fallback_message(self, request: VacationModeRequest) -> str:
        start = request.vacation_start.strftime("%B %d")
        end = request.vacation_end.strftime("%B %d")
        parts = [f"From {start} to {end}:"]
        if request.season and request.season_factor:
            change = round(abs(request.season_factor - 1) * 100)
            direction = "less often" if request.season_factor > 1 else "more often"
            parts.append(f"{request.season} adjustments apply: water about {change}% {direction}.")
        for plant in request.plants:
            parts.append(
                f"Water {plant.plant_name} ({plant.species}) in {plant.location} "
                f"at {plant.specific_spot} every {plant.frequency_days} days with "
                f"{plant.amount_ml} ml."
            )
            if plant.pet_safety in {"mild", "toxic"}:
                parts.append(
                    f"Wear gloves when handling {plant.plant_name} and wash hands afterward; "
                    "keep it away from pets."
                )
        return " ".join(parts)


_vacation_service: Optional[VacationService] = None


def get_vacation_service() -> VacationService:
    global _vacation_service
    if _vacation_service is None:
        _vacation_service = VacationService()
    return _vacation_service
