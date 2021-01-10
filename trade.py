from huobi.client.account import AccountClient
from huobi.client.generic import GenericClient
from huobi.client.trade import TradeClient

from app import app
import os
from contants import PHONE_NOTIFICATION_TRADE_SQS_NAME

huobi_api_key = os.getenv("HUOBI_API_KEY")
huobi_secret_key = os.getenv("HUOBI_SECRET_KEY")


@app.on_sqs_message(queue=PHONE_NOTIFICATION_TRADE_SQS_NAME)
def handler_trade_msg(event: dict):
    """
    处理交易信息
    :return:
    """
    # 获取余额

    # 交易

# spot_id = 4756379
# otc_id = 4817995
if __name__ == '__main__':
    account_client = AccountClient(api_key=huobi_api_key, secret_key=huobi_secret_key)
    accounts = account_client.get_accounts()
    for i in accounts:
        i.print_object()
    # for balance in account_balance_list:
    #     # if balance !=0:
    #     # print(balance.print_object())
    #     for sub in balance.subtype:
    #         if sub.blance > 0:
    #             print(sub.print_object())
