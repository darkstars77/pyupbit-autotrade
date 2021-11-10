import time
import pyupbit
import datetime
import requests
import json
import os

# 상대경로 사용하기 위해, 실행파일 프로젝트 경로 고정
os.chdir(os.path.dirname(os.path.realpath(__file__)))

with open('../pw.json') as json_file:
    json_data = json.load(json_file)

# access setting
access = json_data['access']
secret = json_data['secret']
myToken = json_data['myToken']


def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k, inter):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval=inter, count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker, inter):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval=inter, count=1)
    start_time = df.index[0]
    return start_time

def get_ma(ticker, d):
    """d일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=d)
    ma = df['close'].rolling(d).mean().iloc[-1]
    return ma

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# parameter
my_ticker='KRW-SOL'


# 시작 메세지 슬랙 전송
post_message(myToken,"#crypto", "{} autotrade start".format(my_ticker))

# MY PARAMETER
Max_Price = 0

#buy
krw = get_balance("KRW")

if krw > 5000:
    #krw * 0.9995
    buy_result = upbit.buy_market_order(my_ticker, krw * 0.9995)
    print(buy_result)
    Max_Price = float(buy_result['price'])
    post_message(myToken, "#crypto", "{} buy : ".format(my_ticker) + str(buy_result['price']))

while True:
    try:
        current_price = get_current_price(my_ticker)
        if current_price > Max_Price:
            Max_Price = current_price

        target_price = Max_Price * 0.9
        if current_price < target_price:
            coin = get_balance(my_ticker.split('-')[-1])
            print('coin : {}'.format(coin))
            sell_result = upbit.sell_market_order(my_ticker, coin*0.9995)
            post_message(myToken, "#crypto", "{} sell : ".format(my_ticker) + str(sell_result['price']))
            break

        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#crypto", e)
        time.sleep(1)
