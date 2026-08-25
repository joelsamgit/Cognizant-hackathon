import uuid
from datetime import datetime
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
            created_at=datetime.utcnow()
        )

    async def generate_full_plan(self, request: VacationModeRequest) -> VacationModeResponse:
        response = self.create_vacation_plan(request)
        caretaker_message = await self.ai_client.generate_caretaker_message(request)
        response.caretaker_message = caretaker_message
        return response


_vacation_service: Optional[VacationService] = None


def get_vacation_service() -> VacationService:
    global _vacation_service
    if _vacation_service is None:
        _vacation_service = VacationService()
    return _vacation_service