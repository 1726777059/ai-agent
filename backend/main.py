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


# ─── 积分系统 ──────────────────────────────────

@app.get("/points")
def api_points():
    """获取当前积分状态"""
    sb = get_sb()
    row = sb.table("user_points").select("*").limit(1).execute()
    if row.data:
        return row.data[0]
    # auto-init
    sb.table("user_points").insert({"total_points": 0, "current_streak": 0, "max_streak": 0, "multiplier": 1.0}).execute()
    return {"total_points": 0, "current_streak": 0, "max_streak": 0, "multiplier": 1.0}


class AwardPayload(BaseModel):
    reason: str = "flashcard_mastered"  # flashcard_mastered | quiz_correct | streak_bonus | achievement


@app.post("/points/award")
def api_award(payload: AwardPayload):
    """答对一题 + 积分, 处理连击倍率"""
    sb = get_sb()
    row = sb.table("user_points").select("*").limit(1).execute()
    if not row.data:
        sb.table("user_points").insert({"total_points": 0, "current_streak": 0, "max_streak": 0, "multiplier": 1.0}).execute()
        pts = {"total_points": 0, "current_streak": 0, "max_streak": 0, "multiplier": 1.0}
    else:
        pts = row.data[0]

    streak = pts.get("current_streak", 0) + 1
    multiplier = float(pts.get("multiplier", 1.0))

    # every 10-streak, +0.2 multiplier, cap 3.0
    if streak > 0 and streak % 10 == 0:
        multiplier = min(3.0, multiplier + 0.2)

    earned = round(1 * multiplier, 1)
    total = (pts.get("total_points", 0) or 0) + earned
    max_streak = max(pts.get("max_streak", 0), streak)

    sb.table("user_points").update({
        "total_points": total,
        "current_streak": streak,
        "max_streak": max_streak,
        "multiplier": multiplier,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", pts["id"]).execute()

    # log
    sb.table("point_logs").insert({
        "points_earned": earned,
        "multiplier": multiplier,
        "reason": payload.reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    return {
        "total_points": total,
        "current_streak": streak,
        "max_streak": max_streak,
        "multiplier": multiplier,
        "earned": earned,
    }


@app.post("/points/reset")
def api_reset():
    """答错重置连击"""
    sb = get_sb()
    row = sb.table("user_points").select("*").limit(1).execute()
    if not row.data:
        return {"msg": "no data"}
    sb.table("user_points").update({
        "current_streak": 0,
        "multiplier": 1.0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", row.data[0]["id"]).execute()
    return {
        "total_points": row.data[0].get("total_points", 0),
        "current_streak": 0,
        "multiplier": 1.0,
    }


@app.get("/points/history")
def api_points_history(limit: int = 20):
    """积分变动日志"""
    sb = get_sb()
    rows = sb.table("point_logs").select("*").order("created_at", desc=True).limit(limit).execute()
    return rows.data or []


# ─── 奖品系统 ──────────────────────────────────

@app.get("/prizes")
def api_prizes():
    """奖品库列表"""
    sb = get_sb()
    rows = sb.table("prize_library").select("*").order("cost", desc=False).execute()
    return rows.data or []


@app.get("/prizes/mine")
def api_my_prizes():
    """我已获得的奖品"""
    sb = get_sb()
    rows = sb.table("user_prizes").select("*, prize_library(name, icon, type, description)").execute()
    return rows.data or []


class RedeemPayload(BaseModel):
    prize_id: str


@app.post("/prizes/redeem")
def api_redeem(payload: RedeemPayload):
    """兑换奖品"""
    sb = get_sb()

    # get prize
    prize = sb.table("prize_library").select("*").eq("id", payload.prize_id).execute()
    if not prize.data:
        raise HTTPException(404, "奖品不存在")
    prize = prize.data[0]

    # check already owned
    owned = sb.table("user_prizes").select("id").eq("prize_id", payload.prize_id).execute()
    if owned.data:
        raise HTTPException(400, "已拥有该奖品")

    # check points for cost
    if prize["cost"] > 0:
        pts = sb.table("user_points").select("*").limit(1).execute()
        if not pts.data or (pts.data[0].get("total_points", 0) or 0) < prize["cost"]:
            raise HTTPException(400, "积分不足")

        # deduct points
        sb.table("user_points").update({
            "total_points": (pts.data[0].get("total_points", 0) or 0) - prize["cost"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", pts.data[0]["id"]).execute()

        # log deduction
        sb.table("point_logs").insert({
            "points_earned": -prize["cost"],
            "multiplier": pts.data[0].get("multiplier", 1.0),
            "reason": "achievement",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

    # award prize
    sb.table("user_prizes").insert({
        "prize_id": payload.prize_id,
        "earned_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    return {"msg": f"🎉 成功兑换：{prize['name']}！"}


# ─── 统计扩展 ──────────────────────────────────

@app.get("/stats/heatmap")
def api_heatmap():
    """知识热力图数据：过去30天的知识点×日期矩阵"""
    sb = get_sb()
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    days = 30
    start = (now - timedelta(days=days)).isoformat()

    attempts = (
        sb.table("quiz_attempts")
        .select("*, quiz_questions(knowledge_point)")
        .gte("created_at", start)
        .eq("graded", True)
        .order("created_at", desc=False)
        .execute()
    ).data or []

    # Build matrix: {kp: {date: [correct, total]}}
    matrix = {}
    kps = []
    for a in attempts:
        q = a.get("quiz_questions", {}) or {}
        kp = q.get("knowledge_point", "")
        if not kp:
            continue
        d = a["created_at"][:10]  # date only
        if kp not in matrix:
            matrix[kp] = {}
            kps.append(kp)
        if d not in matrix[kp]:
            matrix[kp][d] = {"correct": 0, "total": 0}
        matrix[kp][d]["total"] += 1
        if a.get("is_correct"):
            matrix[kp][d]["correct"] += 1

    # Generate date list
    from datetime import timedelta
    dates = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days, -1, -1)]

    # Convert to percentage
    heatmap = {}
    for kp in matrix:
        heatmap[kp] = {}
        for d, v in matrix[kp].items():
            heatmap[kp][d] = round(v["correct"] / v["total"] * 100) if v["total"] > 0 else 0

    return {"kps": kps, "dates": dates, "matrix": heatmap}


@app.get("/stats/history")
def api_history(limit: int = 30):
    """答题记录详情"""
    sb = get_sb()
    attempts = (
        sb.table("quiz_attempts")
        .select("*, quiz_questions(question, knowledge_point, correct_index, explanation)")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    ).data or []
    return attempts


@app.get("/health")
def health():
    return {"status": "ok"}
