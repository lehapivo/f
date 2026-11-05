from app.models.diagnostic import Diagnostic
from app.repositories.base import LocalRepository


class DiagnosticRepo(LocalRepository[Diagnostic]):
    model = Diagnostic
