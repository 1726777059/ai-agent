"""
出题算法 / 遗忘曲线 / 掌握度计算

前端只传 mode + params，所有逻辑在这里算完返回结果。
"""

from datetime import datetime, timezone, timedelta
from supabase import Client


# 遗忘间隔（天）→ 权重系数，越久权重越高
FORGETTING_CURVE = {1: 1.0, 3: 1.5, 7: 2.0, 14: 2.5, 30: 3.0}


def get_entry_modes(sb: Client) -> dict:
    """返回入口弹窗的三个选项数据"""
    now = datetime.now(timezone.utc)

    # 今日学习：按遗忘曲线优先级
    today = _mode_today(sb, now)
    # 继续章节
    chapter = _mode_chapter(sb)
    # 本周复习
    weekly = _mode_weekly(sb, now)

    return {"today": today, "chapter": chapter, "weekly": weekly}


def _mode_today(sb: Client, now: datetime) -> dict:
    """今日学习：距今最久未复习 + 薄弱优先"""
    rows = (
        sb.table("mastery_scores")
        .select("knowledge_point, score, last_review_at, phase")
        .order("last_review_at", desc=False)
        .limit(20)
        .execute()
    ).data or []

    # 按遗忘曲线加权排序
    scored = []
    for r in rows:
        days = 999
        if r.get("last_review_at"):
            delta = now - datetime.fromisoformat(r["last_review_at"].replace("Z", "+00:00"))
            days = delta.days
        # 权重 = 遗忘系数 × (1 - score/100)
        forget_weight = 3.0 if days > 30 else FORGETTING_CURVE.get(days // 7 * 7, 1.0)
        priority = forget_weight * (1 - r.get("score", 50) / 100)
        scored.append({**r, "days_since": days, "priority": round(priority, 2)})

    scored.sort(key=lambda x: x["priority"], reverse=True)
    top = scored[:8]

    # count flashcard & quiz counts
    kps = [r["knowledge_point"] for r in top]
    fc_count = _count_flashcards(sb, kps)
    qz_count = _count_questions(sb, kps)

    return {
        "label": "今日学习",
        "desc": f"按遗忘曲线，今天该复习 {len(top)} 个知识点",
        "detail": ", ".join(r["knowledge_point"] for r in top[:3]),
        "knowledge_points": kps,
        "card_count": fc_count,
        "quiz_count": qz_count,
    }


def _mode_chapter(sb: Client) -> dict:
    """继续章节：从掌握度最低的 phase 中取"""
    rows = (
        sb.table("mastery_scores")
        .select("phase, knowledge_point, score")
        .order("score", desc=False)
        .limit(20)
        .execute()
    ).data or []

    if not rows:
        return {"label": "继续章节", "desc": "暂无数据", "knowledge_points": [], "card_count": 0, "quiz_count": 0}

    # 按 phase 分组，找最需要复习的 phase
    phases = {}
    for r in rows:
        p = r.get("phase", "Other")
        phases.setdefault(p, []).append(r)
    # 取 score 平均最低的 phase
    best_phase = min(phases, key=lambda p: sum(r["score"] for r in phases[p]) / len(phases[p]))
    kps = [r["knowledge_point"] for r in phases[best_phase][:8]]

    return {
        "label": "继续章节",
        "desc": f"最需复习: {best_phase}（{len(kps)} 个知识点）",
        "detail": best_phase,
        "knowledge_points": kps,
        "card_count": _count_flashcards(sb, kps),
        "quiz_count": _count_questions(sb, kps),
    }


def _mode_weekly(sb: Client, now: datetime) -> dict:
    """本周复习：本周学过的全部，薄弱优先"""
    week_ago = (now - timedelta(days=7)).isoformat()
    rows = (
        sb.table("mastery_scores")
        .select("knowledge_point, score, last_quiz_at, last_review_at")
        .gte("last_review_at", week_ago)
        .order("score", desc=False)
        .limit(20)
        .execute()
    ).data or []

    kps = [r["knowledge_point"] for r in rows[:12]]
    weak = rows[0]["knowledge_point"] if rows else ""
    weak_score = rows[0]["score"] if rows else 0

    return {
        "label": "本周复习",
        "desc": f"本周学了 {len(rows)} 个知识点，薄弱: {weak}({weak_score}%)",
        "knowledge_points": kps,
        "card_count": _count_flashcards(sb, kps),
        "quiz_count": _count_questions(sb, kps),
    }


def get_flashcards(sb: Client, kps: list[str]) -> list[dict]:
    """根据知识点列表取闪卡，按遗忘曲线排序"""
    if not kps:
        return []
    # Supabase 不支持 IN 数组，用 or 拼接
    rows = []
    for kp in kps:
        res = sb.table("flashcard_bank").select("*").eq("title", kp).execute()
        rows.extend(res.data or [])
    # 去重
    seen = set()
    unique = []
    for r in rows:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)
    return unique


def get_quiz_questions(sb: Client, kps: list[str], count: int = 5) -> list[dict]:
    """根据知识点列表抽题，优先出薄弱知识点的题"""
    if not kps:
        return []

    # 取掌握度排序
    mastery_rows = (
        sb.table("mastery_scores")
        .select("knowledge_point, score")
        .in_("knowledge_point", kps)
        .execute()
    ).data or []

    # score 低的知识点优先，每个知识点最多抽 2 题
    mastery_rows.sort(key=lambda x: x["score"])
    questions = []
    used_kps = {}
    for m in mastery_rows:
        kp = m["knowledge_point"]
        qs = (
            sb.table("quiz_questions")
            .select("*")
            .eq("knowledge_point", kp)
            .eq("active", True)
            .limit(2)
            .execute()
        ).data or []
        for q in qs:
            if len(questions) >= count:
                break
            used_kps.setdefault(kp, 0)
            if used_kps[kp] < 2:
                questions.append(q)
                used_kps[kp] += 1
        if len(questions) >= count:
            break

    return questions[:count]


def compute_mastery_score(old_score: int, correct_rate: float) -> int:
    """加权滑动平均：旧分数×0.7 + 本次正确率×0.3"""
    new_score = old_score * 0.7 + correct_rate * 100 * 0.3
    return max(0, min(100, round(new_score)))


def _count_flashcards(sb: Client, kps: list[str]) -> int:
    if not kps:
        return 0
    count = 0
    for kp in kps:
        res = sb.table("flashcard_bank").select("id", count="exact").eq("title", kp).execute()
        count += res.count or 0
    return count


def _count_questions(sb: Client, kps: list[str]) -> int:
    if not kps:
        return 0
    count = 0
    for kp in kps:
        res = sb.table("quiz_questions").select("id", count="exact").eq("knowledge_point", kp).eq("active", True).execute()
        count += res.count or 0
    return count
