import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to SQLite file database in the backend directory, or use DATABASE_URL (e.g., PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./patient_journey.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes database tables and safely applies missing columns if upgrading."""
    from app.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Safe lightweight SQLite migration helper
    if DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check medical_events columns
            event_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(medical_events)")).fetchall()]
            if "importance_priority" not in event_cols:
                conn.execute(text("ALTER TABLE medical_events ADD COLUMN importance_priority VARCHAR(32) DEFAULT 'Moderate'"))
            if "importance_reason" not in event_cols:
                conn.execute(text("ALTER TABLE medical_events ADD COLUMN importance_reason TEXT"))
            if "evidence_level" not in event_cols:
                conn.execute(text("ALTER TABLE medical_events ADD COLUMN evidence_level VARCHAR(32) DEFAULT 'Strong'"))
            if "evidence_rationale" not in event_cols:
                conn.execute(text("ALTER TABLE medical_events ADD COLUMN evidence_rationale TEXT"))

            # Check change_events columns
            change_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(change_events)")).fetchall()]
            if "significance_category" not in change_cols:
                conn.execute(text("ALTER TABLE change_events ADD COLUMN significance_category VARCHAR(64) DEFAULT 'routine_change'"))
            if "previous_date" not in change_cols:
                conn.execute(text("ALTER TABLE change_events ADD COLUMN previous_date VARCHAR(32)"))
            if "new_date" not in change_cols:
                conn.execute(text("ALTER TABLE change_events ADD COLUMN new_date VARCHAR(32)"))
            if "source_evidence" not in change_cols:
                conn.execute(text("ALTER TABLE change_events ADD COLUMN source_evidence TEXT"))

            # Check conflicts columns
            conf_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(conflicts)")).fetchall()]
            if "conflicting_item" not in conf_cols:
                conn.execute(text("ALTER TABLE conflicts ADD COLUMN conflicting_item VARCHAR(128)"))
            if "source_a_date" not in conf_cols:
                conn.execute(text("ALTER TABLE conflicts ADD COLUMN source_a_date VARCHAR(32)"))
            if "source_b_date" not in conf_cols:
                conn.execute(text("ALTER TABLE conflicts ADD COLUMN source_b_date VARCHAR(32)"))
            if "source_a_page" not in conf_cols:
                conn.execute(text("ALTER TABLE conflicts ADD COLUMN source_a_page INTEGER DEFAULT 1"))
            if "source_b_page" not in conf_cols:
                conn.execute(text("ALTER TABLE conflicts ADD COLUMN source_b_page INTEGER DEFAULT 1"))
            if "review_reason" not in conf_cols:
                conn.execute(text("ALTER TABLE conflicts ADD COLUMN review_reason TEXT"))
            if "human_action_guidance" not in conf_cols:
                conn.execute(text("ALTER TABLE conflicts ADD COLUMN human_action_guidance TEXT"))
            if "resolution_notes" not in conf_cols:
                conn.execute(text("ALTER TABLE conflicts ADD COLUMN resolution_notes TEXT"))

            # Check timeline_gaps columns
            gap_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(timeline_gaps)")).fetchall()]
            if "gap_start_date" not in gap_cols:
                conn.execute(text("ALTER TABLE timeline_gaps ADD COLUMN gap_start_date VARCHAR(32)"))
            if "gap_end_date" not in gap_cols:
                conn.execute(text("ALTER TABLE timeline_gaps ADD COLUMN gap_end_date VARCHAR(32)"))
            if "clinical_context" not in gap_cols:
                conn.execute(text("ALTER TABLE timeline_gaps ADD COLUMN clinical_context TEXT"))
            if "review_recommendation" not in gap_cols:
                conn.execute(text("ALTER TABLE timeline_gaps ADD COLUMN review_recommendation TEXT"))

            conn.commit()


# Auto-initialize tables
init_db()


