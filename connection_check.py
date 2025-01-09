from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

def is_connection_ok(database_url):
    try:
        # Create a database engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as connection:
            print("Connection successful!")
            return True
        
    except SQLAlchemyError as e:
        print(f"Connection failed: {e}")
        return False
    finally:
        engine.dispose() 

def is_table_exist(database_url, table_name):
    try:
        # Create a database engine
        engine = create_engine(database_url)
        
        # Create an inspector
        inspector = inspect(engine)
        
        # Get the list of tables in the database
        table_names = inspector.get_table_names()
        # print(table_names)
        # print(f"Table Name: {table_name}")
        # Check if the target table exists
        if table_name in table_names:
            # print(f"Table '{table_name}' exists.")
            return True
        else:
            # print(f"Table '{table_name}' does NOT exist.")
            return False
    
    except SQLAlchemyError as e:
        print(f"Error occurred: {e}")
        return False
    finally:
        engine.dispose() 

def get_random_rows(database_url, table_name, row_count=5):
    try:
        # Construct the query to get random rows using PostgreSQL RANDOM()
        sql_query = f"SELECT * FROM {table_name} ORDER BY RANDOM() LIMIT {row_count}"
        
        engine = create_engine(database_url)
        
        df = pd.read_sql_query(sql_query, engine)
        for column in df.select_dtypes(include=["datetime", "object"]):
            df[column] = df[column].astype(str)
        return df
    except SQLAlchemyError as e:
        print(f"Error occurred: {e}")
        return None
    finally:
        engine.dispose() 


# Example usage
# database_url = "postgresql://postgres:postgres@localhost/ChinookDB"

# df = get_random_rows(database_url, "employee")
# print(df)


# engine = create_engine(database_url)
            # sql_query = f"SELECT * FROM {table_name} Limit 10"

            # df = pd.read_sql_query(sql_query, engine)
            # with engine.begin() as connection:
            #     results = connection.execute(text(sql_query))
            #     df = pd.DataFrame(results.fetchall())