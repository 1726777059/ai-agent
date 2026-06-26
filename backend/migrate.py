"""
Auto-migration: runs on every startup via the startup event in main.py.
Uses Supabase RPC (exec_sql) to create missing tables automatically.

One-time setup: run schema.sql in SQL Editor ONCE (creates exec_sql function).
After that, all table creation is automatic on deploy.
"""
from supabase import Client


def run_migrations(sb: Client):
    """Idempotent — safe to run every startup. Uses service_role for DDL."""

    tables = {
        "flashcard_bank": """
            CREATE TABLE IF NOT EXISTS flashcard_bank (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                phase TEXT NOT NULL,
                chapter TEXT NOT NULL,
                step TEXT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                image_url TEXT,
                tags TEXT[] DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "mastery_scores": """
            CREATE TABLE IF NOT EXISTS mastery_scores (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                flashcard_id UUID REFERENCES flashcard_bank(id) ON DELETE CASCADE,
                knowledge_point TEXT NOT NULL UNIQUE,
                phase TEXT,
                score INT DEFAULT 50 CHECK (score >= 0 AND score <= 100),
                total_reviews INT DEFAULT 0,
                total_quiz INT DEFAULT 0,
                total_correct INT DEFAULT 0,
                last_review_at TIMESTAMPTZ,
                last_quiz_at TIMESTAMPTZ,
                streak INT DEFAULT 0
            )
        """,
        "quiz_questions": """
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                flashcard_id UUID REFERENCES flashcard_bank(id) ON DELETE SET NULL,
                knowledge_point TEXT,
                type TEXT NOT NULL CHECK (type IN ('true_false', 'single_choice')),
                difficulty INT DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 3),
                question TEXT NOT NULL,
                options JSONB NOT NULL,
                correct_index INT NOT NULL,
                explanation TEXT,
                active BOOLEAN DEFAULT true,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "quiz_sessions": """
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                mode TEXT NOT NULL,
                strategy TEXT,
                total INT DEFAULT 0,
                correct INT DEFAULT 0,
                graded BOOLEAN DEFAULT false,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "quiz_attempts": """
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID REFERENCES quiz_sessions(id) ON DELETE CASCADE,
                question_id UUID REFERENCES quiz_questions(id) ON DELETE SET NULL,
                user_answer INT,
                is_correct BOOLEAN,
                graded BOOLEAN DEFAULT false,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "review_logs": """
            CREATE TABLE IF NOT EXISTS review_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                flashcard_id UUID REFERENCES flashcard_bank(id) ON DELETE SET NULL,
                knowledge_point TEXT,
                action TEXT CHECK (action IN ('mastered', 'not_mastered')),
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "user_points": """
            CREATE TABLE IF NOT EXISTS user_points (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                total_points INT DEFAULT 0,
                current_streak INT DEFAULT 0,
                max_streak INT DEFAULT 0,
                multiplier DECIMAL(3,1) DEFAULT 1.0,
                updated_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "point_logs": """
            CREATE TABLE IF NOT EXISTS point_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                points_earned INT NOT NULL,
                multiplier DECIMAL(3,1) DEFAULT 1.0,
                reason TEXT,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "prize_library": """
            CREATE TABLE IF NOT EXISTS prize_library (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                type TEXT CHECK (type IN ('badge', 'unlock', 'physical')),
                description TEXT,
                icon TEXT,
                cost INT DEFAULT 0,
                unlock_condition JSONB,
                created_at TIMESTAMPTZ DEFAULT now()
            )
        """,
        "user_prizes": """
            CREATE TABLE IF NOT EXISTS user_prizes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                prize_id UUID REFERENCES prize_library(id) ON DELETE CASCADE,
                earned_at TIMESTAMPTZ DEFAULT now()
            )
        """,
    }

    for name, sql in tables.items():
        try:
            # try to query — if table exists, this succeeds
            sb.table(name).select("id", count="exact").limit(1).execute()
        except Exception:
            # table missing — create via RPC
            try:
                sb.rpc("exec_sql", {"sql_text": sql}).execute()
                print(f"  ✅ Created table: {name}")
            except Exception as e:
                print(f"  ⚠️  Cannot create {name}: {e}")

    # ── RLS policies ──
    _ensure_rls(sb)

    # ── Seed data ──
    _seed_prizes(sb)
    _seed_user_points(sb)

    print("✅ Migrations complete")


def _ensure_rls(sb: Client):
    """Ensure anon role can read/write all tables."""
    table_list = [
        "flashcard_bank", "mastery_scores", "quiz_questions",
        "quiz_sessions", "quiz_attempts", "review_logs",
        "user_points", "point_logs", "prize_library", "user_prizes",
    ]
    for t in table_list:
        try:
            sb.rpc("exec_sql", {"sql_text": f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_read_{t}') THEN
                        CREATE POLICY "anon_read_{t}" ON {t} FOR SELECT TO anon USING (true);
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_write_{t}') THEN
                        CREATE POLICY "anon_write_{t}" ON {t} FOR INSERT TO anon WITH CHECK (true);
                    END IF;
                END
                $$;
            """}).execute()
        except Exception:
            pass  # RLS might already be set

    # Allow UPDATE on mutable tables
    for t in ["mastery_scores", "quiz_sessions", "quiz_attempts", "user_points"]:
        try:
            sb.rpc("exec_sql", {"sql_text": f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'anon_update_{t}') THEN
                        CREATE POLICY "anon_update_{t}" ON {t} FOR UPDATE TO anon USING (true);
                    END IF;
                END
                $$;
            """}).execute()
        except Exception:
            pass


def _seed_prizes(sb: Client):
    """Insert default prizes if empty."""
    try:
        r = sb.table("prize_library").select("id", count="exact").execute()
        if r.count == 0:
            prizes = [
                {"name":"一条裤子","type":"physical","description":"300 积分兑换","icon":"👖","cost":300},
                {"name":"一场话剧","type":"physical","description":"500 积分兑换","icon":"🎭","cost":500},
                {"name":"连续3天","type":"badge","description":"连续3天打卡学习","icon":"🔥","cost":0,"unlock_condition":{"streak":3}},
                {"name":"连续7天","type":"badge","description":"连续7天打卡学习","icon":"💪","cost":0,"unlock_condition":{"streak":7}},
            ]
            for p in prizes:
                sb.table("prize_library").insert(p).execute()
            print(f"  Seeded {len(prizes)} prizes")
    except Exception:
        pass


def _seed_user_points(sb: Client):
    """Init user_points if empty."""
    try:
        r = sb.table("user_points").select("id", count="exact").execute()
        if r.count == 0:
            sb.table("user_points").insert({
                "total_points": 0, "current_streak": 0,
                "max_streak": 0, "multiplier": 1.0,
            }).execute()
    except Exception:
        pass
