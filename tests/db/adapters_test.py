from okcupyd.db import txn, model
from okcupyd.db.adapters import ThreadAdapter


def test_thread_adapter_create_and_update(T):
    initiator = 'first_initiator'
    respondent = 'respondent_one'

    message_thread = T.build_mock.thread(initiator=initiator,
                                         respondent=respondent)

    thread_model, _ = ThreadAdapter(message_thread).get_thread()
    T.ensure.thread_model_resembles_okcupyd_thread(
        thread_model, message_thread
    )

    # Ensure that the operation is idempotent
    other_thread_model, _ = ThreadAdapter(message_thread).get_thread()
    T.ensure.thread_model_resembles_okcupyd_thread(
        thread_model, message_thread
    )
    assert other_thread_model.id == thread_model.id

    # Add messages and ensure that they are picked up.
    message_thread.messages.append(
        T.build_mock.message(sender=message_thread.initiator.username,
                             recipient=message_thread.respondent.username,
                             content='other')
    )

    ThreadAdapter(message_thread).get_thread()
    with txn() as session:
        loaded_thread_model = model.MessageThread.find_no_txn(session,
                                                              thread_model.id)
        assert loaded_thread_model.id == thread_model.id
        T.ensure.thread_model_resembles_okcupyd_thread(
            loaded_thread_model, message_thread
        )
        for i, message in enumerate(loaded_thread_model.messages):
            assert message.thread_index == i

    assert other_thread_model.id == thread_model.id

    second_thread = T.build_mock.thread(initiator=initiator,
                                        respondent='new_respondent')

    second_thread_model, _ = ThreadAdapter(second_thread).get_thread()
    assert second_thread_model.initiator.id == thread_model.initiator.id
    assert second_thread_model.respondent != thread_model.initiator

    T.ensure.thread_model_resembles_okcupyd_thread(second_thread_model,
                                                   second_thread)
