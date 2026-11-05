from app.models.diagnostic import Diagnostic
from app.repositories.base import DbRepository
from app.schemas.diagnostic import DiagnosticDB


class DiagnosticRepo(DbRepository[Diagnostic]):
    model = Diagnostic
    table = DiagnosticDB
