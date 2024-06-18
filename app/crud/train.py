from sqlalchemy.orm import Session
from app.schemas import user_schema
from fastapi import HTTPException, status
from app.core import openAI_embeddings

def finetune(db: Session, current_user: user_schema.User):
    try:
        openAI_embeddings.main()

        return {"message": "Script executed successfully"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Script execution failed: {str(e)}")
