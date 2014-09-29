from okcupyd.db import model, with_txn


def add_message_to_campaign_and_template_by_okc_id_no_txn(session, okc_id,
                                                          campaign, template):
    message = model.Message.find_no_txn(session, okc_id, id_key='id')
    message.template = template
    message.campaign = campaign
    return message


add_message_to_campaign_and_template_by_okc_id = with_txn(
    add_message_to_campaign_and_template_by_okc_id_no_txn
)