from hermes_python.hermes import Hermes
import times_tables as tt


MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))


INTENT_START_QUIZ = "start_lesson"
INTENT_ANSWER = "give_answer"
INTENT_INTERRUPT = "interrupt"
INTENT_DOES_NOT_KNOW = "does_not_know"

INTENT_FILTER_GET_ANSWER = [
    INTENT_ANSWER,
    INTENT_INTERRUPT,
    INTENT_DOES_NOT_KNOW
]

SessionsStates = {}


def user_request_quiz(hermes, intentMessage):
    print("User is asking for a quizz")
    number_of_questions = 1
    tables = []

    if intentMessage.slots.number:
        number_of_questions = intentMessage.slots.number.value.value
    if intentMessage.slots.table:
        tables = [intentMessage.slots.table.value.value]

    session_state, sentence = tt.start_quizz(number_of_questions, tables)

    tt.save_session_state(SessionsStates, intentMessage.session_id, session_state)

    hermes.publish_continue_session(intentMessage.session_id, sentence, INTENT_FILTER_GET_ANSWER)


def user_gives_answer(hermes, intentMessage):
    print("User is giving an answer")

    answer = None
    session_id = intentMessage.session_id
    session_state = SessionsStates.get(session_id)

    if intentMessage.slots.answer:
        answer = intentMessage.slots.answer.value.value

    session_state, sentence, continues = tt.check_user_answer(session_state, answer)

    if not continues:
        hermes.publish_end_session(session_id, sentence)
        tt.remove_session_state(SessionsStates, session_id)
        return

    hermes.publish_continue_session(session_id, sentence, INTENT_FILTER_GET_ANSWER)


def user_does_not_know(hermes, intentMessage):
    print("User does not know the answer")
    session_id = intentMessage.session_id

    sentence, continues = tt.user_does_not_know(session_id, SessionsStates)

    if not continues:
        hermes.publish_end_session(session_id, sentence)
        tt.remove_session_state(SessionsStates, session_id)
        return

    hermes.publish_continue_session(session_id, sentence, INTENT_FILTER_GET_ANSWER)


def user_quits(hermes, intentMessage):
    print("User wants to quit")
    session_id = intentMessage.session_id

    hermes.publish_end_session(session_id, tt.terminate_early(SessionsStates, session_id))


with Hermes(MQTT_ADDR) as h:

    h.subscribe_intent(INTENT_START_QUIZ, user_request_quiz) \
        .subscribe_intent(INTENT_INTERRUPT, user_quits) \
        .subscribe_intent(INTENT_DOES_NOT_KNOW, user_does_not_know) \
        .subscribe_intent(INTENT_ANSWER, user_gives_answer) \
        .start()
