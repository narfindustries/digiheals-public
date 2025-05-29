"""SQLAlchemy code to create and insert into SQLite DB."""

from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class SynServerRecord(Base):
    """Synthea Server Class"""

    __tablename__ = "synthea_server_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_file = Column(String, nullable=False)
    og_file_valid = Column(String, nullable=False)
    blaze_valid = Column(String, nullable=False)
    hapi_valid = Column(String, nullable=False)
    ibm_valid = Column(String, nullable=False)
    iris_valid = Column(String, nullable=False)
    vista_valid = Column(String, nullable=False)


class Database:

    def __init__(self, db_path: str):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)

    def insert_syn_file_record(
        self,
        patient_file: str,
        og_file_valid: str,
        blaze_valid: str,
        hapi_valid: str,
        ibm_valid: str,
        iris_valid: str,
        vista_valid: str,
    ) -> None:
        """
        Insert a new record into the synthea_server_records table.
        Creates a SynServerRecord instance and commits it to the database.
        All parameters correspond to columns in the SynServerRecord table.
        """
        record = SynServerRecord(
            patient_file=patient_file,
            og_file_valid=og_file_valid,
            blaze_valid=blaze_valid,
            hapi_valid=hapi_valid,
            ibm_valid=ibm_valid,
            iris_valid=iris_valid,
            vista_valid=vista_valid,
        )

        with Session(self.engine) as session:
            session.add(record)
            session.commit()
