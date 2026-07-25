"""Create the initial Waga Index schema.

Revision ID: 20260725_0001
Revises:
Create Date: 2026-07-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260725_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sectors",
        sa.Column("id", sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_en", sa.String(length=160), nullable=False),
        sa.Column("name_am", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("btrim(code) <> ''", name="code_not_blank"),
        sa.CheckConstraint("btrim(name_am) <> ''", name="name_am_not_blank"),
        sa.CheckConstraint("btrim(name_en) <> ''", name="name_en_not_blank"),
        sa.PrimaryKeyConstraint("id", name="pk_sectors"),
        sa.UniqueConstraint("code", name="uq_sectors_code"),
    )

    op.create_table(
        "markets",
        sa.Column("id", sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_en", sa.String(length=160), nullable=False),
        sa.Column("name_am", sa.String(length=160), nullable=False),
        sa.Column("city_en", sa.String(length=160), nullable=False),
        sa.Column("city_am", sa.String(length=160), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("btrim(code) <> ''", name="code_not_blank"),
        sa.CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="latitude_range",
        ),
        sa.CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="longitude_range",
        ),
        sa.CheckConstraint("btrim(name_am) <> ''", name="name_am_not_blank"),
        sa.CheckConstraint("btrim(name_en) <> ''", name="name_en_not_blank"),
        sa.PrimaryKeyConstraint("id", name="pk_markets"),
        sa.UniqueConstraint("code", name="uq_markets_code"),
    )

    op.create_table(
        "contributors",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("external_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            sa.String(length=16),
            server_default=sa.text("'user'"),
            nullable=False,
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('user', 'agent', 'team')",
            name="contributor_kind",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_contributors"),
        sa.UniqueConstraint("external_id", name="uq_contributors_external_id"),
    )

    op.create_table(
        "commodities",
        sa.Column("id", sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column("sector_id", sa.SmallInteger(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name_en", sa.String(length=160), nullable=False),
        sa.Column("name_am", sa.String(length=160), nullable=False),
        sa.Column("canonical_unit", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "btrim(canonical_unit) <> ''",
            name="canonical_unit_not_blank",
        ),
        sa.CheckConstraint("btrim(code) <> ''", name="code_not_blank"),
        sa.CheckConstraint("btrim(name_am) <> ''", name="name_am_not_blank"),
        sa.CheckConstraint("btrim(name_en) <> ''", name="name_en_not_blank"),
        sa.ForeignKeyConstraint(
            ["sector_id"],
            ["sectors.id"],
            name="fk_commodities_sector_id_sectors",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_commodities"),
        sa.UniqueConstraint("code", name="uq_commodities_code"),
    )
    op.create_index(
        "ix_commodities_sector_id_is_active",
        "commodities",
        ["sector_id", "is_active"],
        unique=False,
    )

    op.create_table(
        "commodity_synonyms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("commodity_id", sa.SmallInteger(), nullable=False),
        sa.Column("surface", sa.String(length=160), nullable=False),
        sa.Column("normalized", sa.String(length=160), nullable=False),
        sa.Column("script", sa.String(length=16), nullable=False),
        sa.CheckConstraint(
            "script IN ('ethiopic', 'latin', 'english')",
            name="commodity_synonym_script",
        ),
        sa.CheckConstraint(
            "btrim(normalized) <> ''",
            name="normalized_not_blank",
        ),
        sa.CheckConstraint(
            "btrim(surface) <> ''",
            name="surface_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["commodity_id"],
            ["commodities.id"],
            name="fk_commodity_synonyms_commodity_id_commodities",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_commodity_synonyms"),
        sa.UniqueConstraint(
            "normalized",
            "script",
            name="uq_commodity_synonyms_normalized_script",
        ),
    )
    op.create_index(
        "ix_commodity_synonyms_commodity_id",
        "commodity_synonyms",
        ["commodity_id"],
        unique=False,
    )

    op.create_table(
        "unit_conversions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("commodity_id", sa.SmallInteger(), nullable=False),
        sa.Column("source_unit", sa.String(length=32), nullable=False),
        sa.Column("conversion_factor", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.CheckConstraint(
            "conversion_factor > 0",
            name="factor_positive",
        ),
        sa.CheckConstraint(
            "btrim(source_unit) <> ''",
            name="source_unit_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["commodity_id"],
            ["commodities.id"],
            name="fk_unit_conversions_commodity_id_commodities",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_unit_conversions"),
        sa.UniqueConstraint(
            "commodity_id",
            "source_unit",
            name="uq_unit_conversions_commodity_source_unit",
        ),
    )
    op.create_index(
        "ix_unit_conversions_commodity_id",
        "unit_conversions",
        ["commodity_id"],
        unique=False,
    )
    op.create_index(
        "uq_unit_conversions_default_commodity",
        "unit_conversions",
        ["commodity_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )

    op.create_table(
        "contributor_consents",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("contributor_id", sa.Uuid(), nullable=False),
        sa.Column("consent_version", sa.String(length=64), nullable=False),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "btrim(consent_version) <> ''",
            name="version_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["contributor_id"],
            ["contributors.id"],
            name="fk_contributor_consents_contributor_id_contributors",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_contributor_consents"),
        sa.UniqueConstraint(
            "contributor_id",
            "consent_version",
            name="uq_contributor_consents_contributor_version",
        ),
    )
    op.create_index(
        "ix_contributor_consents_contributor_id",
        "contributor_consents",
        ["contributor_id"],
        unique=False,
    )

    op.create_table(
        "submissions",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("client_submission_id", sa.Uuid(), nullable=False),
        sa.Column("contributor_id", sa.Uuid(), nullable=True),
        sa.Column("market_id", sa.SmallInteger(), nullable=True),
        sa.Column("commodity_id", sa.SmallInteger(), nullable=True),
        sa.Column("price_raw", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("unit_raw", sa.String(length=32), nullable=True),
        sa.Column("price_canonical", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("unit_canonical", sa.String(length=32), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column(
            "licence_class",
            sa.String(length=32),
            server_default=sa.text("'internal_only'"),
            nullable=False,
        ),
        sa.Column("parse_status", sa.String(length=16), nullable=False),
        sa.Column("parse_method", sa.String(length=16), nullable=False),
        sa.Column(
            "input_mode",
            sa.String(length=16),
            server_default=sa.text("'rest'"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "contributor_id IS NOT NULL OR source IN ('scraped', 'seed')",
            name="contributor_required_for_direct_sources",
        ),
        sa.CheckConstraint(
            "input_mode IN ('rest')",
            name="submission_input_mode",
        ),
        sa.CheckConstraint(
            "licence_class IN "
            "('commercial_permitted', 'internal_only', 'display_only')",
            name="licence_class",
        ),
        sa.CheckConstraint(
            "parse_method IN ('structured', 'dictionary', 'fuzzy')",
            name="submission_parse_method",
        ),
        sa.CheckConstraint(
            "parse_status IN ('parsed', 'ambiguous', 'unparsed')",
            name="submission_parse_status",
        ),
        sa.CheckConstraint(
            "parse_status <> 'parsed' OR "
            "(market_id IS NOT NULL AND commodity_id IS NOT NULL "
            "AND price_canonical IS NOT NULL AND unit_canonical IS NOT NULL)",
            name="parsed_fields_present",
        ),
        sa.CheckConstraint(
            "price_canonical IS NULL OR price_canonical > 0",
            name="price_canonical_positive",
        ),
        sa.CheckConstraint(
            "price_raw IS NULL OR price_raw > 0",
            name="price_raw_positive",
        ),
        sa.CheckConstraint(
            "source IN ('user', 'agent', 'scraped', 'seed')",
            name="submission_source",
        ),
        sa.ForeignKeyConstraint(
            ["commodity_id"],
            ["commodities.id"],
            name="fk_submissions_commodity_id_commodities",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["contributor_id"],
            ["contributors.id"],
            name="fk_submissions_contributor_id_contributors",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["market_id"],
            ["markets.id"],
            name="fk_submissions_market_id_markets",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_submissions"),
        sa.UniqueConstraint(
            "contributor_id",
            "client_submission_id",
            name="uq_submissions_contributor_client_id",
        ),
    )
    op.create_index(
        "ix_submissions_contributor_id",
        "submissions",
        ["contributor_id"],
        unique=False,
    )
    op.create_index(
        "ix_submissions_market_commodity_received_at",
        "submissions",
        ["market_id", "commodity_id", sa.text("received_at DESC")],
        unique=False,
    )

    op.create_table(
        "submission_verifications",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("reviewer_label", sa.String(length=120), nullable=True),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "outcome IN ('pending', 'accepted', 'flagged')",
            name="review_outcome",
        ),
        sa.CheckConstraint(
            "outcome <> 'flagged' OR (reason IS NOT NULL AND btrim(reason) <> '')",
            name="reason_required_when_flagged",
        ),
        sa.CheckConstraint(
            "(outcome = 'pending' AND reviewer_label IS NULL) "
            "OR (outcome IN ('accepted', 'flagged') "
            "AND reviewer_label IS NOT NULL AND btrim(reviewer_label) <> '')",
            name="reviewer_required_for_final_outcome",
        ),
        sa.ForeignKeyConstraint(
            ["submission_id"],
            ["submissions.id"],
            name="fk_submission_verifications_submission_id_submissions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_submission_verifications"),
        sa.UniqueConstraint(
            "submission_id",
            "outcome",
            name="uq_submission_verifications_submission_outcome",
        ),
    )
    op.create_index(
        "ix_submission_verifications_submission_created_at",
        "submission_verifications",
        ["submission_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "uq_submission_verifications_one_final_outcome",
        "submission_verifications",
        ["submission_id"],
        unique=True,
        postgresql_where=sa.text("outcome IN ('accepted', 'flagged')"),
    )

    op.create_table(
        "index_values",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("market_id", sa.SmallInteger(), nullable=False),
        sa.Column("commodity_id", sa.SmallInteger(), nullable=False),
        sa.Column("trigger_verification_id", sa.Uuid(), nullable=False),
        sa.Column("method_version", sa.String(length=32), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("value", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("n_submissions", sa.Integer(), nullable=False),
        sa.Column("n_contributors", sa.Integer(), nullable=False),
        sa.Column(
            "source_mix",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.CheckConstraint(
            "n_contributors >= 0",
            name="contributor_count_nonnegative",
        ),
        sa.CheckConstraint(
            "btrim(method_version) <> ''",
            name="method_version_not_blank",
        ),
        sa.CheckConstraint(
            "(status = 'published' AND value IS NOT NULL) "
            "OR (status = 'insufficient_data' AND value IS NULL)",
            name="status_matches_value",
        ),
        sa.CheckConstraint(
            "status IN ('published', 'insufficient_data')",
            name="index_status",
        ),
        sa.CheckConstraint(
            "n_submissions >= 0",
            name="submission_count_nonnegative",
        ),
        sa.CheckConstraint("btrim(unit) <> ''", name="unit_not_blank"),
        sa.CheckConstraint(
            "window_start < window_end",
            name="valid_window",
        ),
        sa.ForeignKeyConstraint(
            ["commodity_id"],
            ["commodities.id"],
            name="fk_index_values_commodity_id_commodities",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["market_id"],
            ["markets.id"],
            name="fk_index_values_market_id_markets",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["trigger_verification_id"],
            ["submission_verifications.id"],
            name="fk_index_values_trigger_verification",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_index_values"),
        sa.UniqueConstraint(
            "trigger_verification_id",
            "method_version",
            name="uq_index_values_trigger_method",
        ),
    )
    op.create_index(
        "ix_index_values_market_commodity_computed_at",
        "index_values",
        ["market_id", "commodity_id", sa.text("computed_at DESC")],
        unique=False,
    )

    op.execute(
        """
        CREATE FUNCTION reject_append_only_change()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION '% is append-only', TG_TABLE_NAME
                USING ERRCODE = '55000';
            RETURN NULL;
        END;
        $$
        """
    )

    for table_name in (
        "contributor_consents",
        "submissions",
        "submission_verifications",
        "index_values",
    ):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table_name}_append_only
            BEFORE UPDATE OR DELETE ON {table_name}
            FOR EACH ROW
            EXECUTE FUNCTION reject_append_only_change()
            """
        )


def downgrade() -> None:
    for table_name in (
        "index_values",
        "submission_verifications",
        "submissions",
        "contributor_consents",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table_name}_append_only ON {table_name}")

    op.execute("DROP FUNCTION IF EXISTS reject_append_only_change()")

    op.drop_index(
        "ix_index_values_market_commodity_computed_at",
        table_name="index_values",
    )
    op.drop_table("index_values")

    op.drop_index(
        "uq_submission_verifications_one_final_outcome",
        table_name="submission_verifications",
    )
    op.drop_index(
        "ix_submission_verifications_submission_created_at",
        table_name="submission_verifications",
    )
    op.drop_table("submission_verifications")

    op.drop_index(
        "ix_submissions_market_commodity_received_at",
        table_name="submissions",
    )
    op.drop_index("ix_submissions_contributor_id", table_name="submissions")
    op.drop_table("submissions")

    op.drop_index(
        "ix_contributor_consents_contributor_id",
        table_name="contributor_consents",
    )
    op.drop_table("contributor_consents")

    op.drop_index(
        "uq_unit_conversions_default_commodity",
        table_name="unit_conversions",
    )
    op.drop_index("ix_unit_conversions_commodity_id", table_name="unit_conversions")
    op.drop_table("unit_conversions")

    op.drop_index(
        "ix_commodity_synonyms_commodity_id",
        table_name="commodity_synonyms",
    )
    op.drop_table("commodity_synonyms")

    op.drop_index(
        "ix_commodities_sector_id_is_active",
        table_name="commodities",
    )
    op.drop_table("commodities")
    op.drop_table("contributors")
    op.drop_table("markets")
    op.drop_table("sectors")
