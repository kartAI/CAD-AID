
from abc import ABC, abstractmethod
from fastapi import  Depends
from typing import Optional
from shared.utils.metadata import Metadata
from sqlalchemy.orm import Session

class MetadataStorage(ABC):
    @abstractmethod
    def save(self, metadata: "Metadata"):
        pass

    @abstractmethod
    def get(self, filename: str) -> Optional["Metadata"]:
        pass

class InMemoryMetadataStorage(MetadataStorage):
    def __init__(self) -> None:
        self.metadata_store = {}
    
    def save(self, metadata: 'Metadata'):
        self.metadata_store[metadata.filename] = metadata
    
    def get(self, filename: str) -> Optional['Metadata']:
        return self.metadata_store.get(filename, None)


class DatabaseMetadataStorage(MetadataStorage):
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, metadata: Metadata):
        self.session.add(metadata)
        self.session.commit()
    
    def get(self, filename: str) -> Optional[Metadata]:
        return self.session.query(Metadata).filter(Metadata.filename == filename).first()

