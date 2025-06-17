# File: application/src/app/models/payment_proof.py
from sqlmodel import SQLModel, Field
import uuid
from datetime import datetime

class PaymentProof(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    enrollment_id: uuid.UUID = Field(foreign_key="enrollment.id", nullable=False)
    proof_url: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
