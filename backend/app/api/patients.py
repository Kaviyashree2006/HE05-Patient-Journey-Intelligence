from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database import models
from app.schemas.models import PatientCreate, PatientOut
from app.demo_data.synthetic_dataset import seed_demo_patient_in_db

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=List[PatientOut])
def list_patients(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).all()
    results = []
    for p in patients:
        doc_count = db.query(models.Document).filter(models.Document.patient_id == p.patient_id).count()
        ev_count = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == p.patient_id).count()
        chg_count = db.query(models.ChangeEvent).filter(models.ChangeEvent.patient_id == p.patient_id).count()
        conf_count = db.query(models.Conflict).filter(models.Conflict.patient_id == p.patient_id).count()

        results.append(PatientOut(
            patient_id=p.patient_id,
            patient_reference=p.patient_reference,
            name=p.name,
            age=p.age,
            gender=p.gender,
            created_at=p.created_at,
            document_count=doc_count,
            event_count=ev_count,
            change_count=chg_count,
            conflict_count=conf_count
        ))
    return results


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Patient).filter(models.Patient.patient_reference == payload.patient_reference).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient reference already exists.")

    new_patient = models.Patient(
        patient_reference=payload.patient_reference,
        name=payload.name,
        age=payload.age,
        gender=payload.gender
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    return PatientOut(
        patient_id=new_patient.patient_id,
        patient_reference=new_patient.patient_reference,
        name=new_patient.name,
        age=new_patient.age,
        gender=new_patient.gender,
        created_at=new_patient.created_at,
        document_count=0,
        event_count=0,
        change_count=0,
        conflict_count=0
    )


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    p = db.query(models.Patient).filter(models.Patient.patient_id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found.")

    doc_count = db.query(models.Document).filter(models.Document.patient_id == p.patient_id).count()
    ev_count = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == p.patient_id).count()
    chg_count = db.query(models.ChangeEvent).filter(models.ChangeEvent.patient_id == p.patient_id).count()
    conf_count = db.query(models.Conflict).filter(models.Conflict.patient_id == p.patient_id).count()

    return PatientOut(
        patient_id=p.patient_id,
        patient_reference=p.patient_reference,
        name=p.name,
        age=p.age,
        gender=p.gender,
        created_at=p.created_at,
        document_count=doc_count,
        event_count=ev_count,
        change_count=chg_count,
        conflict_count=conf_count
    )


@router.post("/seed-demo", response_model=PatientOut)
def seed_demo_patient(db: Session = Depends(get_db)):
    """1-Click Seed: Ingests 5 synthetic medical documents and generates full patient journey."""
    patient = seed_demo_patient_in_db(db)
    doc_count = db.query(models.Document).filter(models.Document.patient_id == patient.patient_id).count()
    ev_count = db.query(models.MedicalEvent).filter(models.MedicalEvent.patient_id == patient.patient_id).count()
    chg_count = db.query(models.ChangeEvent).filter(models.ChangeEvent.patient_id == patient.patient_id).count()
    conf_count = db.query(models.Conflict).filter(models.Conflict.patient_id == patient.patient_id).count()

    return PatientOut(
        patient_id=patient.patient_id,
        patient_reference=patient.patient_reference,
        name=patient.name,
        age=patient.age,
        gender=patient.gender,
        created_at=patient.created_at,
        document_count=doc_count,
        event_count=ev_count,
        change_count=chg_count,
        conflict_count=conf_count
    )
