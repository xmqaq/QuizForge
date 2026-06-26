from app.schemas.ai import GenerateFromFileResponse, GenerateRequest, GenerateResponse
from app.schemas.auth import LoginRequest, Token
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.file_task import FileTaskCreate, FileTaskResponse, FileTaskUpdate
from app.schemas.question import QuestionCreate, QuestionResponse, QuestionUpdate
from app.schemas.question_bank import (
    QuestionBankCreate,
    QuestionBankResponse,
    QuestionBankUpdate,
)
from app.schemas.quiz_answer import (
    QuizAnswerCreate,
    QuizAnswerResponse,
    QuizAnswerUpdate,
)
from app.schemas.quiz_session import (
    QuizSessionCreate,
    QuizSessionResponse,
    QuizSessionUpdate,
)
from app.schemas.study_plan import StudyPlanCreate, StudyPlanResponse, StudyPlanUpdate
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.wrong_question import (
    WrongQuestionCreate,
    WrongQuestionResponse,
    WrongQuestionUpdate,
)

__all__ = [
    "GenerateRequest",
    "GenerateResponse",
    "GenerateFromFileResponse",
    "LoginRequest",
    "Token",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "FileTaskCreate",
    "FileTaskUpdate",
    "FileTaskResponse",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "QuestionBankCreate",
    "QuestionBankUpdate",
    "QuestionBankResponse",
    "QuizAnswerCreate",
    "QuizAnswerUpdate",
    "QuizAnswerResponse",
    "QuizSessionCreate",
    "QuizSessionUpdate",
    "QuizSessionResponse",
    "StudyPlanCreate",
    "StudyPlanUpdate",
    "StudyPlanResponse",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "WrongQuestionCreate",
    "WrongQuestionUpdate",
    "WrongQuestionResponse",
]
