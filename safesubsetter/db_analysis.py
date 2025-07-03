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
Base.VALID_TYPES = (
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

_model_cache = {}


def get_model_for_table(table_name):
    if table_name in _model_cache:
        return _model_cache[table_name]

    class_name = f"SafeSubsetRecord_{table_name}"
    table_attrs = {
        "__tablename__": table_name,
        "id": Column(Integer, autoincrement=True),
        "patient_file": Column(String, nullable=False),
        "leaf_node_path": Column(String, nullable=False),
        "old_type": Column(String, nullable=False),
        "old_value": Column(String, nullable=False),
        "new_type": Column(String, nullable=False),
        "new_value": Column(String, nullable=False),
        "resp_type": Column(String, nullable=False),
        "resp_value": Column(String, nullable=False),
        "server": Column(String, nullable=False),
        "response_status": Column(Boolean, nullable=False),
        "error_message": Column(String, nullable=True),
        "ip_validity": Column(Boolean, nullable=False),
        "ip_validity_error": Column(String, nullable=False),
        "op_validity": Column(Boolean, nullable=False),
        "op_validity_error": Column(String, nullable=False),
        "__table_args__": (
            PrimaryKeyConstraint(
                "patient_file", "leaf_node_path", "old_type", "new_type", "server"
            ),
            CheckConstraint(
                f"server IN {str(('ibm', 'iris', 'hapi', 'vista', 'blaze'))}",
                name=f"check_server_validity_{table_name}",
            ),
            CheckConstraint(
                f"old_type IN {str(Base.VALID_TYPES)}",
                name=f"check_old_type_validity_{table_name}",
            ),
            CheckConstraint(
                f"new_type IN {str(Base.VALID_TYPES)}",
                name=f"check_new_type_validity_{table_name}",
            ),
            CheckConstraint(
                "NOT (response_status = 0 AND error_message IS NULL)",
                name=f"check_error_message_presence_{table_name}",
            ),
            {
                "extend_existing": True,
                "sqlite_autoincrement": True,
            },
        ),
    }

    model = type(class_name, (Base,), table_attrs)
    _model_cache[table_name] = model
    return model


class Database:
    def __init__(self, db_path: str):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)

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
        Model = get_model_for_table("safe_subset_records")
        record = Model(
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

    def get_all_records(self, table_name):
        Model = get_model_for_table(table_name)
        with Session(self.engine) as session:
            return session.query(Model).all()

    def count_accepted(self, table_name):
        Model = get_model_for_table(table_name)
        with Session(self.engine) as session:
            return session.query(Model).filter(Model.response_status == 1).count()

    def count_accepted_with_missing(self, table_name):
        Model = get_model_for_table(table_name)
        with Session(self.engine) as session:
            return (
                session.query(Model)
                .filter(Model.response_status == 1, Model.resp_value.like("%missing%"))
                .count()
            )

    def count_output_resp_diff(self, table_name):
        Model = get_model_for_table(table_name)
        with Session(self.engine) as session:
            total_count = (
                session.query(Model).filter(Model.response_status == 1).count()
            )
            diff_count = (
                session.query(Model)
                .filter(
                    Model.response_status == 1,
                    Model.resp_value.not_like("%missing%"),
                    Model.new_value != Model.resp_value,
                )
                .count()
            )
            return diff_count if total_count else 0.0
