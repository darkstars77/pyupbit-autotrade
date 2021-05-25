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
my_ticker='KRW-ETC'
ma_value=5 # moving average value
k=0.5 #변동성 계수 통상적으로 0.5 사용
interval_value = "minute30"
min_value = 30

# trading time
fix_time_start = datetime.datetime(1999, 9, 9, 1, 00, 0, 0)
fix_time_end = datetime.datetime(1999, 9, 9, 9, 00, 0, 0)


# 시작 메세지 슬랙 전송
post_message(myToken,"#crypto", "{} autotrade start".format(my_ticker))

# 매매 컨트롤
buy_status = False
trading_start_msg = False
buy_count = 0
sell_count = 0

# 하루 수익률 계산
Init_KRW = 0
Final_KRW = 0


while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time(my_ticker, interval_value)
        end_time = start_time + datetime.timedelta(minutes=min_value) - datetime.timedelta(seconds=1)

        #print("start: {}, now: {}, end: {}".format(start_time, now, end_time))
        if fix_time_start.time() < now.time() < fix_time_end.time() and trading_start_msg is False:
            Init_KRW = get_balance("KRW")
            post_message(myToken, "#crypto", "<거래 개시>\nㅇ시작시간 : {}\nㅇ잔고 : {}".format(now.time(), Init_KRW))
            trading_start_msg = True
            buy_count = 0
            sell_count = 0

        if fix_time_start.time() < now.time() < fix_time_end.time():
            if start_time < now < end_time - datetime.timedelta(seconds=10):
                target_price = get_target_price(my_ticker, k, interval_value)
                #ma = get_ma(my_ticker, ma_value)
                current_price = get_current_price(my_ticker)
                #if target_price < current_price and ma < current_price:
                #print("target_price: {}, current_price: {}".format(target_price, current_price))
                if target_price < current_price and buy_status is False:
                    krw = get_balance("KRW")
                    if krw > 5000:
                        buy_result = upbit.buy_market_order(my_ticker, krw*0.9995)
                        post_message(myToken,"#crypto", "{} buy : ".format(my_ticker) +str(buy_result))
                        #print("#crypto", "{} buy : ".format(my_ticker) +str(buy_result))
                        buy_status = True
                        buy_count += 1
            else:
                coin = get_balance(my_ticker.split('-')[-1]) #my_ticker의 A-B -> B 의미
                if coin > 0 and buy_status is True:
                    sell_result = upbit.sell_market_order(my_ticker, coin*0.9995)
                    post_message(myToken,"#crypto", "{} sell : ".format(my_ticker) +str(sell_result))
                    #print("#crypto", "{} sell : ".format(my_ticker) +str(sell_result))
                    buy_status = False
                    sell_count += 1
        else:
            if trading_start_msg is True:
                Final_KRW = get_balance("KRW")
                post_message(myToken, "#crypto", "<거래 종료>\nㅇ종료시간 : {}\nㅇ잔고 : {}".format(now.time(), Final_KRW))
                post_message(myToken, "#crypto", "ㅇ매수:{}회, 매도:{}회".format(buy_count, sell_count))
                post_message(myToken, "#crypto", "ㅇ수익률 : {}".format((Final_KRW/Init_KRW-1)*100))
                trading_start_msg = False
                #print("거래시간이 아닙니다.")

        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken,"#crypto", e)
        time.sleep(1)