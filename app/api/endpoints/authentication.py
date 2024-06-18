from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app import schemas, db, models, utils
from sqlalchemy.orm import Session

router = APIRouter(
    tags=["Authentication"],
)

@router.post("/login")
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(db.session.get_db)):
    user = db.query(models.user.User).filter(models.user.User.email == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials")
    if not utils.hashing.Hash.verify(user.password, request.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect Password")
        
    access_token = utils.token.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}