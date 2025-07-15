import logging
from abc import ABC

from rdflib import Namespace

from app.core.supabase import get_supabase


class BaseOntologyService(ABC):
    """Base service for all ontology operations"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Standard ontology namespaces
        self.FIBO_FND = Namespace("https://spec.edmcouncil.org/fibo/ontology/FND/")
        self.FIBO_SEC = Namespace("https://spec.edmcouncil.org/fibo/ontology/SEC/")
        self.FIBO_LOAN = Namespace("https://spec.edmcouncil.org/fibo/ontology/LOAN/")
        self.FIBO_DER = Namespace("https://spec.edmcouncil.org/fibo/ontology/DER/")
        self.FIBO_INS = Namespace("https://spec.edmcouncil.org/fibo/ontology/INS/")

    async def get_supabase(self):
        return await get_supabase()
