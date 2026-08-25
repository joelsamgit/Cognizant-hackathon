import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from app.schemas import VacationModeRequest, VacationModeResponse, PlantWateringSchedule, RiskLevel
from app.vacation_service import VacationService
from app.ai_client import AIAssistanceClient


class TestVacationSchemas:
    def test_valid_plant_schedule(self):
        schedule = PlantWateringSchedule(
            plant_name="Monstera",
            species="Monstera deliciosa",
            location="Living Room",
            specific_spot="Near east window",
            frequency_days=3,
            amount_ml=500,
            last_watered=datetime(2024, 6, 14, 10, 0, 0),
            notes="Use filtered water"
        )
        assert schedule.plant_name == "Monstera"
        assert schedule.frequency_days == 3

    def test_valid_vacation_request(self):
        req = VacationModeRequest(
            vacation_start=datetime(2024, 6, 15, 8, 0, 0),
            vacation_end=datetime(2024, 6, 22, 20, 0, 0),
            plants=[
                PlantWateringSchedule(
                    plant_name="Monstera",
                    species="Monstera deliciosa",
                    location="Living Room",
                    specific_spot="Near east window",
                    frequency_days=3,
                    amount_ml=500,
                    last_watered=datetime(2024, 6, 14, 10, 0, 0)
                )
            ],
            risk_level=RiskLevel.MEDIUM
        )
        assert req.vacation_start == datetime(2024, 6, 15, 8, 0, 0)
        assert len(req.plants) == 1

    def test_vacation_end_before_start_raises(self):
        with pytest.raises(ValueError, match="vacation_end must be after vacation_start"):
            VacationModeRequest(
                vacation_start=datetime(2024, 6, 22, 20, 0, 0),
                vacation_end=datetime(2024, 6, 15, 8, 0, 0),
                plants=[
                    PlantWateringSchedule(
                        plant_name="Monstera",
                        species="Monstera deliciosa",
                        location="Living Room",
                        specific_spot="Near east window",
                        frequency_days=3,
                        amount_ml=500,
                        last_watered=datetime(2024, 6, 14, 10, 0, 0)
                    )
                ]
            )

    def test_empty_plants_list_raises(self):
        with pytest.raises(ValueError):
            VacationModeRequest(
                vacation_start=datetime(2024, 6, 15, 8, 0, 0),
                vacation_end=datetime(2024, 6, 22, 20, 0, 0),
                plants=[]
            )


class TestVacationService:
    @pytest.fixture
    def sample_request(self):
        return VacationModeRequest(
            vacation_start=datetime(2024, 6, 15, 8, 0, 0),
            vacation_end=datetime(2024, 6, 22, 20, 0, 0),
            plants=[
                PlantWateringSchedule(
                    plant_name="Monstera",
                    species="Monstera deliciosa",
                    location="Living Room",
                    specific_spot="Near east window",
                    frequency_days=3,
                    amount_ml=500,
                    last_watered=datetime(2024, 6, 14, 10, 0, 0)
                )
            ],
            risk_level=RiskLevel.MEDIUM
        )

    def test_create_vacation_plan(self, sample_request):
        service = VacationService()
        response = service.create_vacation_plan(sample_request)

        assert isinstance(response, VacationModeResponse)
        assert response.vacation_id is not None
        assert response.plant_count == 1
        assert response.risk_level == RiskLevel.MEDIUM
        assert response.caretaker_message is None

    @pytest.mark.asyncio
    async def test_generate_full_plan_with_ai(self, sample_request):
        service = VacationService()
        mock_ai_client = Mock()
        async def mock_generate(request):
            return "Water Monstera every 3 days with 500ml"
        mock_ai_client.generate_caretaker_message = mock_generate
        service.ai_client = mock_ai_client

        response = await service.generate_full_plan(sample_request)

        assert response.caretaker_message == "Water Monstera every 3 days with 500ml"


class TestAIAssistanceClient:
    @pytest.mark.asyncio
    async def test_generate_caretaker_message_success(self):
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"caretaker_message": "Water the plants"}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            client = AIAssistanceClient(base_url="http://test:8000")
            request = VacationModeRequest(
                vacation_start=datetime(2024, 6, 15, 8, 0, 0),
                vacation_end=datetime(2024, 6, 22, 20, 0, 0),
                plants=[
                    PlantWateringSchedule(
                        plant_name="Monstera",
                        species="Monstera deliciosa",
                        location="Living Room",
                        specific_spot="Near east window",
                        frequency_days=3,
                        amount_ml=500,
                        last_watered=datetime(2024, 6, 14, 10, 0, 0)
                    )
                ]
            )

            result = await client.generate_caretaker_message(request)
            assert result == "Water the plants"

    @pytest.mark.asyncio
    async def test_generate_caretaker_message_failure(self):
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("Connection failed")

            client = AIAssistanceClient(base_url="http://test:8000")
            request = VacationModeRequest(
                vacation_start=datetime(2024, 6, 15, 8, 0, 0),
                vacation_end=datetime(2024, 6, 22, 20, 0, 0),
                plants=[
                    PlantWateringSchedule(
                        plant_name="Monstera",
                        species="Monstera deliciosa",
                        location="Living Room",
                        specific_spot="Near east window",
                        frequency_days=3,
                        amount_ml=500,
                        last_watered=datetime(2024, 6, 14, 10, 0, 0)
                    )
                ]
            )

            result = await client.generate_caretaker_message(request)
            assert result is None