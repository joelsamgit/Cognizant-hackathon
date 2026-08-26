import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from app.schemas import (
    CareInstructionRequest,
    CareInstructionResponse,
    CareAction,
    VacationCareRequest,
    VacationCareResponse,
    WateringScheduleItem
)
from app.llm_service import GroqLLMService
from app.prompts import (
    build_user_prompt,
    SYSTEM_PROMPT,
    VACATION_SYSTEM_PROMPT,
    build_vacation_user_prompt
)


@pytest.fixture(autouse=True)
def reset_llm_service():
    """Reset the global LLM service singleton between tests."""
    import app.llm_service
    app.llm_service._llm_service = None
    yield
    app.llm_service._llm_service = None


class TestSchemas:
    def test_valid_water_request(self):
        req = CareInstructionRequest(
            plant_name="Monstera",
            species="Monstera deliciosa",
            location="Living Room",
            specific_spot="Near east window",
            action=CareAction.WATER,
            amount_ml=500,
            notes="Use filtered water",
            timestamp=datetime(2024, 1, 15, 10, 0, 0)
        )
        assert req.plant_name == "Monstera"
        assert req.action == CareAction.WATER
        assert req.amount_ml == 500

    def test_valid_check_request_no_amount(self):
        req = CareInstructionRequest(
            plant_name="Snake Plant",
            species="Sansevieria",
            location="Bedroom",
            specific_spot="Floor by window",
            action=CareAction.CHECK,
            notes="Check for pests"
        )
        assert req.amount_ml is None
        assert req.action == CareAction.CHECK

    def test_invalid_water_without_amount(self):
        with pytest.raises(ValueError, match="amount_ml is required"):
            CareInstructionRequest(
                plant_name="Monstera",
                species="Monstera deliciosa",
                location="Living Room",
                specific_spot="Near east window",
                action=CareAction.WATER
            )

    def test_invalid_check_with_amount(self):
        with pytest.raises(ValueError, match="amount_ml should not be provided"):
            CareInstructionRequest(
                plant_name="Monstera",
                species="Monstera deliciosa",
                location="Living Room",
                specific_spot="Near east window",
                action=CareAction.CHECK,
                amount_ml=100
            )

    def test_amount_validation_bounds(self):
        with pytest.raises(ValueError):
            CareInstructionRequest(
                plant_name="Monstera",
                species="Monstera deliciosa",
                location="Living Room",
                specific_spot="Near east window",
                action=CareAction.WATER,
                amount_ml=15000
            )


class TestPrompts:
    def test_build_user_prompt_with_amount_and_notes(self):
        prompt = build_user_prompt(
            plant_name="Monstera",
            species="Monstera deliciosa",
            location="Living Room",
            specific_spot="Near east window",
            action="water",
            amount_ml=500,
            notes="Use filtered water",
            timestamp="2024-01-15T10:00:00"
        )
        assert "Monstera" in prompt
        assert "500 ml" in prompt
        assert "Use filtered water" in prompt
        assert "Living Room" in prompt
        assert "Near east window" in prompt

    def test_build_user_prompt_without_amount_and_notes(self):
        prompt = build_user_prompt(
            plant_name="Snake Plant",
            species="Sansevieria",
            location="Bedroom",
            specific_spot="Floor by window",
            action="check",
            amount_ml=None,
            notes="",
            timestamp="2024-01-15T14:30:00"
        )
        assert "Snake Plant" in prompt
        assert "500 ml" not in prompt
        assert "Floor by window" in prompt
        assert "Check for pests" not in prompt

    def test_system_prompt_contains_rules(self):
        assert "NEVER VIOLATE" in SYSTEM_PROMPT
        assert "NEVER invent" in SYSTEM_PROMPT
        assert "NEVER modify critical details" in SYSTEM_PROMPT
        assert "location" in SYSTEM_PROMPT
        assert "amount_ml" in SYSTEM_PROMPT


class TestLLMService:
    @pytest.fixture
    def mock_groq_client(self):
        with patch('app.llm_service.Groq') as mock:
            yield mock

    @pytest.fixture
    def sample_request(self):
        return CareInstructionRequest(
            plant_name="Monstera",
            species="Monstera deliciosa",
            location="Living Room",
            specific_spot="Near east window",
            action=CareAction.WATER,
            amount_ml=500,
            notes="Use filtered water",
            timestamp=datetime(2024, 1, 15, 10, 0, 0)
        )

    def test_generate_instruction_success(self, mock_groq_client, sample_request):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"instruction": "Water the Monstera (Monstera deliciosa) in the Living Room near the east window with 500 ml using filtered water."}'
        mock_groq_client.return_value.chat.completions.create.return_value = mock_response

        service = GroqLLMService(api_key="test-key")
        response = service.generate_instruction(sample_request)

        assert isinstance(response, CareInstructionResponse)
        assert "Monstera" in response.instruction
        assert "500 ml" in response.instruction
        assert response.plant_name == "Monstera"
        assert response.amount_ml == 500

    def test_generate_instruction_fallback_on_json_error(self, mock_groq_client, sample_request):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Not valid JSON"
        mock_groq_client.return_value.chat.completions.create.return_value = mock_response

        service = GroqLLMService(api_key="test-key")
        response = service.generate_instruction(sample_request)

        assert isinstance(response, CareInstructionResponse)
        assert "Monstera" in response.instruction
        assert "Living Room" in response.instruction

    def test_fallback_instruction_format(self, sample_request):
        service = GroqLLMService(api_key="test-key")
        fallback = service._fallback_instruction(sample_request)

        assert "Water the Monstera" in fallback
        assert "Monstera deliciosa" in fallback
        assert "Living Room" in fallback
        assert "Near east window" in fallback
        assert "500 ml" in fallback
        assert "Use filtered water" in fallback

    def test_fallback_without_amount_or_notes(self):
        req = CareInstructionRequest(
            plant_name="Snake Plant",
            species="Sansevieria",
            location="Bedroom",
            specific_spot="Floor by window",
            action=CareAction.CHECK,
            notes="Check for pests",
            timestamp=datetime(2024, 1, 15, 14, 30, 0)
        )
        service = GroqLLMService(api_key="test-key")
        fallback = service._fallback_instruction(req)

        assert "Check the Snake Plant" in fallback
        assert "Bedroom" in fallback
        assert "Floor by window" in fallback
        assert "Check for pests" in fallback
        assert "ml" not in fallback

    def test_init_without_api_key_raises(self):
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY not found"):
                GroqLLMService()


class TestFastAPIEndpoints:
    @pytest.fixture
    def client(self):
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            with patch('app.llm_service.GroqLLMService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                
                from fastapi.testclient import TestClient
                from app.main import app
                yield TestClient(app), mock_service

    def test_health_endpoint(self, client):
        test_client, _ = client
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-care-assistant"

    def test_root_endpoint(self, client):
        test_client, _ = client
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "AI Care Assistant"
        assert "generate_care_instruction" in data["endpoints"]

    def test_generate_care_instruction_endpoint(self, client):
        test_client, mock_service = client
        mock_response = CareInstructionResponse(
            instruction="Water the Monstera (Monstera deliciosa) in the Living Room near the east window with 500 ml.",
            plant_name="Monstera",
            species="Monstera deliciosa",
            location="Living Room",
            specific_spot="Near east window",
            action=CareAction.WATER,
            amount_ml=500,
            notes=None,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            generated_at=datetime(2024, 1, 15, 10, 0, 0)
        )
        mock_service.generate_instruction.return_value = mock_response

        response = test_client.post(
            "/generate-care-instruction",
            json={
                "plant_name": "Monstera",
                "species": "Monstera deliciosa",
                "location": "Living Room",
                "specific_spot": "Near east window",
                "action": "water",
                "amount_ml": 500,
                "notes": "",
                "timestamp": "2024-01-15T10:00:00"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["plant_name"] == "Monstera"
        assert "500 ml" in data["instruction"]

    def test_generate_care_instruction_invalid_action(self, client):
        test_client, _ = client
        response = test_client.post(
            "/generate-care-instruction",
            json={
                "plant_name": "Monstera",
                "species": "Monstera deliciosa",
                "location": "Living Room",
                "specific_spot": "Near east window",
                "action": "invalid_action",
                "amount_ml": 500
            }
        )
        assert response.status_code == 422

    def test_generate_care_instruction_missing_amount_for_water(self, client):
        test_client, _ = client
        response = test_client.post(
            "/generate-care-instruction",
            json={
                "plant_name": "Monstera",
                "species": "Monstera deliciosa",
                "location": "Living Room",
                "specific_spot": "Near east window",
                "action": "water"
            }
        )
        assert response.status_code == 422


class TestVacationSchemas:
    def test_valid_vacation_request(self):
        req = VacationCareRequest(
            vacation_start=datetime(2024, 6, 15, 8, 0, 0),
            vacation_end=datetime(2024, 6, 22, 20, 0, 0),
            plants=[
                WateringScheduleItem(
                    plant_name="Monstera",
                    species="Monstera deliciosa",
                    location="Living Room",
                    specific_spot="Near east window",
                    frequency_days=3,
                    amount_ml=500,
                    last_watered=datetime(2024, 6, 14, 10, 0, 0),
                    notes="Use filtered water"
                ),
                WateringScheduleItem(
                    plant_name="Snake Plant",
                    species="Sansevieria",
                    location="Bedroom",
                    specific_spot="Floor by window",
                    frequency_days=7,
                    amount_ml=200,
                    last_watered=datetime(2024, 6, 13, 14, 0, 0),
                    notes=""
                )
            ],
            risk_level="medium",
            additional_notes="Key under mat"
        )
        assert req.vacation_start == datetime(2024, 6, 15, 8, 0, 0)
        assert req.risk_level == "medium"
        assert len(req.plants) == 2

    def test_vacation_end_before_start_raises(self):
        with pytest.raises(ValueError, match="vacation_end must be after vacation_start"):
            VacationCareRequest(
                vacation_start=datetime(2024, 6, 22, 20, 0, 0),
                vacation_end=datetime(2024, 6, 15, 8, 0, 0),
                plants=[
                    WateringScheduleItem(
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

    def test_invalid_risk_level_raises(self):
        with pytest.raises(ValueError, match="risk_level must be one of"):
            VacationCareRequest(
                vacation_start=datetime(2024, 6, 15, 8, 0, 0),
                vacation_end=datetime(2024, 6, 22, 20, 0, 0),
                plants=[
                    WateringScheduleItem(
                        plant_name="Monstera",
                        species="Monstera deliciosa",
                        location="Living Room",
                        specific_spot="Near east window",
                        frequency_days=3,
                        amount_ml=500,
                        last_watered=datetime(2024, 6, 14, 10, 0, 0)
                    )
                ],
                risk_level="extreme"
            )

    def test_valid_risk_levels(self):
        for level in ["low", "medium", "high"]:
            req = VacationCareRequest(
                vacation_start=datetime(2024, 6, 15, 8, 0, 0),
                vacation_end=datetime(2024, 6, 22, 20, 0, 0),
                plants=[
                    WateringScheduleItem(
                        plant_name="Monstera",
                        species="Monstera deliciosa",
                        location="Living Room",
                        specific_spot="Near east window",
                        frequency_days=3,
                        amount_ml=500,
                        last_watered=datetime(2024, 6, 14, 10, 0, 0)
                    )
                ],
                risk_level=level
            )
            assert req.risk_level == level

    def test_empty_plants_list_raises(self):
        with pytest.raises(ValueError):
            VacationCareRequest(
                vacation_start=datetime(2024, 6, 15, 8, 0, 0),
                vacation_end=datetime(2024, 6, 22, 20, 0, 0),
                plants=[]
            )


class TestVacationPrompts:
    def test_build_vacation_user_prompt(self):
        plants = [
            {
                "plant_name": "Monstera",
                "species": "Monstera deliciosa",
                "location": "Living Room",
                "specific_spot": "Near east window",
                "frequency_days": 3,
                "amount_ml": 500,
                "last_watered": "2024-06-14T10:00:00",
                "notes": "Use filtered water"
            }
        ]
        prompt = build_vacation_user_prompt(
            vacation_start="2024-06-15T08:00:00",
            vacation_end="2024-06-22T20:00:00",
            plants=plants,
            risk_level="medium",
            additional_notes="Key under mat"
        )
        assert "Monstera" in prompt
        assert "Monstera deliciosa" in prompt
        assert "Living Room" in prompt
        assert "Near east window" in prompt
        assert "every 3 days" in prompt
        assert "500 ml" in prompt
        assert "2024-06-14T10:00:00" in prompt
        assert "Use filtered water" in prompt
        assert "Key under mat" in prompt
        assert "caretaker_message" in prompt

    def test_vacation_system_prompt_contains_rules(self):
        assert "NEVER VIOLATE" in VACATION_SYSTEM_PROMPT
        assert "NEVER invent" in VACATION_SYSTEM_PROMPT
        assert "vacation dates" in VACATION_SYSTEM_PROMPT.lower()
        assert "watering schedule" in VACATION_SYSTEM_PROMPT.lower()
        assert "last watered" in VACATION_SYSTEM_PROMPT.lower()

    def test_vacation_prompt_pet_warning_and_winter_context(self):
        toxic = {
            "plant_name": "Greeny",
            "species": "Golden Pothos",
            "location": "Living Room",
            "specific_spot": "High shelf",
            "frequency_days": 10,
            "amount_ml": 150,
            "last_watered": "2026-12-01T10:00:00Z",
            "notes": "",
            "pet_safety": "toxic",
            "placement_tip": "Keep above cat height",
        }
        safe = {**toxic, "plant_name": "Pesto", "species": "Sweet Basil", "pet_safety": "safe"}
        prompt = build_vacation_user_prompt(
            vacation_start="2026-12-10T10:00:00Z",
            vacation_end="2026-12-20T10:00:00Z",
            plants=[toxic, safe],
            risk_level="high",
            season="Winter",
            season_factor=1.4,
        )
        assert "Winter" in prompt
        assert "40% less often" in prompt
        assert prompt.count("wear gloves") == 1


class TestVacationLLMService:
    @pytest.fixture
    def mock_groq_client(self):
        with patch('app.llm_service.Groq') as mock:
            yield mock

    @pytest.fixture
    def sample_vacation_request(self):
        return VacationCareRequest(
            vacation_start=datetime(2024, 6, 15, 8, 0, 0),
            vacation_end=datetime(2024, 6, 22, 20, 0, 0),
            plants=[
                WateringScheduleItem(
                    plant_name="Monstera",
                    species="Monstera deliciosa",
                    location="Living Room",
                    specific_spot="Near east window",
                    frequency_days=3,
                    amount_ml=500,
                    last_watered=datetime(2024, 6, 14, 10, 0, 0),
                    notes="Use filtered water"
                ),
                WateringScheduleItem(
                    plant_name="Snake Plant",
                    species="Sansevieria",
                    location="Bedroom",
                    specific_spot="Floor by window",
                    frequency_days=7,
                    amount_ml=200,
                    last_watered=datetime(2024, 6, 13, 14, 0, 0),
                    notes=""
                )
            ],
            risk_level="medium",
            additional_notes="Key under mat"
        )

    def test_generate_vacation_care_success(self, mock_groq_client, sample_vacation_request):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"caretaker_message": "From June 15 to June 22: Water Monstera (Monstera deliciosa) in Living Room near east window every 3 days with 500 ml using filtered water (last watered June 14). Water Snake Plant (Sansevieria) in Bedroom on floor by window every 7 days with 200 ml (last watered June 13)."}'
        mock_groq_client.return_value.chat.completions.create.return_value = mock_response

        service = GroqLLMService(api_key="test-key")
        response = service.generate_vacation_care(sample_vacation_request)

        assert isinstance(response, VacationCareResponse)
        assert "Monstera" in response.caretaker_message
        assert "Snake Plant" in response.caretaker_message
        assert "500 ml" in response.caretaker_message
        assert "200 ml" in response.caretaker_message
        assert response.plant_count == 2
        assert response.risk_level == "medium"

    def test_generate_vacation_care_fallback_on_json_error(self, mock_groq_client, sample_vacation_request):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Not valid JSON"
        mock_groq_client.return_value.chat.completions.create.return_value = mock_response

        service = GroqLLMService(api_key="test-key")
        response = service.generate_vacation_care(sample_vacation_request)

        assert isinstance(response, VacationCareResponse)
        assert "Monstera" in response.caretaker_message
        assert "Snake Plant" in response.caretaker_message
        assert "Living Room" in response.caretaker_message
        assert "Bedroom" in response.caretaker_message

    def test_fallback_vacation_message_format(self, sample_vacation_request):
        service = GroqLLMService(api_key="test-key")
        fallback = service._fallback_vacation_message(sample_vacation_request)

        assert "From June 15 to June 22:" in fallback
        assert "Monstera" in fallback
        assert "Snake Plant" in fallback
        assert "every 3 days" in fallback
        assert "every 7 days" in fallback
        assert "500 ml" in fallback
        assert "200 ml" in fallback
        assert "last watered" in fallback
        assert "Use filtered water" in fallback


class TestVacationFastAPIEndpoints:
    @pytest.fixture
    def client(self):
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            with patch('app.llm_service.GroqLLMService') as mock_service_class:
                mock_service = Mock()
                mock_service_class.return_value = mock_service
                
                from fastapi.testclient import TestClient
                from app.main import app
                yield TestClient(app), mock_service

    def test_generate_vacation_care_endpoint(self, client):
        test_client, mock_service = client
        mock_response = VacationCareResponse(
            caretaker_message="From June 15 to June 22: Water Monstera (Monstera deliciosa) in Living Room near east window every 3 days with 500 ml using filtered water (last watered June 14). Water Snake Plant (Sansevieria) in Bedroom on floor by window every 7 days with 200 ml (last watered June 13).",
            vacation_start=datetime(2024, 6, 15, 8, 0, 0),
            vacation_end=datetime(2024, 6, 22, 20, 0, 0),
            plant_count=2,
            risk_level="medium",
            generated_at=datetime(2024, 6, 15, 8, 0, 0)
        )
        mock_service.generate_vacation_care.return_value = mock_response

        response = test_client.post(
            "/generate-vacation-care",
            json={
                "vacation_start": "2024-06-15T08:00:00",
                "vacation_end": "2024-06-22T20:00:00",
                "plants": [
                    {
                        "plant_name": "Monstera",
                        "species": "Monstera deliciosa",
                        "location": "Living Room",
                        "specific_spot": "Near east window",
                        "frequency_days": 3,
                        "amount_ml": 500,
                        "last_watered": "2024-06-14T10:00:00",
                        "notes": "Use filtered water"
                    },
                    {
                        "plant_name": "Snake Plant",
                        "species": "Sansevieria",
                        "location": "Bedroom",
                        "specific_spot": "Floor by window",
                        "frequency_days": 7,
                        "amount_ml": 200,
                        "last_watered": "2024-06-13T14:00:00",
                        "notes": ""
                    }
                ],
                "risk_level": "medium",
                "additional_notes": "Key under mat"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["plant_count"] == 2
        assert data["risk_level"] == "medium"
        assert "Monstera" in data["caretaker_message"]
        assert "Snake Plant" in data["caretaker_message"]

    def test_generate_vacation_care_endpoint_invalid_dates(self, client):
        test_client, _ = client
        response = test_client.post(
            "/generate-vacation-care",
            json={
                "vacation_start": "2024-06-22T20:00:00",
                "vacation_end": "2024-06-15T08:00:00",
                "plants": [
                    {
                        "plant_name": "Monstera",
                        "species": "Monstera deliciosa",
                        "location": "Living Room",
                        "specific_spot": "Near east window",
                        "frequency_days": 3,
                        "amount_ml": 500,
                        "last_watered": "2024-06-14T10:00:00"
                    }
                ]
            }
        )
        assert response.status_code == 422

    def test_generate_vacation_care_endpoint_missing_plant_fields(self, client):
        test_client, _ = client
        response = test_client.post(
            "/generate-vacation-care",
            json={
                "vacation_start": "2024-06-15T08:00:00",
                "vacation_end": "2024-06-22T20:00:00",
                "plants": [
                    {
                        "plant_name": "Monstera",
                        "species": "Monstera deliciosa"
                    }
                ]
            }
        )
        assert response.status_code == 422

    def test_generate_vacation_care_endpoint_empty_plants(self, client):
        test_client, _ = client
        response = test_client.post(
            "/generate-vacation-care",
            json={
                "vacation_start": "2024-06-15T08:00:00",
                "vacation_end": "2024-06-22T20:00:00",
                "plants": []
            }
        )
        assert response.status_code == 422
