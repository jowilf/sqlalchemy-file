from sqlmodel import create_engine

engine = create_engine("sqlite:///example.db?check_same_thread=False", echo=True)
