#!/usr/bin/env pypy

import argparse
import json
import os
import logging
import sys
import time
import requests, pickle
from urllib.parse import urlparse
from urllib.parse import parse_qs
from selenium.webdriver.firefox.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

logger = logging.getLogger(__name__)

USER_NAME = os.environ['USER_NAME']
PASSWORD = os.environ['PASSWORD']
UPI_ID = os.environ['UPI_ID']
URL = os.environ['URL']
SLEEP=int(os.environ['SLEEP'])
LID = ""
class BotException(Exception):
    pass

class RetryException(Exception):
    pass
#TODO
def emptyCart(r):
    pass
#TODO
def updateAddress(r):
    pass

def initLogger():
    logger.setLevel(logging.DEBUG)
    path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'logs',time.strftime("%Y%m%d-%H%M%S")+".log"))
    fh = logging.FileHandler(path)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)

def presignin(r):
    logger.debug("Pre-signin..")
    retries = Retry(total=9999,
                    backoff_factor=0.1,
                    status_forcelist=[500, 502, 503, 504])
    r.mount('http://', HTTPAdapter(max_retries=retries))
    r.mount('https://', HTTPAdapter(max_retries=retries))
    r.headers['X-User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 FKUA/website/42/website/Desktop'
    r.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36'
    request(r,"https://www.flipkart.com")
    logger.debug("Pre-signin Cookies {0}".format(r.cookies.get_dict()))
    logger.debug("Pre-signin successful")


def say(text):
    pass
def validate_authenticate(resp):
    if resp.status_code != 200:
        raise RetryException("Retrying due to unsuccessful authentication..{0}".format(resp.text))
    resp_json = json.loads(resp.text)
    if resp_json["STATUS_CODE"] != 200:
        raise RetryException("Retrying due to unsucessfull authentication..{0}".format(resp.text))

def authenticate(r):
    logger.debug("Authenicating..")
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'cookies','logincookies'))):
        logger.debug("Using cached cookies for login")
        usecookies(r,"logincookies")
        logger.debug("Authentication successful")
        return
    json = {"loginId":USER_NAME,"password":PASSWORD}
    resp = request(r,"https://1.rome.api.flipkart.com/api/4/user/authenticate",1,json,validate_authenticate)
    logger.debug("Authentication Cookies {0}".format(r.cookies.get_dict()))
    logger.debug("Authentication successful")
    dumpcookies(r,"logincookies")
    logger.debug("Dumped login cookies")

def request(r,url,_type=0,_params={},callback = None,_retry=2000000,_sleep=SLEEP):
    retry = _retry
    while True :
        logger.debug("Requesting {0} params {1}".format(url,_params))
        try:
            if _type == 0:
                resp = r.get(url, params=_params)
            else:
                if "params" in _params:
                    resp = r.post(url, params=_params["params"], json =_params["json"])
                else:
                    resp = r.post(url, json=_params)
                logger.debug("Response {0}".format(resp.content))
            if callback:
                callback(resp)
            return resp
        except (requests.exceptions.Timeout,requests.exceptions.ConnectTimeout,requests.exceptions.ConnectionError) as e:
            logger.error("Retrying {0} due to timeout {1}".format(url,e))
            time.sleep(_sleep)
            retry -= 1
            continue
        except (requests.exceptions.RequestException,BotException) as e1:
            raise SystemExit(e1)

def cart(r,lid):
    logger.info("Carting...")
    req_json = {"cartContext":{"{0}".format(lid):{"quantity":1}}}
    request(r,"https://1.rome.api.flipkart.com/api/5/cart",1,req_json,validate_cart_rd)
    logger.info("Carted!!!")
    say("Carted")

def validate_cart_rd(resp):
    if resp.status_code != 200:
        raise requests.exceptions.Timeout("Incorrect status code {0}".format(resp.status_code))
    resp_json = json.loads(resp.text)
    if "errorMessage" in resp_json["RESPONSE"]["cartResponse"][LID]:
        errorMessage = resp_json["RESPONSE"]["cartResponse"][LID]["errorMessage"]
        if errorMessage is not None:
            logger.debug("Error message while carting. {0}".format(errorMessage))
            raise requests.exceptions.Timeout("Error message while carting. {0}".format(errorMessage))
    if resp_json["STATUS_CODE"] != 200:
        raise BotException("Validate cart status code not 200")

def validate_cart(resp):
    if resp.status_code != 200:
        raise requests.exceptions.Timeout("Incorrect status code {0}".format(resp.status_code))
    resp_json = json.loads(resp.text)
    if resp_json["STATUS_CODE"] != 200:
        raise BotException("Validate cart status code not 200")

def validate_checkout(resp):
    if resp.status_code != 200:
        raise requests.exceptions.Timeout("Incorrect status code {0}".format(resp.status_code))
    resp_json = json.loads(resp.text)
    if resp_json["STATUS_CODE"] != 200:
        raise BotException("Validate cart status code not 200")
    if len(resp_json["RESPONSE"]["orderSummary"]["requestedStores"][0]["buyableStateItems"]) == 0:
        raise RetryException("Checkout but with zero length")
def checkout(r):
    logger.info("Checkout...")
    req_json = {"checkoutType":"PHYSICAL"}
    resp = request(r,"https://1.rome.api.flipkart.com/api/5/checkout?loginFlow=false",1,req_json,validate_checkout)
    logger.info("Checked Out!!!")
    resp_json = json.loads(resp.text)
    cartItemRefId = resp_json["RESPONSE"]["orderSummary"]["requestedStores"][0]["buyableStateItems"][0]["cartItemRefId"]
    addressId = resp_json["RESPONSE"]["addressData"]["billingAddressInfos"][0]["id"]

    logger.info("CartItemRefId {0}".format(cartItemRefId))
    logger.info("addressId {0}".format(addressId))
    return {"aId" : addressId, "cId" : cartItemRefId}

def paymentToken(r):
    logger.info("Fetching payment token...")
    resp = request(r,"https://1.rome.api.flipkart.com/api/3/checkout/paymentToken",0,{},validate_cart)
    resp_json = json.loads(resp.text)
    pToken = resp_json["RESPONSE"]["getPaymentToken"]["token"]
    logger.debug("Payment Token {0}".format(pToken))
    logger.info("Fetched Payment Token!!!")
    return pToken
def confirmation(r,prim_action):
    logger.info("Confirmation..")
    r = r.post(prim_action["target"], data=prim_action["parameters"],allow_redirects=False)
    logger.debug(r.status_code ) # 302
    logger.debug(r.url )
    logger.debug(r.headers['Location'])
    openURL(r,r.headers['Location'])
    logger.info("Confirmation!!ITEM SECURED")

def pay(r,pToken,method=0):
    logger.info("Fetching payment token...")
    req_json = {}

    logger.info("Payment Step 0..")
    req_json["params"] = {"token": pToken,"instrument" : "UPI"}
    req_json["json"] = {"payment_instrument":"UPI","token": pToken}
    resp = request(r, "https://1.payments.flipkart.com/fkpay/api/v3/payments/pay", 1, req_json, validate_pay)

    logger.info("Payment Step 1..")
    req_json["params"] = {"token": pToken}
    req_json["json"] = {"token": pToken}
    resp = request(r, "https://1.pay.payzippy.com/fkpay/api/v3/payments/upi/options", 1,req_json, validate_pay)

    logger.info("Payment Step 2..")
    req_json["params"] = {"token": pToken}
    req_json["json"]= {"upi_details":{"upi_code":UPI_ID},"payment_instrument":"UPI_COLLECT","token":pToken}
    resp = request(r,"https://1.pay.payzippy.com/fkpay/api/v3/payments/instrumentcheck",1,req_json,validate_pay)
    say("Accept payment")

    logger.info("Payment Step 3..")
    req_json["params"] = {"token": pToken}
    req_json["json"]= {"upi_details":{"app_code":"collect_flow","upi_code":UPI_ID},"payment_instrument":"UPI_COLLECT","token":pToken,"section_info":{"section_name":"OTHERS"}}
    resp = request(r,"https://1.pay.payzippy.com/fkpay/api/v3/payments/paywithdetails",1,req_json,validate_pay)
    resp = json.loads(resp.text)
    txn_id = resp["txn_id"]
    logger.debug("Transaction ID {0}".format(resp["txn_id"]))
    logger.info("PAYMENT SENT TO GPAY..ACCEPT")
    logger.info("Payment Step 4..Polling")
    req_json["params"] = {}
    req_json["json"]= {"token":pToken,"transactionId":txn_id}
    resp = request(r,"https://1.pay.payzippy.com/fkpay/api/v3/payments/upi/poll",1,req_json,validate_poll,1000,4)
    resp = json.loads(resp.text)
    logger.info("PAYMENT DONE")
    logger.debug("Prim_action {0}".format(resp["primary_action"]))
    return resp["primary_action"]

def validate_pay(resp):
    resp_json = json.loads(resp.text)
    if resp_json["response_status"] != "SUCCESS":
        raise BotException("Validate pay status code not SUCCESS")

def validate_poll(resp):
    resp_json = json.loads(resp.text)
    if "response_status" not in resp_json or resp_json["response_status"] != "SUCCESS":
        raise requests.exceptions.Timeout("ACCEPT PAYMENT!!!")


def openURL(r,url):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("window-size=1400,2100")
    chrome_options.add_argument('--disable-gpu')
    driver =  webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
    driver.get("https://www.flipkart.com/404error")
    time.sleep(2)
    for c in r.cookies:
        dict = {'name': c.name, 'value': c.value, 'path': c.path, 'expiry': c.expires}
        print(dict)
        driver.add_cookie({'name': c.name, 'value': c.value, 'path': c.path, 'expiry': c.expires})
    driver.get(url)

def dumpcookies(r,filename = None):
    if filename is None:
        filename = "%Y%m%d-%H%M%S"
    path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'cookies',filename))
    with open(path, 'wb') as f:
        pickle.dump(r.cookies, f)

def usecookies(r,filename):
    path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'cookies',filename))
    with open(path, 'rb') as f:
        r.cookies.update(pickle.load(f))

def execute():
    with requests.Session() as r:
        global LID
        parsed = urlparse(URL)
        lid = parse_qs(parsed.query)['lid'][0]
        LID = lid
        logger.info("LID {0}".format(lid))
        presignin(r)
        authenticate(r)
        emptyCart(r)
        cart(r,lid)
        res = checkout(r)
        #openURL(r,"https://www.flipkart.com/checkout/init?loginFlow=false")
        updateAddress(r)
        pToken = paymentToken(r)
        dumpcookies(r)
        prim_action = pay(r,pToken,0)
        dumpcookies(r)
        confirmation(r,prim_action)
        dumpcookies(r)

if __name__ == "__main__":
    initLogger()
    while True:
        try:
            execute()
            break
        except RetryException as e:
            logger.error("Retrying due to Retry exception {0}".format(e))
            #time.sleep(5)
        finally:
            say("your program is finished")
