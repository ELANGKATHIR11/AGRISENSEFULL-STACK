### Project Structure

Here's a suggested project structure for the AgriSense application:

```
agrisense/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── crops.py
│   │   ├── sensors.py
│   │   └── users.py
│   └── services/
│       ├── __init__.py
│       ├── crop_service.py
│       ├── sensor_service.py
│       └── user_service.py
│
├── requirements.txt
└── README.md
```

### Step 1: Set Up the Environment

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. **Install FastAPI and other dependencies**:
   ```bash
   pip install fastapi uvicorn sqlalchemy pydantic
   ```

3. **Create a `requirements.txt` file**:
   ```plaintext
   fastapi
   uvicorn
   sqlalchemy
   pydantic
   ```

### Step 2: Create the FastAPI Application

#### `app/main.py`

```python
from fastapi import FastAPI
from app.routers import crops, sensors, users

app = FastAPI()

app.include_router(crops.router)
app.include_router(sensors.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the AgriSense API"}
```

#### `app/models.py`

```python
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Crop(Base):
    __tablename__ = "crops"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)
    yield_per_hectare = Column(Float)

class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)
    location = Column(String)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
```

#### `app/schemas.py`

```python
from pydantic import BaseModel

class CropBase(BaseModel):
    name: str
    type: str
    yield_per_hectare: float

class CropCreate(CropBase):
    pass

class Crop(CropBase):
    id: int

    class Config:
        orm_mode = True

class SensorBase(BaseModel):
    name: str
    type: str
    location: str

class SensorCreate(SensorBase):
    pass

class Sensor(SensorBase):
    id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        orm_mode = True
```

#### `app/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./agrisense.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
```

#### `app/routers/crops.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/crops/", response_model=schemas.Crop)
def create_crop(crop: schemas.CropCreate, db: Session = Depends(get_db)):
    db_crop = models.Crop(**crop.dict())
    db.add(db_crop)
    db.commit()
    db.refresh(db_crop)
    return db_crop

@router.get("/crops/{crop_id}", response_model=schemas.Crop)
def read_crop(crop_id: int, db: Session = Depends(get_db)):
    return db.query(models.Crop).filter(models.Crop.id == crop_id).first()

@router.get("/crops/", response_model=list[schemas.Crop])
def read_crops(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.Crop).offset(skip).limit(limit).all()
```

#### `app/routers/sensors.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/sensors/", response_model=schemas.Sensor)
def create_sensor(sensor: schemas.SensorCreate, db: Session = Depends(get_db)):
    db_sensor = models.Sensor(**sensor.dict())
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor

@router.get("/sensors/{sensor_id}", response_model=schemas.Sensor)
def read_sensor(sensor_id: int, db: Session = Depends(get_db)):
    return db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()

@router.get("/sensors/", response_model=list[schemas.Sensor])
def read_sensors(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.Sensor).offset(skip).limit(limit).all()
```

#### `app/routers/users.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.User).filter(models.User.id == user_id).first()

@router.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(models.User).offset(skip).limit(limit).all()
```

### Step 3: Initialize the Database

You can initialize the database by adding the following code to your `main.py` file:

```python
from app.database import init_db

if __name__ == "__main__":
    init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 4: Run the Application

Run the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload
```

### Step 5: Test the API

You can test the API using tools like Postman or directly in your browser by navigating to `http://127.0.0.1:8000/docs` to access the automatically generated Swagger UI.

### Conclusion

This is a basic setup for the AgriSense application using FastAPI. You can expand upon this by adding more features, such as authentication, more complex business logic, or integrating with external APIs.