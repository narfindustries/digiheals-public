"""SQLAlchemy code to create and insert into SQLite DB."""

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


def get_record_class(tablename):
    class SafeSubsetRecord(Base):
        __tablename__ = tablename

        id = Column(Integer, autoincrement=True)
        patient_file = Column(String, nullable=False)
        leaf_node_path = Column(String, nullable=False)
        old_type = Column(String, nullable=False)
        old_value = Column(String, nullable=False)
        new_type = Column(String, nullable=False)
        new_value = Column(String, nullable=False)
        resp_type = Column(String, nullable=False)
        resp_value = Column(String, nullable=False)
        server = Column(String, nullable=False)
        response_status = Column(Boolean, nullable=False)
        error_message = Column(String, nullable=True)
        ip_validity = Column(Boolean, nullable=False)
        ip_validity_error = Column(String, nullable=False)
        op_validity = Column(Boolean, nullable=False)
        op_validity_error = Column(String, nullable=False)

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
            "largeInt",
            "largeFloat",
            "largeString",
        )
        SERVERS = ("ibm", "iris", "hapi", "vista", "blaze")

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

    return SafeSubsetRecord


class Database:

    def __init__(self, db_path: str, table_name: str):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.table_name = table_name
        self.record_class = get_record_class(table_name)

    def insert_safe_subset_record(
        self,
        patient_file: str,
        leaf_node_path: str,
        old_type: str,
        old_value: str,
        new_type: str,
        new_value: str,
        resp_type: str,
        resp_value: str,
        server: str,
        response_status: bool,
        error_message: str | None,
        ip_validity: bool,
        ip_validity_error: str,
        op_validity: bool,
        op_validity_error: str,
    ) -> None:
        """
        Insert a new record into the safe_subset_records table.
        Creates a SafeSubsetRecord instance and commits it to the database.
        All parameters correspond to columns in the SafeSubsetRecord table.
        """
        record = self.record_class(
            patient_file=patient_file,
            leaf_node_path=leaf_node_path,
            old_type=old_type,
            old_value=old_value,
            new_type=new_type,
            new_value=new_value,
            resp_type=resp_type,
            resp_value=resp_value,
            server=server,
            response_status=response_status,
            error_message=error_message,
            ip_validity=ip_validity,
            ip_validity_error=ip_validity_error,
            op_validity=op_validity,
            op_validity_error=op_validity_error,
        )

        with Session(self.engine) as session:
            session.add(record)
            session.commit()

    def get_all_records(self):
        """
        Retrieve all records from the safe_subset_records table.
        Returns a list of SafeSubsetRecord objects.
        """
        with Session(self.engine) as session:
            return session.query(self.record_class).all()
