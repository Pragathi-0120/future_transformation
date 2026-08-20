from sqlalchemy.orm import Session
from app.models.models import ActivityLog
def log(db:Session,user_id:int,action:str,details:str): db.add(ActivityLog(user_id=user_id,action=action,details=details))
