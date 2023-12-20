from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class tbl_mobil_sports(Base):
    __tablename__ = 'tbl_mobil_sports'
    merk_mobil_sports: Mapped[str] = mapped_column(primary_key=True)
    cc: Mapped[int] = mapped_column()
    harga: Mapped[int] = mapped_column()
    speed: Mapped[int] = mapped_column()
    berat: Mapped[int] = mapped_column()
    kapasitas_bensin: Mapped[int] = mapped_column()
    
    def __repr__(self) -> str:
        return f"tbl_mobil_sports(merk_mobil_sports={self.merk_mobil_sports!r}, cc={self.cc!r})"