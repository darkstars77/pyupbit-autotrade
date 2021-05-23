import time
import pyupbit
import requests
import json

with open('../pw.json') as json_file:
    json_data = json.load(json_file)


access = json_data['access']
secret = json_data['secret']
myToken = json_data['myToken']


def bull_market(ticker, k):
    """상승장 흐름 조회"""
    df = pyupbit.get_ohlcv(ticker)
    ma5 = df['close'].rolling(window=k).mean()
    price = pyupbit.get_current_price(ticker)
    last_ma5 = ma5[-2]

    if price > last_ma5:
        return True
    else:
        return False

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

# 로그인
upbit = pyupbit.Upbit(access, secret)

# Parameter
hour = 8
time_period = 3600 * hour
k = 5 #moving average day 5

print("Bull Market Notification start")

tickers = pyupbit.get_tickers(fiat="KRW")

while True:
    try:
        market_dict = dict()
        bull_list = []

        for ticker in tickers:
            if bull_market(ticker, k):
                market_dict[ticker] = '상승장'
                bull_list.append(ticker)
            else:
                market_dict[ticker] = '하락장'

        post_message(myToken, "#crypto", "Bull Coin List\n{}".format(bull_list))

        time.sleep(time_period)
    except Exception as e:
        print(e)
        post_message(myToken,"#crypto", e)
        time.sleep(time_period)