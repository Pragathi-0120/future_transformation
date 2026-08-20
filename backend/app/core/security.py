from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
pwd_context=CryptContext(schemes=['bcrypt'],deprecated='auto'); oauth2_scheme=OAuth2PasswordBearer(tokenUrl='/auth/login')
def hash_password(value): return pwd_context.hash(value)
def verify_password(raw, hashed): return pwd_context.verify(raw,hashed)
def create_token(user): return jwt.encode({'sub':str(user.id),'role':user.role.name,'exp':datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_expire_minutes)},settings.jwt_secret,algorithm='HS256')
def current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    try: user_id=jwt.decode(token,settings.jwt_secret,algorithms=['HS256']).get('sub')
    except JWTError: user_id=None
    user=db.get(User,int(user_id)) if user_id else None
    if not user: raise HTTPException(status_code=401,detail='Your session is invalid or has expired.')
    return user
def admin_only(user=Depends(current_user)):
    if user.role.name.lower()!='admin': raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail='This space is for administrators only.')
    return user
