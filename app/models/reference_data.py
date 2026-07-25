from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import Script, enum_values


class Sector(Base):
    __tablename__ = "sectors"
    __table_args__ = (
        CheckConstraint("btrim(code) <> ''", name="code_not_blank"),
        CheckConstraint("btrim(name_en) <> ''", name="name_en_not_blank"),
        CheckConstraint("btrim(name_am) <> ''", name="name_am_not_blank"),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    name_am: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Market(Base):
    __tablename__ = "markets"
    __table_args__ = (
        CheckConstraint("btrim(code) <> ''", name="code_not_blank"),
        CheckConstraint("btrim(name_en) <> ''", name="name_en_not_blank"),
        CheckConstraint("btrim(name_am) <> ''", name="name_am_not_blank"),
        CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="latitude_range",
        ),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="longitude_range",
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    name_am: Mapped[str] = mapped_column(String(160), nullable=False)
    city_en: Mapped[str] = mapped_column(String(160), nullable=False)
    city_am: Mapped[str] = mapped_column(String(160), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Commodity(Base):
    __tablename__ = "commodities"
    __table_args__ = (
        CheckConstraint("btrim(code) <> ''", name="code_not_blank"),
        CheckConstraint("btrim(name_en) <> ''", name="name_en_not_blank"),
        CheckConstraint("btrim(name_am) <> ''", name="name_am_not_blank"),
        CheckConstraint("btrim(canonical_unit) <> ''", name="canonical_unit_not_blank"),
        Index("ix_commodities_sector_id_is_active", "sector_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    sector_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("sectors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False)
    name_am: Mapped[str] = mapped_column(String(160), nullable=False)
    canonical_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class CommoditySynonym(Base):
    __tablename__ = "commodity_synonyms"
    __table_args__ = (
        UniqueConstraint(
            "normalized",
            "script",
            name="uq_commodity_synonyms_normalized_script",
        ),
        CheckConstraint("btrim(surface) <> ''", name="surface_not_blank"),
        CheckConstraint("btrim(normalized) <> ''", name="normalized_not_blank"),
        Index("ix_commodity_synonyms_commodity_id", "commodity_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    commodity_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("commodities.id", ondelete="RESTRICT"),
        nullable=False,
    )
    surface: Mapped[str] = mapped_column(String(160), nullable=False)
    normalized: Mapped[str] = mapped_column(String(160), nullable=False)
    script: Mapped[Script] = mapped_column(
        SqlEnum(
            Script,
            name="commodity_synonym_script",
            native_enum=False,
            create_constraint=True,
            values_callable=enum_values,
            length=16,
        ),
        nullable=False,
    )


class UnitConversion(Base):
    __tablename__ = "unit_conversions"
    __table_args__ = (
        UniqueConstraint(
            "commodity_id",
            "source_unit",
            name="uq_unit_conversions_commodity_source_unit",
        ),
        CheckConstraint("btrim(source_unit) <> ''", name="source_unit_not_blank"),
        CheckConstraint("conversion_factor > 0", name="factor_positive"),
        Index("ix_unit_conversions_commodity_id", "commodity_id"),
        Index(
            "uq_unit_conversions_default_commodity",
            "commodity_id",
            unique=True,
            postgresql_where=text("is_default"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    commodity_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("commodities.id", ondelete="RESTRICT"),
        nullable=False,
    )
    source_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    conversion_factor: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
