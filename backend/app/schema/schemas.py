from pydantic import BaseModel, Field
# `str` intentionally permits the documented local demo accounts such as
# admin@mosaic.local, while real user creation would validate email separately.
class LoginInput(BaseModel): email: str=Field(min_length=5,max_length=120); password: str
class RegistrationInput(BaseModel): name: str=Field(min_length=2,max_length=100); email: str=Field(min_length=5,max_length=120); password: str=Field(min_length=8,max_length=128)
class Token(BaseModel): access_token: str; token_type: str='bearer'; role: str; name: str
class TaskCreate(BaseModel): title: str=Field(min_length=2,max_length=180); description: str=''; assigned_to: int
class TaskUpdate(BaseModel): status: str
class SearchInput(BaseModel): query: str=Field(min_length=2); limit: int=3
