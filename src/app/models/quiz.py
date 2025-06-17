# quiz.py
from sqlmodel import SQLModel, Field, Relationship
import uuid
from typing import List, Optional
from datetime import datetime

class Quiz(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id")
    title: str
    description: Optional[str] = None

    questions: List["Question"] = Relationship(back_populates="quiz")

class Question(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    quiz_id: uuid.UUID = Field(foreign_key="quiz.id")
    text: str
    is_multiple_choice: bool = Field(default=True)

    quiz: Quiz = Relationship(back_populates="questions")
    options: List["Option"] = Relationship(back_populates="question")

class Option(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    question_id: uuid.UUID = Field(foreign_key="question.id")
    text: str
    is_correct: bool = Field(default=False)

    question: Question = Relationship(back_populates="options")

class QuizSubmission(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    quiz_id: uuid.UUID = Field(foreign_key="quiz.id")
    student_id: uuid.UUID = Field(foreign_key="user.id")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    answers: List["Answer"] = Relationship(back_populates="submission")

class Answer(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    submission_id: uuid.UUID = Field(foreign_key="quizsubmission.id")
    question_id: uuid.UUID = Field(foreign_key="question.id")
    selected_option_id: Optional[uuid.UUID] = None
    text_answer: Optional[str] = None

    submission: QuizSubmission = Relationship(back_populates="answers")
