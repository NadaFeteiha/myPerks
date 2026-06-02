"""
myPerks — ORM Models
backend/db/models.py
"""

from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clerk_user_id = Column(String(128), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(128), nullable=True)

    vacation_balances = relationship(
        "VacationBalance", back_populates="employee", cascade="all, delete-orphan"
    )
    request_histories = relationship(
        "RequestHistory", back_populates="employee", cascade="all, delete-orphan"
    )
    documents = relationship(
        "Document", back_populates="uploader", cascade="all, delete-orphan"
    )
    conversations = relationship(
        "Conversation", back_populates="employee", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} name={self.name!r}>"


class VacationBalance(Base):
    __tablename__ = "vacation_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    leave_type: Mapped[str] = mapped_column(
        Enum("vacation", "sick", "pto", name="leave_type"),
        nullable=False,
    )
    total_days: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    used_days: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    year = Column(Integer, nullable=False)

    employee = relationship("Employee", back_populates="vacation_balances")

    # One row per employee, per year, per leave type
    __table_args__ = (
        Index(
            "ix_vacation_balance_employee_year_type",
            "employee_id",
            "year",
            "leave_type",
            unique=True,
        ),
    )

    @property
    def remaining_days(self) -> float:
        return self.total_days - self.used_days

    def __repr__(self) -> str:
        return (
            f"<VacationBalance employee_id={self.employee_id} "
            f"year={self.year} type={self.leave_type} remaining={self.remaining_days}>"
        )


class RequestHistory(Base):
    __tablename__ = "request_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", "cancelled", name="request_status"),
        nullable=False,
        default="pending",
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    body = Column(Text, nullable=True)

    employee = relationship("Employee", back_populates="request_histories")

    def __repr__(self) -> str:
        return (
            f"<RequestHistory id={self.id} type={self.type!r} status={self.status!r}>"
        )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(512), nullable=False)
    content_sha256 = Column(String(64), nullable=True, unique=True, index=True)
    uploaded_by = Column(
        Integer,
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    uploaded_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    uploader = relationship("Employee", back_populates="documents")
    chunks = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} filename={self.filename!r}>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)

    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("ix_document_chunk_doc_idx", "document_id", "chunk_index", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk id={self.id} document_id={self.document_id} "
            f"chunk_index={self.chunk_index}>"
        )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(
        String(255), nullable=True
    )  # optional summary/title of the conversation
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    employee = relationship("Employee", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} employee_id={self.employee_id}>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        Enum("user", "assistant", name="message_role"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id} conversation_id={self.conversation_id} "
            f"role={self.role!r}>"
        )
