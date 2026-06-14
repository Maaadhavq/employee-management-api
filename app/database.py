from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

DATABASE_URL = settings.DATABASE_URL
SQL_ECHO = settings.SQL_ECHO

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models.employee_orm import DepartmentORM
    Base.metadata.create_all(bind=engine)
    
    # Seed departments table if empty
    db = SessionLocal()
    try:
        if db.query(DepartmentORM).count() == 0:
            departments = [
                DepartmentORM(name="Engineering", description="Software development, QA and operations", cost_center="ENG-01"),
                DepartmentORM(name="Sales", description="Customer acquisition and account management", cost_center="SAL-02"),
                DepartmentORM(name="Marketing", description="Brand awareness, product marketing and PR", cost_center="MKT-03"),
                DepartmentORM(name="Human Resources", description="Talent acquisition, employee relations and culture", cost_center="HR-04"),
                DepartmentORM(name="Finance", description="Accounting, budget planning and financial analysis", cost_center="FIN-05"),
                DepartmentORM(name="Operations", description="Facility operations, logistics and support", cost_center="OPS-06"),
            ]
            db.bulk_save_objects(departments)
            db.commit()
    finally:
        db.close()
