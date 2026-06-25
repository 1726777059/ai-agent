-- AI 学习助手 Supabase 建表脚本
-- 在 Supabase SQL Editor 中执行此文件

-- 1. 闪卡库
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
