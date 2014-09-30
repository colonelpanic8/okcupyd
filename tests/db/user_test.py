from okcupyd.db import user


def test_have_messaged_before(T):
    message_thread_model = T.factory.message_thread()
    assert user.have_messaged_by_username(
        message_thread_model.initiator.handle,
        message_thread_model.respondent.handle
    )
    assert user.have_messaged_by_username(
        message_thread_model.respondent.handle,
        message_thread_model.initiator.handle
    )

    assert not user.have_messaged_by_username('a', 'b')
    assert not user.have_messaged_by_username(
        message_thread_model.respondent.handle, 'a'
    )

    T.factory.user('b')
    assert not user.have_messaged_by_username(
        'b', message_thread_model.initiator.handle
    )
