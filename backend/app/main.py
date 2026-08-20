from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base,engine,SessionLocal
from app.models.models import Role,User
from app.core.security import hash_password
from app.api.routes import router
app=FastAPI(title='Mosaic API',version='1.0.0'); app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_credentials=True,allow_methods=['*'],allow_headers=['*']); app.include_router(router)
@app.on_event('startup')
def setup():
    Base.metadata.create_all(engine); db=SessionLocal()
    try:
        admin=db.query(Role).filter_by(name='Admin').first() or Role(name='Admin'); user_role=db.query(Role).filter_by(name='User').first() or Role(name='User'); db.add_all([admin,user_role]); db.flush()
        if not db.query(User).filter_by(email='admin@mosaic.local').first(): db.add(User(name='Pragathi',email='admin@mosaic.local',password=hash_password('Admin@123'),role_id=admin.id))
        if not db.query(User).filter_by(email='priya@mosaic.local').first(): db.add(User(name='Priya Sharma',email='priya@mosaic.local',password=hash_password('User@123'),role_id=user_role.id))
        db.commit()
    finally: db.close()
@app.get('/health')
def health(): return {'status':'ready','product':'Mosaic'}
