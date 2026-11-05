from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.messaging import RabbitPublisher
from app.models.client import Client, ClientCard, ClientCreate, Vehicle, VehicleCreate
from app.repositories.db_client_repo import ClientRepo, VehicleRepo
from app.services.client_service import ClientService

router = APIRouter(tags=["Clients"])


def get_service(db: Session = Depends(get_db)) -> ClientService:
    return ClientService(ClientRepo(db), VehicleRepo(db), RabbitPublisher())


@router.post("/clients", status_code=status.HTTP_201_CREATED)
def register_client(data: ClientCreate, service: ClientService = Depends(get_service)) -> Client:
    return service.register_client(data)


@router.get("/clients/{client_id}")
def get_client(client_id: UUID, service: ClientService = Depends(get_service)) -> ClientCard:
    return service.get_card(client_id)


@router.post("/clients/{client_id}/vehicles", status_code=status.HTTP_201_CREATED)
def add_vehicle(client_id: UUID, data: VehicleCreate,
                service: ClientService = Depends(get_service)) -> Vehicle:
    return service.add_vehicle(client_id, data)


@router.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: UUID, service: ClientService = Depends(get_service)) -> Vehicle:
    return service.get_vehicle(vehicle_id)
