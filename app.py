import re
from loguru import logger

from chalice import Chalice
import boto3

from contants import PHONE_NOTIFICATION_TRADE_SQS_URL, PHONE_NOTIFICATION_TRADE_SQS_NAME

app = Chalice(app_name="phone-notification-trade")


@app.route("/receive_notification", methods=["post"])
def receive_notification():
    """
    接收短信
    :return:
    """
    user_as_json = app.current_request.json_body

    content = user_as_json["content"]
    exchange, trade_type, symbol = format_bishijie_msg(content)
    trade_msg = {
        "exchange": exchange,
        "type": trade_type,
        "symbol": symbol
    }
    dispatch_trade_msg(trade_msg)
    save_msg(user_as_json)


def save_msg(message: dict):
    """
    保存通知内容到dynamoDB
    :return:
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("phone-notification")
    response = table.put_item(
        Item=message
    )
    logger.info(response)


def format_bishijie_msg(content: str):
    """
    转换币世界短信通知
    :return:
    """
    pattern = "「(.*?)」"
    strategy, signal, price, symbol = re.findall(pattern, content)
    trade_type, symbol = get_huobi_trade_info(signal, symbol)
    return "huobi", trade_type, symbol


def get_huobi_trade_info(signal: str, symbol: str):
    """
    :return:
    """
    signal_map = {
        "XRP": {
            "做多": ("buy-market", "xrplsusdt"),
            "平多": ("sell-market", "xrp3lusdt"),
            "做空": ("buy-market", "xrp3susdt"),
            "平空": ("sell-market", "xrp3susdt"),
        }
    }
    for currency in ["XRP", "ETC"]:
        match = re.search(f"{currency}/", symbol)
        if match:
            return signal_map[currency][signal]


def dispatch_trade_msg(message: dict):
    """
    将交易信息推送到队列
    :return:
    """
    sqs = boto3.client("sqs")
    response = sqs.send_message(
        QueueUrl=PHONE_NOTIFICATION_TRADE_SQS_URL,
        DelaySeconds=10,
        MessageBody=message,
        MessageAttributes={
        }
    )
    logger.info(response)

