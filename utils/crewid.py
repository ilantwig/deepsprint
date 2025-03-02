import random

class CrewID:
    _instance = None
    crewid = None

    def __new__(cls, *args, **kwargs):
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
        CrewID.crewid = str(random.randint(1000, 9999))
        print(f"\n\n\n**************************************\ncrewid.py: Generated Crew ID: {CrewID.crewid}\n*******************************\n\n")
        return CrewID.crewid
