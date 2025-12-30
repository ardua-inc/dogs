from abc import ABC, abstractmethod
from flask import current_app

class DatabaseInterface(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self, conn):
        pass

    @abstractmethod
    def init_db(self):
        pass

    @abstractmethod
    def execute(self, query, params=()):
        pass

    @abstractmethod
    def fetch_one(self, query, params=()):
        pass

    @abstractmethod
    def fetch_all(self, query, params=()):
        pass

    @abstractmethod
    def last_insert_id(self):
        pass

def get_db():
    db_type = current_app.config['DATABASE_TYPE']
    if db_type == 'sqlite':
        from dog_app.db_sqlite import SQLiteDatabase
        return SQLiteDatabase(current_app.config['DATABASE_CONFIG']['sqlite'])
    elif db_type == 'mysql':
        from dog_app.db_mysql import MySQLDatabase
        return MySQLDatabase(current_app.config['DATABASE_CONFIG']['mysql'])
    elif db_type == 'postgresql':
        from dog_app.db_postgresql import PostgreSQLDatabase
        return PostgreSQLDatabase(current_app.config['DATABASE_CONFIG']['postgresql'])
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
