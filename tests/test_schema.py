from pathlib import Path
from uuid import UUID

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import Constraint, CreateIndex, CreateTable

import app.models  # noqa: F401
from app.database import Base

EXPECTED_TABLES = {
    "auth_sessions",
    "sectors",
    "markets",
    "commodities",
    "commodity_synonyms",
    "unit_conversions",
    "contributors",
    "contributor_consents",
    "agent_invite_codes",
    "agent_score_events",
    "agent_reward_settings",
    "agent_redeem_requests",
    "agent_applications",
    "submissions",
    "submission_verifications",
    "index_values",
    "users",
    "audit_log",
    "rate_limit_events",
    "invite_tokens",
}


def constraint_names(table_name: str, constraint_type: type[Constraint]) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {
        str(constraint.name)
        for constraint in table.constraints
        if isinstance(constraint, constraint_type)
    }


def test_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_commodities_require_a_sector() -> None:
    commodity = Base.metadata.tables["commodities"]
    sector_id = commodity.c.sector_id

    assert sector_id.nullable is False
    foreign_key = next(iter(sector_id.foreign_keys))
    assert foreign_key.target_fullname == "sectors.id"
    assert foreign_key.ondelete == "RESTRICT"


def test_operational_records_use_uuid_primary_keys() -> None:
    for table_name in (
        "auth_sessions",
        "contributors",
        "contributor_consents",
        "submissions",
        "submission_verifications",
        "index_values",
    ):
        primary_key = Base.metadata.tables[table_name].primary_key
        assert [column.name for column in primary_key.columns] == ["id"]
        assert primary_key.columns["id"].type.python_type is UUID


def test_auth_schema_constraints_exist() -> None:
    users = Base.metadata.tables["users"]
    sessions = Base.metadata.tables["auth_sessions"]
    user_checks = constraint_names("users", CheckConstraint)
    session_checks = constraint_names("auth_sessions", CheckConstraint)

    assert "ck_users_email_normalized" in user_checks
    assert "ck_users_auth_version_positive" in user_checks
    assert "ck_users_user_role" in user_checks
    assert "ck_users_user_status" in user_checks
    assert "ck_auth_sessions_refresh_hash_length" in session_checks
    assert "ck_auth_sessions_valid_expiry" in session_checks
    assert users.c.email.unique is True
    assert sessions.c.refresh_token_hash.unique is True


def test_contributor_can_link_to_one_user() -> None:
    contributor = Base.metadata.tables["contributors"]
    user_id = contributor.c.user_id

    assert user_id.nullable is True
    assert user_id.unique is True
    foreign_key = next(iter(user_id.foreign_keys))
    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "RESTRICT"


def test_submission_idempotency_and_provenance_constraints_exist() -> None:
    unique_constraints = constraint_names("submissions", UniqueConstraint)
    check_constraints = constraint_names("submissions", CheckConstraint)

    assert "uq_submissions_contributor_client_id" in unique_constraints
    assert "ck_submissions_contributor_required_for_direct_sources" in check_constraints
    assert "ck_submissions_parsed_fields_present" in check_constraints
    assert "ck_submissions_licence_class" in check_constraints


def test_review_events_allow_only_one_final_outcome() -> None:
    table = Base.metadata.tables["submission_verifications"]
    unique_constraints = constraint_names("submission_verifications", UniqueConstraint)
    final_index = next(
        index
        for index in table.indexes
        if index.name == "uq_submission_verifications_one_final_outcome"
    )

    assert "uq_submission_verifications_submission_outcome" in unique_constraints
    assert final_index.unique is True
    assert str(final_index.dialect_options["postgresql"]["where"]) == (
        "outcome IN ('accepted', 'flagged')"
    )


def test_index_snapshot_constraints_exist() -> None:
    check_constraints = constraint_names("index_values", CheckConstraint)
    unique_constraints = constraint_names("index_values", UniqueConstraint)

    assert "ck_index_values_status_matches_value" in check_constraints
    assert "ck_index_values_valid_window" in check_constraints
    assert "uq_index_values_trigger_method" in unique_constraints


def test_all_tables_and_indexes_compile_for_postgresql() -> None:
    dialect = postgresql.dialect()

    for table in Base.metadata.sorted_tables:
        assert str(CreateTable(table).compile(dialect=dialect))
        for index in table.indexes:
            assert str(CreateIndex(index).compile(dialect=dialect))


def test_migration_enforces_append_only_tables() -> None:
    migration = (
        Path(__file__).parents[1] / "migrations" / "versions" / "20260725_0001_initial_schema.py"
    ).read_text()

    assert "CREATE FUNCTION reject_append_only_change()" in migration
    assert "CREATE TRIGGER trg_{table_name}_append_only" in migration
    for table_name in (
        "contributor_consents",
        "submissions",
        "submission_verifications",
        "index_values",
    ):
        assert f'"{table_name}",' in migration
