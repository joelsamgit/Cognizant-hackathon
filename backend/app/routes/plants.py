from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.care_event import CareEventCreate, CareEventResponse
from app.schemas.plant import ErrorResponse, PlantCreate, PlantPatch, PlantPut, PlantResponse
from app.services import care_events as care_event_service
from app.services import plants as plant_service


router = APIRouter(prefix="/plants", tags=["plants"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
SeasonOverride = Annotated[
    str | None,
    Query(pattern="^(summer|monsoon|post-monsoon|winter)$"),
]


def require_plant(db: Session, plant_id: int, user_id: int):
    plant = plant_service.get_plant(db, plant_id, user_id)
    if plant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plant not found")
    return plant


@router.get("", response_model=list[PlantResponse])
def list_plants(
    db: DbSession,
    user: CurrentUser,
    room: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    season: SeasonOverride = None,
) -> list[PlantResponse]:
    return plant_service.list_plants(db, user.id, room=room, season_override=season)


@router.get(
    "/{plant_id}",
    response_model=PlantResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_plant(
    plant_id: int,
    db: DbSession,
    user: CurrentUser,
    season: SeasonOverride = None,
) -> PlantResponse:
    return plant_service.response_for_plant(
        db,
        require_plant(db, plant_id, user.id),
        season_override=season,
    )


@router.post("", response_model=PlantResponse, status_code=status.HTTP_201_CREATED)
def create_plant(
    payload: PlantCreate,
    db: DbSession,
    user: CurrentUser,
    season: SeasonOverride = None,
) -> PlantResponse:
    return plant_service.response_for_plant(
        db,
        plant_service.create_plant(db, payload, user.id),
        season_override=season,
    )


@router.put(
    "/{plant_id}",
    response_model=PlantResponse,
    responses={404: {"model": ErrorResponse}},
)
def replace_plant(
    plant_id: int,
    payload: PlantPut,
    db: DbSession,
    user: CurrentUser,
    season: SeasonOverride = None,
) -> PlantResponse:
    plant = require_plant(db, plant_id, user.id)
    return plant_service.response_for_plant(
        db,
        plant_service.replace_plant(db, plant, payload),
        season_override=season,
    )


@router.patch(
    "/{plant_id}",
    response_model=PlantResponse,
    responses={404: {"model": ErrorResponse}},
)
def update_plant(
    plant_id: int,
    payload: PlantPatch,
    db: DbSession,
    user: CurrentUser,
    season: SeasonOverride = None,
) -> PlantResponse:
    plant = require_plant(db, plant_id, user.id)
    return plant_service.response_for_plant(
        db,
        plant_service.update_plant(db, plant, payload),
        season_override=season,
    )


@router.delete(
    "/{plant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
def delete_plant(plant_id: int, db: DbSession, user: CurrentUser) -> Response:
    plant_service.delete_plant(db, require_plant(db, plant_id, user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{plant_id}/water",
    response_model=PlantResponse,
    responses={404: {"model": ErrorResponse}},
)
def water_plant(
    plant_id: int,
    db: DbSession,
    user: CurrentUser,
    season: SeasonOverride = None,
) -> PlantResponse:
    plant = require_plant(db, plant_id, user.id)
    try:
        result = plant_service.water_plant(db, plant, season_override=season)
    except plant_service.WateringLockedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return plant_service.to_response(
        result.plant,
        waterings=result.waterings,
        season_override=season,
        milestone=result.milestone,
    )


@router.get(
    "/{plant_id}/events",
    response_model=list[CareEventResponse],
    responses={404: {"model": ErrorResponse}},
)
def list_care_events(
    plant_id: int,
    db: DbSession,
    user: CurrentUser,
) -> list[CareEventResponse]:
    require_plant(db, plant_id, user.id)
    return [
        CareEventResponse.model_validate(event)
        for event in care_event_service.list_care_events(db, plant_id)
    ]


@router.post(
    "/{plant_id}/events",
    response_model=CareEventResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
)
def create_care_event(
    plant_id: int,
    payload: CareEventCreate,
    db: DbSession,
    user: CurrentUser,
) -> CareEventResponse:
    event = care_event_service.create_care_event(
        db,
        require_plant(db, plant_id, user.id),
        payload,
    )
    return CareEventResponse.model_validate(event)
