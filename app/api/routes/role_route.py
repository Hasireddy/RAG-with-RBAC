from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.role_schema import RoleCreate, RoleResponse
from app.database.session import get_db
from app.models.role_model import RoleDB


router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("/", response_model=list[RoleResponse])
def get_roles(db: Session = Depends(get_db)):
    return db.query(RoleDB).all()


@router.post("/", response_model=RoleResponse)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    existing = db.query(RoleDB).filter(RoleDB.role_name == role.role_name).first()

    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")

    new_role = RoleDB(role_name=role.role_name)

    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    return new_role


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(RoleDB).filter(RoleDB.id == role_id).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return role


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, role_update: RoleCreate, db: Session = Depends(get_db)):
    role = db.query(RoleDB).filter(RoleDB.id == role_id).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    role.role_name = role_update.role_name

    db.commit()
    db.refresh(role)

    return role


@router.delete("/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(RoleDB).filter(RoleDB.id == role_id).first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    db.delete(role)
    db.commit()

    return {"message": "Role deleted successfully"}