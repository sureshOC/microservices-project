from fastapi import FastAPI, Depends

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import SessionLocal, engine, Base
from models import Payment

Base.metadata.create_all(bind=engine)

app = FastAPI(title='Payment service App is Running..')

Base.metadata.create_all(bind=engine)


def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@app.post("/payments")
async def make_payment(id: int, amount: float, idempotency_key: str, db: Session = Depends(get_db)):


    # 1. Check whether payment already exists
    existing_payment = (
        db.query(Payment)
        .filter(Payment.idempotency_key == idempotency_key)
        .first()
    )

    if existing_payment:
        print(f"Payment already processed for order {id}")
        return {
            "id": existing_payment.order_id,
            "amount": float(existing_payment.amount),
            "status": existing_payment.status
        }

    print(f"Processing NEW payment for order {id}")

    payment = Payment(
        idempotency_key=idempotency_key,
        order_id=id,
        amount=amount,
        status="SUCCESS"
    )

    db.add(payment)

    try:

        db.commit()

        db.refresh(payment)

    except IntegrityError:
        # Another concurrent request inserted
        # the same idempotency key.
        db.rollback()

        existing_payment = (
            db.query(Payment)
            .filter(
                Payment.idempotency_key == idempotency_key
            )
            .first()
        )

        return {
            "id": existing_payment.order_id,
            "amount": float(existing_payment.amount),
            "status": existing_payment.status
        }

    return {
        "id": payment.order_id,
        "amount": float(payment.amount),
        "status": payment.status
    }