import base64
import datetime
import hashlib
import hmac
import urllib

import requests

from loguru import logger

from trade import huobi_api_key, huobi_secret_key


class HuobiAPI:
    def __init__(self, api_key: str = None, secret_key: str = None, api_version: str = "v1",
                 url: str = "https://api.hbdm.vn", http_timeout: int = 20):
        self.api_key = api_key
        self.secret_key = secret_key
        self.http_timeout = http_timeout
        self.api_version = api_version
        self.url = url

    def sign(self, params: dict, method: str = None, host_url: str = None, request_path: str = None):
        """
        签名
        :param params:
        :param method:
        :param host_url:
        :param request_path:
        :return:
        """
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = '\n'.join(payload)
        payload = payload.encode(encoding='UTF8')
        secret_key = self.secret_key.encode(encoding='UTF8')

        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature

    def http_get(self, end_url: str, params: dict = None, headers: dict = None, sign=True):
        """
        GET 请求
        :param end_url:
        :param params:
        :param headers:
        :param sign:
        :return:
        """
        if not params:
            params = {}
        if not headers:
            headers = {}
        end_url = '/' + end_url
        method = 'GET'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params.update({'AccessKeyId': self.api_key,
                       'SignatureMethod': 'HmacSHA256',
                       'SignatureVersion': '2',
                       'Timestamp': timestamp})

        host_url = self.url
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params['Signature'] = self.sign(params, method, host_name, end_url)
        url = host_url + end_url
        # 添加请求头
        headers.update(
            {"Content-type": "application/json", }
        )

        response = requests.get(url, params=params, headers=headers, timeout=self.http_timeout)
        return response.json()

    def http_post(self, request_path: str, params: dict = None, headers: dict = None, json_data: dict = None):
        """
        POST 请求
        :param json_data:
        :param request_path:
        :param params:
        :param headers:
        :return:
        """
        if not headers:
            headers = {}
        if not params:
            params = {}
        # 加密拼接url
        request_path = '/' + request_path
        method = 'POST'
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        params_to_sign = {'AccessKeyId': self.api_key,
                          'SignatureMethod': 'HmacSHA256',
                          'SignatureVersion': '2',
                          'Timestamp': timestamp}

        host_url = self.url
        host_name = urllib.parse.urlparse(host_url).hostname
        host_name = host_name.lower()
        params_to_sign['Signature'] = self.sign(params_to_sign, method, host_name, request_path)
        url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
        # 添加请求头

        headers.update({
            "Accept": "application/json",
            'Content-Type': 'application/json'
        })

        response = requests.post(url, headers=headers, params=params, json=json_data, timeout=self.http_timeout)
        return response.json()

    def symbols(self):
        """
        获取所有交易对
        :return:
        """

    def accounts(self):
        """
        账户
        spot：现货账户， margin：逐仓杠杆账户，otc：OTC 账户，point：点卡账户，super-margin：全仓杠杆账户, investment: C2C杠杆借出账户, borrow: C2C杠杆借入账户
        :return:
        """
        return self.http_get("v1/account/accounts")

    def account_balance(self, account_id: int):
        """
        账户余额
        :param account_id: 账户ID
        :return:
        """
        return self.http_get(f"v1/account/accounts/{account_id}/balance")

    def swap_cross_account_info(self, margin_account: str = "USDT"):
        """
        获取全仓用户账户信息
        :param margin_account:
        :return:
        """
        json_data = {
            "margin_account": margin_account
        }
        response = self.http_post("linear-swap-api/v1/swap_cross_account_info", json_data=json_data)
        return response

    def swap_open_interest(self, contract_code: str):
        """
        获取当前可用合约总持仓量
        :param contract_code:
        :return:
        """
        json_data = {
            "contract_code": contract_code
        }
        return self.http_get("linear-swap-api/v1/swap_open_interest", params=json_data)

    def swap_order_limit(self, contract_code: str, order_price_type: str = "opponent"):
        """
        【通用】查询用户当前的下单量限制
        :param contract_code:
        :param order_price_type:
        :return:
        """
        json_data = {
            "contract_code": contract_code,
            "order_price_type": order_price_type,
        }
        return self.http_post("linear-swap-api/v1/swap_order_limit", json_data=json_data)

    def swap_cross_position_info(self, contract_code: str):
        """
        获取用户全仓持仓信息
        :return:
        """
        json_data = {
            "contract_code": contract_code
        }
        response = self.http_post('/linear-swap-api/v1/swap_cross_position_info', json_data=json_data)
        print(response)
        return response

    def swap_cross_order(
            self, contract_code: str, volume: int, direction: str,
            offset: str, lever_rate: int = 5, order_price_type: str = "opponent",
            price: float = None, client_order_id: int = None
    ):
        """
        全仓合约下单
        "limit":限价，"post_only":只做maker单，ioc:IOC订单，fok：FOK订单，这四种报价类型需要传价格，其他都不需要。
        开平方向
        开多：买入开多(direction用buy、offset用open)

        平多：卖出平多(direction用sell、offset用close)

        开空：卖出开空(direction用sell、offset用open)

        平空：买入平空(direction用buy、offset用close)
        :param client_order_id: 客户自己填写和维护，必须为数字,请注意必须小于等于9223372036854775807
        :param contract_code: 合约代码
        :param volume: 委托数量(张)
        :param direction: 仓位方向 "buy":买 "sell":卖
        :param offset: 开平方向 "open":开 "close":平
        :param lever_rate: 杠杆倍数,“开仓”若有10倍多单，就不能再下20倍多单;首次使用高倍杠杆(>20倍)，请使用主账号登录web端同意高倍杠杆协议后，才能使用接口下高倍杠杆(>20倍)]
        :param order_price_type: 订单报价类型 "limit":限价 "opponent":对手价 "post_only":只做maker单,post only下单只受用户持仓数量限制,
        optimal_5：最优5档、optimal_10：最优10档、optimal_20：最优20档，ioc:IOC订单，fok：FOK订单, "opponent_ioc": 对手价-IOC下单，
        "optimal_5_ioc": 最优5档-IOC下单，"optimal_10_ioc": 最优10档-IOC下单，"optimal_20_ioc"：最优20档-IOC下单，
        "opponent_fok"： 对手价-FOK下单, "optimal_5_fok"：最优5档-FOK下单，"optimal_10_fok"：最优10档-FOK下单，"optimal_20_fok"：最优20档-FOK下单
        :param price: 价格
        :return:
        """
        json_data = {
            "contract_code": contract_code,
            "volume": volume,
            "direction": direction,
            "offset": offset,
            "lever_rate": lever_rate,
            "order_price_type": order_price_type,
        }
        if client_order_id:
            json_data["client_order_id"] = client_order_id
        if price:
            json_data["price"] = client_order_id

        response = self.http_post("linear-swap-api/v1/swap_cross_order", json_data=json_data)
        print(response)
        return response


if __name__ == '__main__':
    huobi = HuobiAPI(api_key=huobi_api_key, secret_key=huobi_secret_key)
    resp = huobi.swap_order_limit("XRP-USDT")
    print(resp)
    # response = huobi.swap_cross_position_info("XRP-USDT")
    # volume = response["data"][0]["available"]
    # huobi.swap_cross_order(contract_code="XRP-USDT", volume=int(volume), direction="sell", offset="close")
