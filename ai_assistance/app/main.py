from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from .schemas import (
    CareInstructionRequest,
    CareInstructionResponse,
    HealthResponse,
    CareAction,
    VacationCareRequest,
    VacationCareResponse
)
from .llm_service import get_llm_service, GroqLLMService


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_llm_service()
    yield


app = FastAPI(
    title="AI Care Assistant",
    description="Generates clear caretaker instructions from structured plant care data using Groq LLM",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()


@app.post("/generate-care-instruction", response_model=CareInstructionResponse)
async def generate_care_instruction(
    request: CareInstructionRequest,
    llm_service: GroqLLMService = Depends(get_llm_service)
):
    try:
        response = llm_service.generate_instruction(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate instruction: {str(e)}")


@app.post("/generate-vacation-care", response_model=VacationCareResponse)
async def generate_vacation_care(
    request: VacationCareRequest,
    llm_service: GroqLLMService = Depends(get_llm_service)
):
    try:
        response = llm_service.generate_vacation_care(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate vacation care: {str(e)}")


@app.get("/")
async def root():
    return {
        "service": "AI Care Assistant",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "generate_care_instruction": "/generate-care-instruction",
            "generate_vacation_care": "/generate-vacation-care"
        }
    }