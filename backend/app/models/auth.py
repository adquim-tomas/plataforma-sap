from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RevokedToken(Base):
    """
    Lista de JWT revocados (denylist). Al hacer logout, el `jti` del token se
    inserta acá; `get_current_user` rechaza cualquier token cuyo `jti` esté
    presente. `expires_at` guarda la expiración original del token para poder
    purgar filas vencidas (un jti ya expirado no necesita seguir en la lista).
    """
    __tablename__ = "revoked_token"

    jti:        Mapped[str]      = mapped_column(String(32), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[datetime] = mapped_column(
                                       DateTime,
                                       server_default=func.now(),
                                       nullable=False,
                                   )
