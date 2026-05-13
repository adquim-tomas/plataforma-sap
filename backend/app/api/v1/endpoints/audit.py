from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.audit import OperationAudit
from app.schemas.auth import TokenPayload

router = APIRouter(prefix="/audit", tags=["audit"])


class OperationAuditRow(BaseModel):
    id: int
    batch_id: int
    row_index: int
    username: str
    sap_module: str
    resource_id: str | None
    fields_before: dict[str, Any] | None
    fields_after: dict[str, Any] | None
    status: Literal["ok", "fail"]
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class OperationAuditPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[OperationAuditRow]


@router.get("/operations", response_model=OperationAuditPage)
def list_operations(
    db: Session = Depends(get_db),
    _user: TokenPayload = Depends(get_current_user),
    module: str | None = Query(default=None, description="Filtra por sap_module"),
    username: str | None = Query(default=None, description="Filtra por usuario operador"),
    resource_id: str | None = Query(default=None, description="Filtra por identificador del recurso SAP"),
    status: Literal["ok", "fail"] | None = Query(default=None),
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> OperationAuditPage:
    """
    Bitácora de operaciones: una fila por cada row de Excel procesada, con
    snapshot antes/después del recurso SAP cuando aplica. Append-only.
    """
    stmt = select(OperationAudit)
    if module:
        stmt = stmt.where(OperationAudit.sap_module == module)
    if username:
        stmt = stmt.where(OperationAudit.username == username)
    if resource_id:
        stmt = stmt.where(OperationAudit.resource_id == resource_id)
    if status:
        stmt = stmt.where(OperationAudit.status == status)
    if from_date:
        stmt = stmt.where(OperationAudit.created_at >= from_date)
    if to_date:
        stmt = stmt.where(OperationAudit.created_at <= to_date)

    count_stmt = stmt.with_only_columns(OperationAudit.id).order_by(None)
    total = len(db.execute(count_stmt).all())

    rows = db.execute(
        stmt.order_by(OperationAudit.created_at.desc())
            .limit(limit)
            .offset(offset)
    ).scalars().all()

    return OperationAuditPage(
        total=total,
        limit=limit,
        offset=offset,
        items=[OperationAuditRow.model_validate(r) for r in rows],
    )
