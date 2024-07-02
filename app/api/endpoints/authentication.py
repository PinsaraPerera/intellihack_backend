import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from app import schemas, db, models, utils
from sqlalchemy.orm import Session
from app.core.gcp_utils import create_folder_in_gcp

router = APIRouter(
    tags=["Authentication"],
)


@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(db.session.get_db),
):
    user = (
        db.query(models.user.User)
        .filter(models.user.User.email == form_data.username)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )
    if not utils.hashing.Hash.verify(user.password, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect Password"
        )

    access_token = utils.token.create_access_token(data={"sub": user.email})

    # Create a folder in the GCS bucket for the user
    try:
        create_folder_in_gcp(user.email)
    except RuntimeError as e:
        print(f"An error occurred: {e}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "vectorstore": user.vectorstore,
    }
