import threading
import random

class CrewID:
    _instance = None
    _lock = threading.Lock()
    crewid = None

    def __new__(cls, *args, **kwargs):
        # with cls._lock:
        #     if not cls._instance:
        #         cls._instance = super(CrewID, cls).__new__(cls, *args, **kwargs)
        #         logger = logging.getLogger(__name__)
        #         logger.debug(f"\n\n**************************************\nGenerated Crew ID: {CrewID.crewid}\n*******************************\n\n")
        return cls._instance

    @staticmethod
    def set_crewid(new_crewid: str) -> None:
        with CrewID._lock:
            CrewID.crewid = new_crewid

    @staticmethod
    def get_crewid() -> str:
        if CrewID.crewid is None:
            CrewID.generate_crewid()
        return CrewID.crewid

    @staticmethod
    def generate_crewid() -> str:

        with CrewID._lock:
            if CrewID.crewid is None:
                CrewID.crewid = str(random.randint(1000, 9999))
                print(f"\n\n\n**************************************\ncrewid.py: Generated Crew ID: {CrewID.crewid}\n*******************************\n\n")
        return CrewID.crewid