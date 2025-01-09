import os
import json
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, joinedload


# Define the project root and the path to the database file
project_root = os.path.abspath(os.path.dirname(__file__) + "/..")
db_path = os.path.join(project_root, "data", "db_info.db")

# Ensure the `data` directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Define the DATABASE_URL and create the engine
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=True)


# Define a base class for our classes to inherit from
Base = declarative_base()

# Define the FileInfo model class
class DBInfo(Base):
    __tablename__ = "db_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    db_name = Column(String, nullable=False, unique=True)
    db_description = Column(String, nullable=False)
    connection_string = Column(String, nullable=False)
    erd_path = Column(String, nullable=False)
    # Establish a relationship with DBInfoDetails
    details = relationship("DBInfoDetails", back_populates="db_info", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DBInfo(name='{self.db_name}', connection_string='{self.connection_string}', erd_path='{self.erd_path}')>"

class DBInfoDetails(Base):
    __tablename__ = "db_info_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String, nullable=False)
    table_description = Column(String, nullable=False)
    column_descriptions = Column(String, nullable=True)
    df_head = Column(String, nullable=True)
    # Foreign key reference to DBInfo
    db_info_id = Column(Integer, ForeignKey("db_info.id", ondelete="CASCADE"), nullable=False)
    
    # Establish a relationship with DBInfo
    db_info = relationship("DBInfo", back_populates="details")

    def __repr__(self):
        return f"<DBInfoDetails(table_name='{self.table_name}', table_description='{self.table_description}', column_descriptions='{self.column_descriptions}', df_head='{self.df_head}', db_info_id='{self.db_info_id}')>"

# Create the file_info table
Base.metadata.create_all(engine)

# Create a sessionmaker bound to the engine
Session = sessionmaker(bind=engine)

def insert_db_info(data_dictionary):
    # data = json.loads(data_dictionary)
    session = Session()

    try:
        # Insert database overview into DBInfo
        db_info = DBInfo(
            db_name=data_dictionary["db_name"],
            db_description=data_dictionary["description"],
            connection_string=data_dictionary["connection_string"],
            erd_path=data_dictionary["erd_path"],
        )
        session.add(db_info)
        session.flush()  # Flush to get db_info.id without committing

        # Insert table details into DBInfoDetails
        for table in data_dictionary['tables']:
            table_name = table['name']
            table_description = table['description']
            column_descriptions = json.dumps(table['columns'])  # Store column details as JSON string
            sample_data = json.dumps(table['sample_data']) 
            db_info_details = DBInfoDetails(
                table_name=table_name,
                table_description=table_description,
                column_descriptions=column_descriptions,
                df_head=sample_data,
                db_info_id=db_info.id  # Use the flushed db_info.id
            )
            session.add(db_info_details)

        # Commit the transaction
        session.commit()
        print("Transaction committed successfully!")
    except SQLAlchemyError as e:
        # Rollback the transaction in case of an error
        session.rollback()
        print(f"Transaction failed! Rolled back due to error: {e}")

    finally:
        # Close the session
        session.close()




def if_db_exist(db_name):
    session = Session()
    try:
        existing_file = session.query(DBInfo).filter(func.lower(DBInfo.db_name) == db_name.lower()).first()
        if existing_file:
            return True
        else:
            return False
    except Exception as e:
        return False
    finally:
        session.close()
    

def get_db_info_by_dataset(db_name):
    session = Session()
    try:
        db = session.query(DBInfo).options(joinedload(DBInfo.details)).filter(func.lower(DBInfo.db_name) == db_name.lower()).first()
        db_info_data = {
            "db_name": db.db_name,
            "connection_string": db.connection_string,
            "db_description": db.db_description,
            "erd_path": db.erd_path,
            "details": [
                {"table_name": detail.table_name, 
                    "table_description": detail.table_description, 
                    "column_descriptions": detail.column_descriptions, 
                    "df_head": detail.df_head, 
                    "db_info_id": detail.db_info_id}
                for detail in db.details
            ]
        }
        return db_info_data
    finally:
        session.close()


def get_all_file_info():
    session = Session()
    try:
        # Use joinedload to eagerly load the related DBInfoDetails records
        db_info = session.query(DBInfo).options(joinedload(DBInfo.details)).all()

        # Construct the output list with DBInfo and associated DBInfoDetails data
        result = []
        for db in db_info:
            db_info_data = {
                "db_name": db.db_name,
                "connection_string": db.connection_string,
                "db_description": db.db_description,
                "erd_path": db.erd_path,
                "details": [
                    {"table_name": detail.table_name, 
                     "table_description": detail.table_description, 
                     "column_descriptions": detail.column_descriptions, 
                     "df_head": detail.df_head, 
                     "db_info_id": detail.db_info_id}
                    for detail in db.details
                ]
            }
            result.append(db_info_data)

        return result
    finally:
        session.close()


