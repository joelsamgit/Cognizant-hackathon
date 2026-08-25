from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.plant import ErrorResponse, PlantCreate, PlantPatch, PlantPut, PlantResponse
from app.services import plants as plant_service


router = APIRouter(prefix="/plants", tags=["plants"])
DbSession = Annotated[Session, Depends(get_db)]


def require_plant(db: Session, plant_id: int):
    plant = plant_service.get_plant(db, plant_id)
    if plant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")
    return plant


@router.get("", response_model=list[PlantResponse])
def list_plants(
    db: DbSession,
    room: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
) -> list[PlantResponse]:
    return plant_service.list_plants(db, room=room)


@router.get(
    "/{plant_id}",
    response_model=PlantResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_plant(plant_id: int, db: DbSession) -> PlantResponse:
    return plant_service.to_response(require_plant(db, plant_id))


@router.post("", response_model=PlantResponse, status_code=status.HTTP_201_CREATED)
def create_plant(payload: PlantCreate, db: DbSession) -> PlantResponse:
    return plant_service.to_response(plant_service.create_plant(db, payload))


@router.put(
    "/{plant_id}",
    response_model=PlantResponse,
    responses={404: {"model": ErrorResponse}},
)
def replace_plant(plant_id: int, payload: PlantPut, db: DbSession) -> PlantResponse:
    plant = require_plant(db, plant_id)
    return plant_service.to_response(plant_service.replace_plant(db, plant, payload))


@router.patch(
    "/{plant_id}",
    response_model=PlantResponse,
    responses={404: {"model": ErrorResponse}},
)
def update_plant(plant_id: int, payload: PlantPatch, db: DbSession) -> PlantResponse:
    plant = require_plant(db, plant_id)
    return plant_service.to_response(plant_service.update_plant(db, plant, payload))


@router.delete(
    "/{plant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
def delete_plant(plant_id: int, db: DbSession) -> Response:
    plant_service.delete_plant(db, require_plant(db, plant_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{plant_id}/water",
    response_model=PlantResponse,
    responses={404: {"model": ErrorResponse}},
)
def water_plant(plant_id: int, db: DbSession) -> PlantResponse:
    plant = require_plant(db, plant_id)
    return plant_service.to_response(plant_service.water_plant(db, plant))

