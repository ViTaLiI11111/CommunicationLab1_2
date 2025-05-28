from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
import logging
import datetime
from pathlib import Path
import os

from .db_connector import DatabaseConnector
from .models import User, QuizSession
from lib.quiz_lib.question_data import QuestionData
from .reply_markup_formatter import format_answers_as_inline_keyboard
from .localization import Localization
from lib.quiz_lib.quiz import QuizSingleton


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HandlerDependencies:
     def __init__(self, db_connector: DatabaseConnector, question_data: QuestionData, localization: Localization):
         self.db = db_connector
         self.quiz_data = question_data
         self.loc = localization

def get_db_session(deps: HandlerDependencies) -> Session | None:
    session = deps.db.get_session()
    if not session:
         logger.error("Failed to get DB session.")
    return session


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, deps: HandlerDependencies):
    user_id = update.effective_user.id
    username = update.effective_user.username
    chat_id = update.effective_chat.id

    session = get_db_session(deps)
    if not session:
         await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('database_error', lang=update.effective_user.language_code))
         return

    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            user = User(id=user_id, username=username)
            session.add(user)
            session.commit()
            session.refresh(user)


        active_session = session.query(QuizSession).filter_by(user_id=user_id, status='active').first()

        if active_session:
             msg = deps.loc.get_message('quiz_already_active', lang=update.effective_user.language_code)
             await context.bot.send_message(chat_id=chat_id, text=msg)
             await send_question(update, context, deps, active_session.current_question_index)
        else:
            new_session = QuizSession(user_id=user_id, current_question_index=0, correct_answers_count=0, status='active')
            session.add(new_session)
            session.commit()
            session.refresh(new_session)

            msg = deps.loc.get_message('greeting_message', lang=update.effective_user.language_code)
            await context.bot.send_message(chat_id=chat_id, text=msg)
            await send_question(update, context, deps, new_session.current_question_index)

    except Exception as e:
         logger.error(f"Error in start_command for user {user_id}: {e}", exc_info=True)
         await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('internal_error', lang=update.effective_user.language_code))
         session.rollback()
    finally:
        session.close()


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE, deps: HandlerDependencies):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    session = get_db_session(deps)
    if not session:
         await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('database_error', lang=update.effective_user.language_code))
         return

    try:
        active_session = session.query(QuizSession).filter_by(user_id=user_id, status='active').first()

        if active_session:
            active_session.status = 'cancelled'
            active_session.end_time = datetime.datetime.now()
            session.commit()

            msg = deps.loc.get_message('farewell_message', lang=update.effective_user.language_code)
            await context.bot.send_message(chat_id=chat_id, text=msg)

        else:
            msg = deps.loc.get_message('no_active_quiz', lang=update.effective_user.language_code)
            await context.bot.send_message(chat_id=chat_id, text=msg)

    except Exception as e:
         logger.error(f"Error in stop_command for user {user_id}: {e}", exc_info=True)
         await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('internal_error', lang=update.effective_user.language_code))
         session.rollback()
    finally:
        session.close()


async def command_c(update: Update, context: ContextTypes.DEFAULT_TYPE, deps: HandlerDependencies):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    args = context.args

    if not args or len(args) != 1:
        msg = deps.loc.get_message('c_command_usage', lang=update.effective_user.language_code)
        await context.bot.send_message(chat_id=chat_id, text=msg)
        return

    try:
        question_index = int(args[0]) - 1
        total_questions = len(deps.quiz_data.collection)
        if question_index < 0 or question_index >= total_questions:
            msg_template = deps.loc.get_message('invalid_question_number', lang=update.effective_user.language_code)
            msg = msg_template.format(count=total_questions)
            await context.bot.send_message(chat_id=chat_id, text=msg)
            return

        session = get_db_session(deps)
        if not session:
             await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('database_error', lang=update.effective_user.language_code))
             return

        try:
            quiz_session = session.query(QuizSession).filter_by(user_id=user_id, status='active').first()
            if not quiz_session:
                quiz_session = QuizSession(user_id=user_id, current_question_index=question_index, correct_answers_count=0, status='active')
                session.add(quiz_session)
                session.commit()
                session.refresh(quiz_session)
                msg_template = deps.loc.get_message('new_quiz_at_q', lang=update.effective_user.language_code)
                msg = msg_template.format(q_num=question_index + 1)
                await context.bot.send_message(chat_id=chat_id, text=msg)
            else:
                quiz_session.current_question_index = question_index
                session.commit()
                msg_template = deps.loc.get_message('jump_to_q', lang=update.effective_user.language_code)
                msg = msg_template.format(q_num=question_index + 1)
                await context.bot.send_message(chat_id=chat_id, text=msg)

            await send_question(update, context, deps, quiz_session.current_question_index)

        except Exception as e:
            logger.error(f"Error in command_c for user {user_id}: {e}", exc_info=True)
            await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('internal_error', lang=update.effective_user.language_code))
        finally:
             session.close()

    except ValueError:
        msg = deps.loc.get_message('invalid_number_format', lang=update.effective_user.language_code)
        await context.bot.send_message(chat_id=chat_id, text=msg)


async def handle_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, deps: HandlerDependencies):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_lang = update.effective_user.language_code

    callback_data = query.data

    if not callback_data or not callback_data.startswith('answer:'):
        logger.warning(f"Received unexpected callback data: {callback_data} from user {user_id}")
        await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('unexpected_action', lang=user_lang))
        return

    chosen_char = callback_data.split(':')[1]

    session = get_db_session(deps)
    if not session:
         await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('database_error', lang=user_lang))
         return

    try:
        quiz_session = session.query(QuizSession).filter_by(user_id=user_id, status='active').first()

        if not quiz_session:
            msg = deps.loc.get_message('no_active_quiz_callback', lang=user_lang)
            await context.bot.send_message(chat_id=chat_id, text=msg)
            return

        current_question_index = quiz_session.current_question_index

        if current_question_index >= len(deps.quiz_data.collection):
             msg = deps.loc.get_message('quiz_already_finished', lang=user_lang)
             await context.bot.send_message(chat_id=chat_id, text=msg)
             if quiz_session.status == 'active':
                 quiz_session.status = 'finished'
                 quiz_session.end_time = datetime.datetime.now()
                 session.commit()
             return

        current_question = deps.quiz_data.collection[current_question_index]

        if chosen_char not in current_question.question_answers:
             logger.warning(f"User {user_id} sent invalid answer char '{chosen_char}' for question index {current_question_index}.")
             await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('invalid_answer_option', lang=user_lang))
             return


        is_correct = chosen_char == current_question.question_correct_answer

        if is_correct:
            quiz_session.correct_answers_count += 1
            response_msg = deps.loc.get_message('answer_correct', lang=user_lang)
            await context.bot.send_message(chat_id=chat_id, text=response_msg)

        else:
            correct_answer_text = current_question.find_answer_by_char(current_question.question_correct_answer)
            msg_template = deps.loc.get_message('answer_incorrect', lang=user_lang)
            response_msg = msg_template.format(correct_answer=correct_answer_text)
            await context.bot.send_message(chat_id=chat_id, text=response_msg)


        quiz_session.current_question_index += 1
        session.commit()

        await send_next_question_or_finish(update, context, deps, quiz_session, session)

    except Exception as e:
         logger.error(f"Error in handle_answer_callback for user {user_id}: {e}", exc_info=True)
         await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('internal_error', lang=user_lang))
         session.rollback()
    finally:
        session.close()


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, deps: HandlerDependencies, question_index: int):
    chat_id = update.effective_chat.id
    user_lang = update.effective_user.language_code

    if question_index < 0 or question_index >= len(deps.quiz_data.collection):
        logger.error(f"Attempted to send invalid question index {question_index} to chat {chat_id}")
        await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('invalid_question_index_error', lang=user_lang))
        return

    question = deps.quiz_data.collection[question_index]

    question_text = f"{question_index + 1}/{len(deps.quiz_data.collection)}. {question.question_body}\n\n"

    reply_markup = format_answers_as_inline_keyboard(question)

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=question_text,
            reply_markup=reply_markup
        )

    except Exception as e:
         logger.error(f"Error sending question {question_index} to chat {chat_id}: {e}", exc_info=True)
         await context.bot.send_message(chat_id=chat_id, text=deps.loc.get_message('send_question_error', lang=user_lang))


async def send_next_question_or_finish(update: Update, context: ContextTypes.DEFAULT_TYPE, deps: HandlerDependencies, quiz_session: QuizSession, session: Session):
    chat_id = update.effective_chat.id
    user_id = quiz_session.user_id
    user_lang = update.effective_user.language_code
    next_question_index = quiz_session.current_question_index
    total_questions = len(deps.quiz_data.collection)

    if next_question_index < total_questions:
        await send_question(update, context, deps, next_question_index)
    else:
        quiz_session.status = 'finished'
        quiz_session.end_time = datetime.datetime.now()

        try:
            session.commit()
            logger.info(f"Quiz session {quiz_session.id} for user {user_id} marked as finished.")
        except Exception as e:
             logger.error(f"Error committing session status 'finished' for user {user_id}: {e}", exc_info=True)
             session.rollback()

        correct_count = quiz_session.correct_answers_count
        percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0

        msg_template = deps.loc.get_message('quiz_finished_report', lang=user_lang)
        report_msg = msg_template.format(
             correct=correct_count,
             total=total_questions,
             percentage=percentage
        )
        await context.bot.send_message(chat_id=chat_id, text=report_msg)

        logger.info(f"Quiz finished for user {user_id}. Report: {report_msg}")

        try:
            quiz_singleton_cfg = QuizSingleton()
            answers_dir = quiz_singleton_cfg.get_project_path(quiz_singleton_cfg.answers_dir)
            timestamp_str = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            filename = f"QUIZ_s_{timestamp_str}.txt"
            filepath = answers_dir / filename

            file_content = f"""
Quiz Session Report
-------------------
User ID: {user_id}
Username: {update.effective_user.username}
Session ID: {quiz_session.id}
Start Time: {quiz_session.start_time.strftime('%Y-%m-%d %H:%M:%S') if quiz_session.start_time else 'N/A'}
End Time: {quiz_session.end_time.strftime('%Y-%m-%d %H:%M:%S') if quiz_session.end_time else 'N/A'}
Correct Answers: {correct_count}
Total Questions: {total_questions}
Percentage: {percentage:.2f}%
Status: {quiz_session.status}
-------------------
"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(file_content.strip())

            logger.info(f"Quiz results for user {user_id} saved to {filepath}")

        except Exception as e:
             logger.error(f"Error saving quiz results to file for user {user_id}: {e}", exc_info=True)