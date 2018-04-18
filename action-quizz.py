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


def user_request_quiz(hermes, intent_message):
    print("User is asking for a quiz")
    number_of_questions = 1
    tables = []

    if intent_message.slots.number:
        number_of_questions = intent_message.slots.number.value.value
    if intent_message.slots.table:
        tables = [intent_message.slots.table.value.value]

    session_state, sentence = tt.start_quiz(number_of_questions, tables)

    tt.save_session_state(SessionsStates, intent_message.session_id, session_state)

    hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER_GET_ANSWER)


def user_gives_answer(hermes, intent_message):
    print("User is giving an answer")

    answer = None
    session_id = intent_message.session_id
    session_state = SessionsStates.get(session_id)

    if intent_message.slots.answer:
        answer = intent_message.slots.answer.value.value

    session_state, sentence, continues = tt.check_user_answer(session_state, answer)

    if not continues:
        hermes.publish_end_session(session_id, sentence)
        tt.remove_session_state(SessionsStates, session_id)
        return

    hermes.publish_continue_session(session_id, sentence, INTENT_FILTER_GET_ANSWER)


def user_does_not_know(hermes, intent_message):
    print("User does not know the answer")
    session_id = intent_message.session_id

    sentence, continues = tt.user_does_not_know(session_id, SessionsStates)

    if not continues:
        hermes.publish_end_session(session_id, sentence)
        tt.remove_session_state(SessionsStates, session_id)
        return

    hermes.publish_continue_session(session_id, sentence, INTENT_FILTER_GET_ANSWER)


def user_quits(hermes, intent_message):
    print("User wants to quit")
    session_id = intent_message.session_id

    tt.remove_session_state(SessionsStates, session_id)
    hermes.publish_end_session(session_id, tt.terminate_early(SessionsStates, session_id))


def session_ended(hermes, session_ended_message):
    print("Session Ended")
    session_id = session_ended_message.session_id
    session_site_id = session_ended_message.session_site_id

    if SessionsStates.get(session_id):
        init = dict(
            type="action",
            text="",
            canBeEnqueued=False,
            intentFilter=INTENT_FILTER_GET_ANSWER
        )
        hermes.publish_start_session(session_site_id, init)


with Hermes(MQTT_ADDR) as h:

    h.subscribe_intent(INTENT_START_QUIZ, user_request_quiz) \
        .subscribe_intent(INTENT_INTERRUPT, user_quits) \
        .subscribe_intent(INTENT_DOES_NOT_KNOW, user_does_not_know) \
        .subscribe_intent(INTENT_ANSWER, user_gives_answer) \
        .subscribe_session_ended(session_ended) \
        .start()
