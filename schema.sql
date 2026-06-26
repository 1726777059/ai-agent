-- AI 学习助手 Supabase 建表脚本 v2
-- 在 Supabase SQL Editor 中执行此文件（仅需一次）

-- ═══ 核心：允许后端自动执行 DDL ═══
CREATE OR REPLACE FUNCTION exec_sql(sql_text TEXT) RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER
AS $$ BEGIN EXECUTE sql_text; END; $$;

-- 授权 service_role 调用（anon 无权调用，安全）
GRANT EXECUTE ON FUNCTION exec_sql(TEXT) TO service_role;

-- 1. 闪卡库
-- content 字段存 JSON: { front, back, blanks: [{pos, answer, options}] }
-- 由 Claude Code 入库时生成，前端 JSON.parse 渲染
CREATE TABLE flashcard_bank (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase TEXT NOT NULL,
    chapter TEXT NOT NULL,
    step TEXT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    image_url TEXT,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. 掌握度
CREATE TABLE mastery_scores (
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
);

-- 3. 题库
CREATE TABLE quiz_questions (
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
);

-- 4. 测验回合
CREATE TABLE quiz_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode TEXT NOT NULL,
    strategy TEXT,
    total INT DEFAULT 0,
    correct INT DEFAULT 0,
    graded BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. 答题记录
CREATE TABLE quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    question_id UUID REFERENCES quiz_questions(id) ON DELETE SET NULL,
    user_answer INT,
    is_correct BOOLEAN,
    graded BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 6. 复习日志
CREATE TABLE review_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flashcard_id UUID REFERENCES flashcard_bank(id) ON DELETE SET NULL,
    knowledge_point TEXT,
    action TEXT CHECK (action IN ('mastered', 'not_mastered')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX idx_flashcard_phase ON flashcard_bank(phase);
CREATE INDEX idx_flashcard_chapter ON flashcard_bank(chapter);
CREATE INDEX idx_mastery_score ON mastery_scores(score);
CREATE INDEX idx_mastery_last_review ON mastery_scores(last_review_at);
CREATE INDEX idx_mastery_last_quiz ON mastery_scores(last_quiz_at);
CREATE INDEX idx_quiz_kp ON quiz_questions(knowledge_point);
CREATE INDEX idx_attempts_session ON quiz_attempts(session_id);
CREATE INDEX idx_attempts_graded ON quiz_attempts(graded);
CREATE INDEX idx_review_logs_flashcard ON review_logs(flashcard_id);

-- 7. 用户积分（单用户，只有一条记录）
CREATE TABLE user_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    total_points INT DEFAULT 0,
    current_streak INT DEFAULT 0,
    max_streak INT DEFAULT 0,
    multiplier DECIMAL(3,1) DEFAULT 1.0,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 8. 积分日志
CREATE TABLE point_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    points_earned INT NOT NULL,
    multiplier DECIMAL(3,1) DEFAULT 1.0,
    reason TEXT CHECK (reason IN ('quiz_correct', 'flashcard_mastered', 'streak_bonus', 'achievement')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 9. 奖品库（预置数据）
CREATE TABLE prize_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT CHECK (type IN ('badge', 'unlock', 'physical')),
    description TEXT,
    icon TEXT,
    cost INT DEFAULT 0,
    unlock_condition JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 10. 用户奖品
CREATE TABLE user_prizes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prize_id UUID REFERENCES prize_library(id) ON DELETE CASCADE,
    earned_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX idx_point_logs_created ON point_logs(created_at);
CREATE INDEX idx_user_prizes_prize ON user_prizes(prize_id);

-- ═══ 预置奖品数据 ═══
INSERT INTO prize_library (name, type, description, icon, cost, unlock_condition) VALUES
('初出茅庐', 'badge', '完成第一次复习', '🌱', 0, '{"total_reviews": 1}'),
('连续7天', 'badge', '连续7天打卡学习', '🔥', 0, '{"streak": 7}'),
('百题斩', 'badge', '累计答对100题', '⚔️', 0, '{"total_correct": 100}'),
('Python大师', 'badge', 'Python知识点全部≥80分', '🐍', 0, '{"phase": "Python", "min_score": 80}'),
('解锁自定义复习', 'unlock', '解锁自定义筛选复习模式', '🔓', 500, NULL),
('解锁夜间模式', 'unlock', '解锁深色主题', '🌙', 200, NULL),
('一杯咖啡', 'physical', '你已获得一杯咖啡！(虚拟标记)', '☕', 1000, NULL),
('一本好书', 'physical', '你已获得一本好书！(虚拟标记)', '📚', 3000, NULL);
