from pathlib import Path
from mimetypes import guess_type
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, desc
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.security import current_user, admin_only, verify_password, hash_password, create_token
from app.core.config import UPLOAD_DIR
from app.models.models import Role, User, Task, Document, ActivityLog
from app.schema.schemas import LoginInput, RegistrationInput, Token, TaskCreate, TaskUpdate, SearchInput
from app.services.activity import log
from app.services.vector import add_document, search
from app.utils.files import extract_text
router=APIRouter()

@router.post('/auth/register', status_code=201)
def register(data:RegistrationInput,db:Session=Depends(get_db)):
    email=data.email.strip().lower()
    if db.query(User).filter(User.email==email).first():
        raise HTTPException(409,'An account with this email already exists.')
    user_role=db.query(Role).filter(func.lower(Role.name)=='user').first()
    if not user_role:
        raise HTTPException(500,'User role is not configured.')
    user=User(name=data.name.strip(),email=email,password=hash_password(data.password),role_id=user_role.id)
    db.add(user); db.commit(); db.refresh(user)
    return {'id':user.id,'name':user.name,'email':user.email,'role':user_role.name,'message':'Account created. You can now sign in.'}

@router.post('/auth/login',response_model=Token)
def login(data:LoginInput,db:Session=Depends(get_db)):
    user=db.query(User).options(joinedload(User.role)).filter(User.email==data.email).first()
    if not user or not verify_password(data.password,user.password): raise HTTPException(401,'Incorrect email or password.')
    log(db,user.id,'login',f'{user.name} signed in'); db.commit(); return Token(access_token=create_token(user),role=user.role.name,name=user.name)

@router.get('/auth/users')
def users(_:User=Depends(admin_only),db:Session=Depends(get_db)):
    return [{'id':u.id,'name':u.name,'email':u.email,'role':u.role.name} for u in db.query(User).options(joinedload(User.role)).all()]

@router.get('/auth/me')
def me(user: User = Depends(current_user)):
    return {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role.name}

@router.get('/tasks')
def list_tasks(status:str|None=None,assigned_to:int|None=None,user:User=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(Task).options(joinedload(Task.assignee),joinedload(Task.creator))
    if user.role.name!='Admin': q=q.filter(Task.assigned_to==user.id)
    if status: q=q.filter(Task.status==status.lower())
    if assigned_to and user.role.name=='Admin': q=q.filter(Task.assigned_to==assigned_to)
    return [{'id':t.id,'title':t.title,'description':t.description,'status':t.status,'assigned_to':t.assigned_to,'assignee':t.assignee.name,'created_at':t.created_at} for t in q.order_by(desc(Task.created_at)).all()]

@router.post('/tasks')
def create_task(data:TaskCreate,user:User=Depends(admin_only),db:Session=Depends(get_db)):
    assignee=db.get(User,data.assigned_to)
    if not assignee: raise HTTPException(404,'Assignee not found.')
    task=Task(**data.model_dump(),created_by=user.id); db.add(task); log(db,user.id,'task_created',f'Assigned “{task.title}” to {assignee.name}'); db.commit(); db.refresh(task); return {'id':task.id,'message':'Task assigned.'}

@router.put('/tasks/{task_id}')
def update_task(task_id:int,data:TaskUpdate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    task=db.get(Task,task_id)
    if not task: raise HTTPException(404,'Task not found.')
    if user.role.name!='Admin' and task.assigned_to!=user.id: raise HTTPException(403,'You can only update your own tasks.')
    if data.status.lower() not in ('pending','completed'): raise HTTPException(422,'Status must be pending or completed.')
    task.status=data.status.lower(); log(db,user.id,'task_updated',f'{user.name} marked “{task.title}” as {task.status}'); db.commit(); return {'message':'Workboard updated.'}

@router.post('/documents')
async def upload_document(file:UploadFile=File(...),user:User=Depends(admin_only),db:Session=Depends(get_db)):
    suffix=Path(file.filename or '').suffix.lower()
    if suffix not in ('.pdf','.txt'): raise HTTPException(415,'Upload a PDF or TXT file.')
    safe_name=f'{user.id}_{file.filename}'; path=UPLOAD_DIR/safe_name; path.write_bytes(await file.read()); document=Document(filename=file.filename,file_path=str(path),uploaded_by=user.id); db.add(document); db.flush()
    try: count=add_document(document.id,document.filename,extract_text(path))
    except Exception as exc: db.rollback(); path.unlink(missing_ok=True); raise HTTPException(422,f'Could not process file: {exc}')
    log(db,user.id,'document_uploaded',f'Uploaded “{document.filename}” and indexed {count} knowledge sections'); db.commit(); return {'id':document.id,'chunks_indexed':count,'message':'Document added to the Library.'}

@router.get('/documents')
def documents(_:User=Depends(current_user),db:Session=Depends(get_db)):
    return [{'id':d.id,'filename':d.filename,'uploaded_by':d.uploader.name,'created_at':d.created_at} for d in db.query(Document).options(joinedload(Document.uploader)).order_by(desc(Document.created_at)).all()]

@router.get('/documents/{document_id}/file')
def open_document(document_id:int,_:User=Depends(current_user),db:Session=Depends(get_db)):
    document=db.get(Document,document_id)
    if not document: raise HTTPException(404,'Document not found.')
    path=Path(document.file_path).resolve()
    if UPLOAD_DIR.resolve() not in path.parents or not path.is_file(): raise HTTPException(404,'The uploaded file is no longer available.')
    media_type=guess_type(document.filename)[0] or 'application/octet-stream'
    return FileResponse(path,media_type=media_type,filename=document.filename,content_disposition_type='inline')

@router.post('/search')
def semantic_search(data:SearchInput,user:User=Depends(current_user),db:Session=Depends(get_db)):
    results=search(data.query,data.limit); log(db,user.id,'search',f'{user.name} searched for “{data.query}”'); db.commit(); return {'query':data.query,'results':results}

@router.get('/analytics')
def analytics(_:User=Depends(admin_only),db:Session=Depends(get_db)):
    total=db.query(Task).count(); completed=db.query(Task).filter(Task.status=='completed').count(); terms=db.query(ActivityLog.details,func.count(ActivityLog.id).label('count')).filter(ActivityLog.action=='search').group_by(ActivityLog.details).order_by(desc('count')).limit(5).all()
    return {'total_tasks':total,'completed_tasks':completed,'pending_tasks':total-completed,'documents':db.query(Document).count(),'popular_searches':[{'query':x[0].split('“')[-1].rstrip('”'),'count':x[1]} for x in terms],'activity':[{'action':a.action,'details':a.details,'created_at':a.created_at} for a in db.query(ActivityLog).order_by(desc(ActivityLog.created_at)).limit(8)]}
