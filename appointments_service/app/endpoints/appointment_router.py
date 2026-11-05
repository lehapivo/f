from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.gateways.clients_gateway import ClientsGateway
from app.messaging import RabbitPublisher
from app.models.appointment import Appointment, AppointmentCreate, AppointmentStatus
from app.repositories.db_appointment_repo import AppointmentRepo
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def get_service(db: Session = Depends(get_db)) -> AppointmentService:
    return AppointmentService(AppointmentRepo(db), RabbitPublisher(), ClientsGateway())


@router.post("", status_code=status.HTTP_201_CREATED)
def create_appointment(data: AppointmentCreate,
                       service: AppointmentService = Depends(get_service)) -> Appointment:
    return service.create(data)


@router.get("")
def list_appointments(date: date | None = None, status: AppointmentStatus | None = None,
                      offset: int = Query(0, ge=0), count: int = Query(20, ge=1, le=100),
                      service: AppointmentService = Depends(get_service)) -> list[Appointment]:
    return service.list(date, status.value if status else None, offset, count)


@router.get("/{appointment_id}")
def get_appointment(appointment_id: UUID, service: AppointmentService = Depends(get_service)) -> Appointment:
    return service.get(appointment_id)


@router.post("/{appointment_id}:confirm")
def confirm_appointment(appointment_id: UUID,
                        service: AppointmentService = Depends(get_service)) -> Appointment:
    return service.confirm(appointment_id)


@router.post("/{appointment_id}:cancel")
def cancel_appointment(appointment_id: UUID,
                       service: AppointmentService = Depends(get_service)) -> Appointment:
    return service.cancel(appointment_id)
