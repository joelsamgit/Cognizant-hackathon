from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    VacationModeRequest,
    VacationModeResponse,
    HealthResponse,
    RiskLevel
)
from .vacation_service import get_vacation_service, VacationService


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_vacation_service()
    yield


app = FastAPI(
    title="Vacation Mode Service",
    description="Manages plant care schedules during vacations and integrates with AI Care Assistant",
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


@app.post("/vacation-mode", response_model=VacationModeResponse)
async def create_vacation_mode(
    request: VacationModeRequest,
    service: VacationService = Depends(get_vacation_service)
):
    try:
        response = await service.generate_full_plan(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vacation plan: {str(e)}")


@app.post("/vacation-mode/plan-only", response_model=VacationModeResponse)
async def create_vacation_plan_only(
    request: VacationModeRequest,
    service: VacationService = Depends(get_vacation_service)
):
    try:
        response = service.create_vacation_plan(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vacation plan: {str(e)}")


@app.get("/")
async def root():
    return {
        "service": "Vacation Mode",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "create_vacation_mode": "/vacation-mode",
            "create_plan_only": "/vacation-mode/plan-only"
        }
    }