from sqlalchemy import (
    create_engine,
    Column,
    String,
    PrimaryKeyConstraint,
    Integer,
    CheckConstraint,
    Boolean,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class SafeSubsetRecord(Base):
    __tablename__ = "safe_subset_records"

    id = Column(Integer, autoincrement=True)
    patient_file = Column(String, nullable=False)
    leaf_node_path = Column(String, nullable=False)
    old_type = Column(String, nullable=False)
    new_type = Column(String, nullable=False)
    new_value = Column(String, nullable=False)
    server = Column(String, nullable=False)
    response_status = Column(Boolean, nullable=False)
    error_message = Column(String, nullable=True)
    validity = Column(Boolean, nullable=False)

    # Define valid types as a class attribute
    VALID_TYPES = (
        "dateTime",
        "date",
        "boolean",
        "positiveInt",
        "markdown",
        "integer",
        "string",
        "url",
        "uri",
        "canonical",
        "time",
        "code",
        "unsignedInt",
        "uuid",
        "base64Binary",
        "id",
        "oid",
        "decimal",
        "xhtml",
        "instant",
    )
    SERVERS = ("ibm", "iris", "hapifhir", "vista", "blaze")

    __table_args__ = (
        PrimaryKeyConstraint(
            "patient_file", "leaf_node_path", "old_type", "new_type", "server"
        ),
        CheckConstraint(
            f"server IN {str(SERVERS)}",
            name="check_server_validity",
            comment=f"Servers must be within a restricted list of {str(SERVERS)}",
        ),
        CheckConstraint(
            f"old_type IN {str(VALID_TYPES)}",
            name="check_old_type_validity",
            comment="Types must be within a restricted list",
        ),
        CheckConstraint(
            f"new_type IN {str(VALID_TYPES)}",
            name="check_new_type_validity",
            comment="Types must be within a restricted list",
        ),
        CheckConstraint(
            "NOT (response_status = 0 AND error_message IS NULL)",
            name="check_error_message_presence",
            comment="Error message must be present if response status is False",
        ),
    )


class Database:

    def __init__(self, db_path: str):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)

    def insert_safe_subset_record(
        self,
        patient_file: str,
        leaf_node_path: str,
        old_type: str,
        new_type: str,
        new_value: str,
        server: str,
        response_status: bool,
        error_message: str | None,
        validity: bool,
    ) -> None:
        """
        Insert a new record into the safe_subset_records table.
        Creates a SafeSubsetRecord instance and commits it to the database.
        All parameters correspond to columns in the SafeSubsetRecord table.
        """
        record = SafeSubsetRecord(
            patient_file=patient_file,
            leaf_node_path=leaf_node_path,
            old_type=old_type,
            new_type=new_type,
            new_value=new_value,
            server=server,
            response_status=response_status,
            error_message=error_message,
            validity=validity,
        )

        with Session(self.engine) as session:
            session.add(record)
            session.commit()
