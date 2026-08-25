import os
import httpx
from typing import Optional
from .schemas import VacationModeRequest, VacationModeResponse


class AIAssistanceClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("AI_ASSISTANCE_URL", "http://localhost:8000")
        self.timeout = httpx.Timeout(30.0)

    async def generate_caretaker_message(self, request: VacationModeRequest) -> Optional[str]:
        plants_data = [
            {
                "plant_name": p.plant_name,
                "species": p.species,
                "location": p.location,
                "specific_spot": p.specific_spot,
                "frequency_days": p.frequency_days,
                "amount_ml": p.amount_ml,
                "last_watered": p.last_watered.isoformat(),
                "notes": p.notes or ""
            }
            for p in request.plants
        ]

        payload = {
            "vacation_start": request.vacation_start.isoformat(),
            "vacation_end": request.vacation_end.isoformat(),
            "plants": plants_data,
            "risk_level": request.risk_level.value,
            "additional_notes": request.additional_notes or ""
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/generate-vacation-care",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data.get("caretaker_message")
        except httpx.HTTPStatusError as e:
            print(f"AI Assistance service error: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"AI Assistance service unavailable: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error calling AI Assistance: {e}")
            return None