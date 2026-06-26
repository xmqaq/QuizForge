import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.question import Question
from app.models.question_bank import QuestionBank
from app.models.quiz_answer import QuizAnswer
from app.models.quiz_session import QuizSession
from app.models.user import User
from app.models.wrong_question import WrongQuestion

router = APIRouter()


@router.get("/overview", summary="我的学习概览")
async def overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """当前用户的整体统计：会话数、作答数、正确率、错题数、创建的题库数。"""
    sessions = await db.scalar(
        select(func.count()).select_from(QuizSession).where(
            QuizSession.user_id == current_user.id
        )
    )
    total_answers = await db.scalar(
        select(func.count())
        .select_from(QuizAnswer)
        .join(QuizSession, QuizSession.id == QuizAnswer.session_id)
        .where(QuizSession.user_id == current_user.id)
    )
    correct_answers = await db.scalar(
        select(func.count())
        .select_from(QuizAnswer)
        .join(QuizSession, QuizSession.id == QuizAnswer.session_id)
        .where(QuizSession.user_id == current_user.id, QuizAnswer.is_correct.is_(True))
    )
    wrong_unmastered = await db.scalar(
        select(func.count()).select_from(WrongQuestion).where(
            WrongQuestion.user_id == current_user.id,
            WrongQuestion.is_mastered.is_(False),
        )
    )
    banks_created = await db.scalar(
        select(func.count()).select_from(QuestionBank).where(
            QuestionBank.created_by == current_user.id
        )
    )
    return {
        "sessions": sessions,
        "total_answers": total_answers,
        "correct_answers": correct_answers,
        "accuracy": round(correct_answers / total_answers, 4) if total_answers else 0,
        "wrong_unmastered": wrong_unmastered,
        "banks_created": banks_created,
    }


@router.get("/bank/{bank_id}", summary="题库统计")
async def bank_stats(
    bank_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """某题库的题目分布（按难度），以及当前用户在该题库的作答正确率。"""
    bank = await db.get(QuestionBank, bank_id)
    if bank is None:
        raise HTTPException(status_code=404, detail="题库不存在")

    by_difficulty = dict(
        (
            await db.execute(
                select(Question.difficulty, func.count())
                .where(Question.bank_id == bank_id)
                .group_by(Question.difficulty)
            )
        ).all()
    )

    total = await db.scalar(
        select(func.count())
        .select_from(QuizAnswer)
        .join(QuizSession, QuizSession.id == QuizAnswer.session_id)
        .where(QuizSession.user_id == current_user.id, QuizSession.bank_id == bank_id)
    )
    correct = await db.scalar(
        select(func.count())
        .select_from(QuizAnswer)
        .join(QuizSession, QuizSession.id == QuizAnswer.session_id)
        .where(
            QuizSession.user_id == current_user.id,
            QuizSession.bank_id == bank_id,
            QuizAnswer.is_correct.is_(True),
        )
    )
    return {
        "bank_id": str(bank_id),
        "title": bank.title,
        "question_count": bank.question_count,
        "by_difficulty": {d.value: c for d, c in by_difficulty.items()},
        "my_answered": total,
        "my_correct": correct,
        "my_accuracy": round(correct / total, 4) if total else 0,
    }
