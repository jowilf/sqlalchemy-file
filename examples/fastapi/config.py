from pydantic import BaseModel, BaseSettings


class BlobStorageSettings(BaseModel):
    key: str = "devstoreaccount1"
    secret: str = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
    host: str = "localhost"
    port: int = 10000
    secure: bool = False


class Config(BaseSettings):
    sqla_engine: str = "sqlite:///example.db?check_same_thread=False"
    secret: str = "123456789"
    storage: BlobStorageSettings = BlobStorageSettings()


config = Config()
