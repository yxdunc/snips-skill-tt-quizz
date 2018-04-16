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
    "give_answer",
    "interrupt",
    "does_not_know"
]

SessionsStates = {}


def user_request_quiz(hermes, intentMessage):
    print("User is asking for a quizz")

    state = tt.start_quizz(intentMessage.slots.get("number"), intentMessage.slots.get("tables"))

    tt.save_session_state(SessionsStates, intentMessage.session_id, state["session_state"])

    hermes.publish_continue_session(intentMessage.session_id, state["response"], INTENT_FILTER_GET_ANSWER)


def user_gives_answer(hermes, intentMessage):
    assert 0 == 1
    assert intentMessage.intent == "give_answer"
    print("User is giving an answer")

    state = tt.check_user_answer(SessionsStates.get(intentMessage.session_id), intentMessage.slots.get("answer"))

    if not state["continues"]:
        hermes.publish_end_session(intentMessage.session_id, state["sentence"])
        tt.remove_session_state(SessionsStates, intentMessage.session_id)
        return

    hermes.publish_continue_session(intentMessage.session_id, state["sentence"], INTENT_FILTER_GET_ANSWER)


def user_does_not_know(hermes, intentMessage):
    print("User does not know the answer")

    state = tt.user_does_not_know(SessionsStates[intentMessage.session_id], intentMessage.slots["answer"])

    if not state["continues"]:
        hermes.publish_end_session(intentMessage.session_id, state["sentence"])
        tt.remove_session_state(SessionsStates, intentMessage.session_id)
        return

    hermes.publish_continue_session(intentMessage.session_id, state["sentence"], INTENT_FILTER_GET_ANSWER)


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
