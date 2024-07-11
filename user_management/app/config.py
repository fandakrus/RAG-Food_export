import os

class Config:
    BASE_DIR = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), os.pardir), os.pardir))
    print(BASE_DIR)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance/users.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False