# app/core/sap_instance.py
from app.core.sap_client import SAPClient

# Singleton del service account — se inicializa en el lifespan de main.py
sap_service = SAPClient()