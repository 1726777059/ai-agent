"""
AI 学习助手 FastAPI 后端
前端只调 4 个接口，算法全在这里
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime, timezone

from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
from algorithms import get_entry_modes, get_flashcards, get_quiz_questions, compute_mastery_score

app = FastAPI(title="AI Study Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_sb() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_sb_admin() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY)


# ─── 前端 API ──────────────────────────────────

@app.get("/modes")
def api_modes():
    """入口弹窗：今日学习 / 继续章节 / 本周复习"""
    sb = get_sb()
    return get_entry_modes(sb)


@app.get("/flashcards")
def api_flashcards(kps: str = ""):
    """获取闪卡列表，kps 逗号分隔知识点"""
    if not kps:
        return []
    sb = get_sb()
    kp_list = [k.strip() for k in kps.split(",") if k.strip()]
    return get_flashcards(sb, kp_list)


@app.get("/quiz")
def api_quiz(kps: str = "", count: int = 5):
    """获取测验题目，kps 逗号分隔知识点"""
    if not kps:
        return []
    sb = get_sb()
    kp_list = [k.strip() for k in kps.split(",") if k.strip()]
    return get_quiz_questions(sb, kp_list, count)


class SubmitPayload(BaseModel):
    mode: str = "today"
    session_id: str = ""
    answers: list[dict]  # [{question_id, user_answer}]


@app.post("/quiz/submit")
def api_submit(payload: SubmitPayload):
    """提交答案，写入 quiz_sessions + quiz_attempts，等 Claude 批改"""
    sb = get_sb()

    # create session
    session = (
        sb.table("quiz_sessions")
        .insert({"mode": payload.mode, "total": len(payload.answers), "graded": False})
        .execute()
    ).data
    if not session:
        raise HTTPException(500, "Failed to create session")
    session_id = session[0]["id"]

    # insert attempts
    for ans in payload.answers:
        sb.table("quiz_attempts").insert({
            "session_id": session_id,
            "question_id": ans.get("question_id"),
            "user_answer": ans.get("user_answer"),
            "graded": False,
        }).execute()

    return {"session_id": session_id, "total": len(payload.answers), "msg": "已提交，告诉 Claude 批改"}


# ─── Claude 批改 API ──────────────────────────

@app.get("/internal/pending")
def api_pending():
    """Claude 读取所有待批改的 session"""
    sb = get_sb_admin()
    sessions = (
        sb.table("quiz_sessions")
        .select("*")
        .eq("graded", False)
        .order("created_at", desc=False)
        .execute()
    ).data or []
    result = []
    for s in sessions:
        attempts = (
            sb.table("quiz_attempts")
            .select("*, quiz_questions(question, options, correct_index, explanation, knowledge_point)")
            .eq("session_id", s["id"])
            .execute()
        ).data or []
        result.append({**s, "attempts": attempts})
    return result


class GradePayload(BaseModel):
    session_id: str
    results: list[dict]  # [{attempt_id, is_correct}]


@app.post("/internal/grade")
def api_grade(payload: GradePayload):
    """Claude 批改后回写结果 + 更新掌握度"""
    sb = get_sb_admin()

    correct_count = 0
    total = len(payload.results)

    for r in payload.results:
        sb.table("quiz_attempts").update({
            "is_correct": r["is_correct"],
            "graded": True,
        }).eq("id", r["attempt_id"]).execute()

        if r["is_correct"]:
            correct_count += 1

    # 更新 session
    sb.table("quiz_sessions").update({
        "correct": correct_count,
        "graded": True,
    }).eq("id", payload.session_id).execute()

    # 按知识点汇总，更新 mastery_scores
    attempts = (
        sb.table("quiz_attempts")
        .select("*, quiz_questions(knowledge_point)")
        .eq("session_id", payload.session_id)
        .execute()
    ).data or []

    kp_stats = {}
    for a in attempts:
        q = a.get("quiz_questions", {}) or {}
        kp = q.get("knowledge_point", "")
        if not kp:
            continue
        kp_stats.setdefault(kp, {"total": 0, "correct": 0})
        kp_stats[kp]["total"] += 1
        kp_stats[kp]["correct"] += 1 if a.get("is_correct") else 0

    now = datetime.now(timezone.utc).isoformat()
    for kp, stats in kp_stats.items():
        old = (
            sb.table("mastery_scores").select("id, score, total_quiz, total_correct")
            .eq("knowledge_point", kp).execute()
        ).data
        if old:
            rate = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            new_score = compute_mastery_score(old[0]["score"], rate)
            sb.table("mastery_scores").update({
                "score": new_score,
                "total_quiz": old[0]["total_quiz"] + stats["total"],
                "total_correct": old[0]["total_correct"] + stats["correct"],
                "last_quiz_at": now,
            }).eq("knowledge_point", kp).execute()

    return {"session_id": payload.session_id, "correct": correct_count, "total": total}


# ─── 复习操作 API ──────────────────────────────

class ReviewPayload(BaseModel):
    flashcard_id: str
    knowledge_point: str
    action: str  # "mastered" or "not_mastered"


@app.post("/review")
def api_review(payload: ReviewPayload):
    """闪卡复习：点 👍 或 👎 后调用"""
    sb = get_sb()

    # 写复习日志
    sb.table("review_logs").insert({
        "flashcard_id": payload.flashcard_id,
        "knowledge_point": payload.knowledge_point,
        "action": payload.action,
    }).execute()

    # 更新掌握度
    now = datetime.now(timezone.utc).isoformat()
    old = (
        sb.table("mastery_scores").select("id, score, total_reviews")
        .eq("knowledge_point", payload.knowledge_point).execute()
    ).data

    if old:
        delta = 10 if payload.action == "mastered" else -5
        new_score = max(0, min(100, old[0]["score"] + delta))
        sb.table("mastery_scores").update({
            "score": new_score,
            "total_reviews": old[0]["total_reviews"] + 1,
            "last_review_at": now,
        }).eq("knowledge_point", payload.knowledge_point).execute()
        return {"knowledge_point": payload.knowledge_point, "new_score": new_score}

    return {"msg": "knowledge_point not found"}


@app.get("/stats")
def api_stats():
    """统计面板数据"""
    sb = get_sb()
    rows = (
        sb.table("mastery_scores").select("knowledge_point, score, phase, last_review_at, total_reviews, total_quiz, total_correct, streak")
        .order("score", desc=False).execute()
    ).data or []

    total_reviews = sum(r.get("total_reviews", 0) for r in rows)
    total_quiz = sum(r.get("total_quiz", 0) for r in rows)
    total_correct = sum(r.get("total_correct", 0) for r in rows)
    avg_correct = round(total_correct / total_quiz * 100) if total_quiz > 0 else 0

    recent = (
        sb.table("quiz_sessions").select("mode, correct, total, created_at")
        .eq("graded", True).order("created_at", desc=False).limit(5).execute()
    ).data or []

    weak = rows[:3] if rows else []

    return {
        "total_reviews": total_reviews,
        "total_quiz": total_quiz,
        "avg_correct": avg_correct,
        "weak_top3": [{"kp": r["knowledge_point"], "score": r["score"]} for r in weak],
        "recent": recent,
        "distribution": {
            "low": sum(1 for r in rows if r["score"] < 40),
            "mid": sum(1 for r in rows if 40 <= r["score"] <= 70),
            "high": sum(1 for r in rows if r["score"] > 70),
        },
    }


@app.get("/health")
def health():
    return {"status": "ok"}
