# coding:utf-8

import time
import re
import datetime
import key

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys

from pymongo import MongoClient

# 対象スレッド数
ACQUIRED_THREADS = 3

def main():

    driver = initialize_driver()

    # 検索した結果のURLを開く
    driver.get(key.SPLA_SEARCH_RESULT_URL)

    # スレッドのURL
    urls = search_result_urls(driver)

    # DB接続
    collection = connect_db()

    i = ACQUIRED_THREADS - 1
    while i > -1:
        print('対象スレッド: ' + urls[i])
        driver.get(urls[i])
        insert_res_list(driver, collection)
        i -= 1

    driver.quit()  # ブラウザーを終了する。

# driverの初期設定を行う
def initialize_driver():
    options = ChromeOptions()
    # なんか動かなかったから追加
    options.add_argument('--no-sandbox')
    # ヘッドレスモードを有効にする（次の行をコメントアウトすると画面が表示される）。
    options.add_argument('--headless')
    # ChromeのWebDriverオブジェクトを作成する。
    return Chrome(options=options)

# 検索結果のURLリストを返却する
def search_result_urls(driver):
    print('対象スレッド件数: ' + str(ACQUIRED_THREADS))
    urls = []
    for number in range(1, ACQUIRED_THREADS + 1):
        href = driver.find_element_by_css_selector('body > ul > li:nth-child(' + str(number) + ') > a:nth-child(1)').get_attribute('href')
        urls.append(href)
        print('対象スレッドURL' + str(number) + ': ' + href)
    return urls

# DBに接続する
def connect_db():
    client = MongoClient('localhost', 27017)
    collection = client.scraping.twoch
    collection.create_index('id', unique=True)
    return collection

# 書き込みを行う
def insert_res_list(driver, collection):

    # URLのスレッドIDを取得
    thread = re.search('\d{10,}', driver.current_url).group()
    print('対象スレッドID: ' + thread)
    max_no = collection.find({'thread': thread}).count()
    print('DB登録済み最大No: ' + str(max_no))

    # 現在の書き込み件数
    numbers = driver.find_elements_by_class_name('post')
    if len(numbers) >= 1000:
        numbers = '1000'
    print('スレッドの書き込み件数: ' + str(len(numbers)))

    # 1件も書き込みがない場合は不要
    if len(numbers) <= max_no:
        print('skip: 1件も書き込みがないため')
        return

    # 1000件を超える場合は不要
    if max_no >= 1000:
        print('skip: 1000件を超えるため')
        return

    # 書き込みの日時
    now_date = str(datetime.datetime.now())
    print('書き込み日時: ' + now_date)

    for number in range(max_no + 1, len(numbers) + 1):
        # レスNo
        no = driver.find_element_by_xpath('//*[@id="' + str(number) + '"]/div[1]/span[1]').text
        print('スレッドID: ' + thread + ', 登録済み最大No: ' + str(max_no) + ', 登録No: ' + no)

        # 書き込み
        text = driver.find_element_by_xpath('//*[@id="' + str(number) + '"]/div[2]/span').text
        
        response_list = re.findall('>>[0-9]{1,3}', text)
        is_response = False
        reply_destinations = ''
        if response_list:
            is_response = True
            response_no_list  = []

            for response in response_list:
                response_no_list.append(re.search('[0-9]{1,4}', response).group())
            
            reply_destinations = ','.join(map(str,response_no_list))
        
        collection.insert_one({
            'id': thread + '-' + no,
            'key': thread + '-' + no,
            'thread': thread,
            'no': no,
            'name': 'dummy',
            'date': driver.find_element_by_xpath('//*[@id="' + str(number) + '"]/div[1]/span[3]').text,
            'userid': 'dummy',
            'text': text,
            'is_response': is_response,
            'reply_destinations': reply_destinations,
            "created_at": now_date,
        })

if __name__ == '__main__':
    main()
