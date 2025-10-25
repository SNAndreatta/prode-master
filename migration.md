Migration guidelines
====================

This project currently uses SQLAlchemy's `Base.metadata.create_all` in
`main.py` for quick local development. For production or repeatable
schema evolution we recommend using Alembic. Below are two practical
options you can follow:

Option A — Recommended: Alembic (structured migrations)
------------------------------------------------------

1. Install Alembic:

   pip install alembic

2. Initialize Alembic (run once):

   alembic init alembic

   This creates an `alembic/` directory and an `alembic.ini` file.

3. Configure `alembic.ini`

   - Set the sqlalchemy.url to your database URL or configure env var based loading
   - Update `alembic/env.py` to import your SQLAlchemy `Base` and target metadata:

     from database import Base
     target_metadata = Base.metadata

4. Create a new revision (autogenerate helps but verify the output):

   alembic revision --autogenerate -m "add points to predictions"

5. Edit the generated migration script if needed. Example op:

   def upgrade():
       op.add_column('predictions', sa.Column('points', sa.Integer(), nullable=True))

   def downgrade():
       op.drop_column('predictions', 'points')

6. Apply the migration:

   alembic upgrade head

7. Integration with `main.py` (optional):

   You can call Alembic programmatically on startup or use an orchestration
   step that runs `alembic upgrade head` during deploy. If you want to run
   Alembic at application start, modify `main.py` to call Alembic's API
   (see Alembic docs) — but prefer running migrations out-of-process in
   production.

Option B — Minimal, opt-in simple migrations (what this repo includes)
------------------------------------------------------------------

If you don't want to add Alembic yet, a tiny helper `migrations/run_simple_migrations.py`
is provided to run idempotent, focused SQL changes automatically on
startup when you enable the environment variable `RUN_SIMPLE_MIGRATIONS=1`.

Current helper
--------------
- Adds `predictions.points` as a nullable INTEGER if it does not exist.
- It is safe (idempotent) and intended as a stop-gap until Alembic is
  introduced.

To enable this helper on app startup, set the environment variable:

  export RUN_SIMPLE_MIGRATIONS=1

and start the app as usual. The startup logic calls the helper and
continues even if migration fails (it logs a warning).

Notes and recommendations
-------------------------
- Prefer Alembic for long-term/production projects. Alembic tracks
  migrations, generates downgrades, and supports branching.
- Keep migrations reviewed and part of your PRs — don't rely solely
  on automatic schema generation in `create_all` for production.
- If you add Alembic, remove or disable `RUN_SIMPLE_MIGRATIONS` in
  production environments to avoid double-applying schema changes.
