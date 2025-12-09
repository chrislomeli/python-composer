from pydantic import BaseModel

class DatabaseLogin(BaseModel):
    database: str
    user: str
    password: str
    host: str
    port: int

    def toURL(self):
        return f'postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'