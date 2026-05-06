from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas.permissions_schema import PermissionCreate, PermissionResponse
from app.database.session import get_db
from app.models.permissions_model import PermissionDB

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("/", response_model=list[PermissionResponse])
def get_permissions(db: Session = Depends(get_db)):
    return db.query(PermissionDB).all()



@router.post("/", response_model=PermissionResponse)
def create_permission(permission: PermissionCreate, db: Session = Depends(get_db)):

    existing = db.query(PermissionDB).filter(
        PermissionDB.permission_name == permission.permission_name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Permission already exists"
        )

    new_permission = PermissionDB(
        permission_name=permission.permission_name
    )

    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)

    return new_permission


@router.get("/{permission_id}", response_model=PermissionResponse)
def get_permission(permission_id: int, db: Session = Depends(get_db)):

    permission = db.query(PermissionDB).filter(
        PermissionDB.id == permission_id
    ).first()

    if not permission:
        raise HTTPException(
            status_code=404,
            detail="Permission not found"
        )

    return permission


@router.put("/{permission_id}", response_model=PermissionResponse)
def update_permission(
    permission_id: int,
    permission_update: PermissionCreate,
    db: Session = Depends(get_db)
):

    permission = db.query(PermissionDB).filter(
        PermissionDB.id == permission_id
    ).first()

    if not permission:
        raise HTTPException(
            status_code=404,
            detail="Permission not found"
        )

    # optional: check duplicate name
    duplicate = db.query(PermissionDB).filter(
        PermissionDB.permission_name == permission_update.permission_name,
        PermissionDB.id != permission_id
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="Permission name already exists"
        )

    permission.permission_name = permission_update.permission_name

    db.commit()
    db.refresh(permission)

    return permission


@router.delete("/{permission_id}")
def delete_permission(permission_id: int, db: Session = Depends(get_db)):

    permission = db.query(PermissionDB).filter(
        PermissionDB.id == permission_id
    ).first()

    if not permission:
        raise HTTPException(
            status_code=404,
            detail="Permission not found"
        )

    db.delete(permission)
    db.commit()

    return {"message": "Permission deleted successfully"}




