import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.question import Question, QuestionStatus
from app.models.quiz_answer import QuizAnswer
from app.models.quiz_session import QuizMode, QuizSession, SessionStatus
from app.models.user import User
from app.models.wrong_question import WrongQuestion
from app.schemas.question import QuestionResponse
from app.schemas.quiz_answer import AnswerResult, AnswerSubmit
from app.schemas.quiz_session import QuizSessionCreate, QuizSessionResponse
from app.utils.time import naive_utcnow

router = APIRouter()


async def _get_session(db: AsyncSession, session_id: uuid.UUID, user: User) -> QuizSession:
    s = await db.get(QuizSession, session_id)
    if s is None:
        raise HTTPException(status_code=404, detail="答题会话不存在")
    if s.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    return s


async def _pick_questions(
    db: AsyncSession, bank_id: uuid.UUID, mode: QuizMode, user_id: uuid.UUID, limit: int | None
) -> list[Question]:
    stmt = select(Question).where(
        Question.bank_id == bank_id, Question.status == QuestionStatus.approved
    )
    if mode == QuizMode.wrong_only:
        stmt = stmt.join(WrongQuestion, WrongQuestion.question_id == Question.id).where(
            WrongQuestion.user_id == user_id, WrongQuestion.is_mastered.is_(False)
        )

    if mode in (QuizMode.random, QuizMode.simulation):
        stmt = stmt.order_by(func.random())
    else:  # sequential / wrong_only keep insertion order
        stmt = stmt.order_by(Question.created_at)

    if limit:
        stmt = stmt.limit(limit)
    return list(await db.scalars(stmt))


@router.post("/sessions", response_model=QuizSessionResponse, summary="开始答题会话")
async def start_session(
    data: QuizSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据 mode 选题并创建一个答题会话。total_questions 为空表示用全部可用题目。"""
    questions = await _pick_questions(
        db, data.bank_id, data.mode, current_user.id, data.total_questions
    )
    if not questions:
        raise HTTPException(status_code=400, detail="该题库下没有可用题目")

    session = QuizSession(
        user_id=current_user.id,
        bank_id=data.bank_id,
        mode=data.mode,
        total_questions=len(questions),
        time_limit_seconds=data.time_limit_seconds,
        question_ids=[str(q.id) for q in questions],
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions", summary="我的答题会话列表")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    base = select(QuizSession).where(QuizSession.user_id == current_user.id)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    rows = await db.scalars(
        base.order_by(QuizSession.started_at.desc()).offset((page - 1) * size).limit(size)
    )
    return {"items": [QuizSessionResponse.model_validate(r) for r in rows], "total": total, "page": page, "size": size}


@router.get(
    "/sessions/{session_id}/questions",
    response_model=list[QuestionResponse],
    summary="获取会话题目",
)
async def session_questions(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """返回本次会话固定的题目列表（开始时已选定，顺序一致）。"""
    s = await _get_session(db, session_id, current_user)
    ids = [uuid.UUID(x) for x in (s.question_ids or [])]
    if not ids:
        return []
    rows = await db.scalars(select(Question).where(Question.id.in_(ids)))
    by_id = {q.id: q for q in rows}
    return [by_id[i] for i in ids if i in by_id]


@router.post(
    "/sessions/{session_id}/answer",
    response_model=AnswerResult,
    summary="提交一道题的作答",
)
async def submit_answer(
    session_id: uuid.UUID,
    data: AnswerSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """判分、记录作答；答错则计入错题本（已存在则次数+1）。"""
    s = await _get_session(db, session_id, current_user)
    if s.status != SessionStatus.active:
        raise HTTPException(status_code=400, detail="会话已结束")

    if str(data.question_id) not in (s.question_ids or []):
        raise HTTPException(status_code=400, detail="该题不属于本次答题")
    q = await db.get(Question, data.question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    existing = await db.scalar(
        select(QuizAnswer).where(
            QuizAnswer.session_id == s.id,
            QuizAnswer.question_id == data.question_id,
        )
    )
    if existing is not None:
        # 已作答过，直接返回原结果，避免重复计分
        return AnswerResult(
            is_correct=existing.is_correct,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            answered_count=s.answered_count,
            correct_count=s.correct_count,
        )

    is_correct = data.user_answer == q.correct_answer
    db.add(
        QuizAnswer(
            session_id=s.id,
            question_id=q.id,
            user_answer=data.user_answer,
            is_correct=is_correct,
            time_spent_seconds=data.time_spent_seconds,
        )
    )
    s.answered_count += 1
    if is_correct:
        s.correct_count += 1
    else:
        wrong = await db.scalar(
            select(WrongQuestion).where(
                WrongQuestion.user_id == current_user.id,
                WrongQuestion.question_id == q.id,
            )
        )
        if wrong is None:
            db.add(WrongQuestion(user_id=current_user.id, question_id=q.id))
        else:
            wrong.wrong_count += 1
            wrong.last_wrong_at = naive_utcnow()
            wrong.is_mastered = False
            wrong.mastered_at = None

    await db.commit()
    return AnswerResult(
        is_correct=is_correct,
        correct_answer=q.correct_answer,
        explanation=q.explanation,
        answered_count=s.answered_count,
        correct_count=s.correct_count,
    )


@router.post(
    "/sessions/{session_id}/finish",
    response_model=QuizSessionResponse,
    summary="结束答题会话",
)
async def finish_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = await _get_session(db, session_id, current_user)
    s.status = SessionStatus.finished
    s.finished_at = naive_utcnow()
    await db.commit()
    await db.refresh(s)
    return s
