import time
import sys
import yaml
import argparse
import requests
import datetime
from os import path
from urllib.parse import urljoin
from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

parser = argparse.ArgumentParser(description="AIM: Update Monitoring Policies.")
parser.add_argument("-f", dest="config_path", action="store", required=True, help="Specify the config path.")
args = parser.parse_args()


# Verify yaml file path
if not path.exists(args.config_path):
    sys.exit(f"Yaml file not found at : {args.config_path}")


# Read config and verify
with open(args.config_path, "r") as stream:
    try:
        config = yaml.safe_load(stream)
        # print(config)
    except yaml.YAMLError as e:
        sys.exit(e)


# Download Chrome Driver from https://chromedriver.chromium.org/downloads
# Verify Drivers
if not path.exists(config['global']['system']['driver-path']):
    print(f"Driver not found at : {config['global']['system']['driver-path']}")
    sys.exit(1)

# check enabled
if config['global']['enabled'] is not True:
    print(f"config['global']['enabled'] not True, Got:  {config['global']['enabled']}")
    print("exit")
    sys.exit(0)


class SlackNotifier:
    def __init__(self, *, webhook_url, verbose):
        self.webhook_url = webhook_url
        if not self.webhook_url:
            sys.exit("Not slack hook url found in config.")

        self.verbose = int(verbose)
        self.verbose_table = {
            0: "[error] No message",
            1: "[info] Info level messages",
            2: "[debug] Verbose messages"
        }
        self.payload = {
            "attachments": [
                {}
            ]
        }

    def _form_payload(self, color, level, content):
        self.payload = {
            "attachments": [
                {
                    "color": color,
                    "title": "[{}]: Punch @  {}".format(level, urljoin(config['global']['system']['hrm-url'], '/')),
                    "title_link": config['global']['system']['hrm-url'],
                    "text": f"{content}",
                    "footer": "AutoPunch",
                    "ts": time.time()
                }
            ]
        }


    # def __str__(self):
    #     return f"verbose level : {self.verbose} ({self.verbose_table[self.verbose]})" \
    #            f"webhook: {self.webhook_url}"
    #
    # def get_verbose_level(self):
    #     return f"verbose level : {self.verbose} ({self.verbose_table[self.verbose]})"

    def requests_post(self):
        try:
            requests.post(self.webhook_url, json=self.payload)
        except requests.exceptions.RequestException as req_err:
            sys.exit(req_err)

    def error(self, message):
        print(f"[ERROR]: {message}")
        if 0 <= self.verbose:
            self._form_payload("#b42c19", "ERROR", message)
            self.requests_post()
            # sys.exit(f"[ERROR]: {message}")

    def info(self, message):
        print(f"[INFO ]: {message}")
        if 1 <= self.verbose:
            self._form_payload("#2eb886", "INFO", message)
            self.requests_post()

    def debug(self, message):
        print(f"[DEBUG]: {message}")
        if 2 <= self.verbose:
            self._form_payload("#acacac", "DEBUG", message)
            self.requests_post()


class PunchWorker:
    driver_path = config['global']['system']['driver-path']
    hrm_url = config['global']['system']['hrm-url']

    def __init__(self, *, email_address):
        self.retry_count = 2
        self.init_retry_count = self.retry_count
        self.retry_interval = 2
        self.email_address = email_address
        self.user_config = config['users'][self.email_address]
        self.slack = SlackNotifier(
            webhook_url=config['users'][self.email_address]['slack']['hookurl'],
            verbose=config['users'][self.email_address]['slack']['verbose']
        )

        # verifies
        if "@" not in self.email_address or "axv.bz" not in self.email_address:
            self.slack.error(f"Invalid Email Address in yaml config. (Got: [{self.email_address}])")
        delay_dict = config['users'][self.email_address]['delay-seconds']
        max_threshold = 1800
        for key, v in delay_dict.items():
            if v > max_threshold:
                config['users'][self.email_address]['delay-seconds'][key] = max_threshold
                self.slack.debug(f"CONFIG: users.{self.email_address}.delay-seconds.{key} must not > {max_threshold}; set to {max_threshold}.")
        if datetime.datetime.today().date() in config['global']['holidays']:
            self.slack.info(f"Punch skipped due to holidays. ({datetime.datetime.today().strftime('%Y-%m-%d')})")
            sys.exit(0)
        if datetime.datetime.today().date() in config['users'][self.email_address]['leave']:
            self.slack.info(f"Punch skipped due to leave. ({datetime.datetime.today().strftime('%Y-%m-%d')})")
            sys.exit(0)

        # init chrome driver
        self.slack.debug("Initializing ...")
        s = Service(executable_path=self.driver_path)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('log-level=1')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f"user-agent={config['users'][self.email_address]['user-agent']}")
        self.driver = webdriver.Chrome(service=s, options=chrome_options)
        self.driver.set_page_load_timeout(15)  # wait page load up to 15 seconds.

    def login(self):
        basic = int(self.user_config['delay-seconds']['basic'])
        rand_start = int(self.user_config['delay-seconds']['random-start'])
        rand_end = int(self.user_config['delay-seconds']['random-end'])
        total_delay = basic + randint(rand_start, rand_end)
        self.slack.info(f"Going to Connect and punch after `{total_delay}` seconds ... ")
        self.slack.debug(f"Total: `{total_delay}` = (basic: `{basic}` + random (`{rand_start}` ~ `{rand_end}`)  )")
        time.sleep(total_delay)

        self.slack.debug(f"Connecting: {self.hrm_url}")

        while self.retry_count > 0:
            print(self.retry_count)
            try:
                self.driver.get(self.hrm_url)
            except NoSuchElementException:
                if self.retry_count == self.init_retry_count:
                    self.slack.error(f"[`NoSuchElementException`] occured while connecting, retry in `{self.retry_interval}` secs ...")
                self.retry_count -= 1
                time.sleep(self.retry_interval)
                continue
            except TimeoutException:
                if self.retry_count == self.init_retry_count:
                    self.slack.error(f"[`TimeoutException`] occured while connecting, retry in `{self.retry_interval}` secs ...")
                self.retry_count -= 1
                time.sleep(self.retry_interval)
                continue
            except WebDriverException as e:
                if self.retry_count == self.init_retry_count:
                    self.slack.error(f"[`WebDriverException`] occured while connecting, retry in `{self.retry_interval}` secs ...")
                self.retry_count -= 1
                time.sleep(self.retry_interval)
                print(e)
                continue
            except Exception as e:
                if self.retry_count == self.init_retry_count:
                    self.slack.error(f"[`Uncatched Exception`] occured while connecting, please check [`/var/spool/mail/<you>]`")
                self.retry_count -= 1
                time.sleep(self.retry_interval)
                print(e)
                continue
            try:
                form_textfield = self.driver.find_element(By.NAME, 'username')
                form_textfield.send_keys(self.email_address)
                form_textfield = self.driver.find_element(By.NAME, 'password')
                form_textfield.send_keys(self.user_config['password'])
                break
            except NoSuchElementException:
                if self.retry_count == self.init_retry_count:
                    self.slack.error(f"[`NoSuchElementException`] occured while filling user/pass, retry in `{self.retry_interval}` secs ...")
                self.retry_count -= 1
                time.sleep(self.retry_interval)
                continue
            except WebDriverException as e:
                if self.retry_count == self.init_retry_count:
                    self.slack.error(f"[`WebDriverException`] occured while filling user/pass, retry in `{self.retry_interval}` secs ...")
                self.retry_count -= 1
                time.sleep(self.retry_interval)
                print(e)
                continue
            except Exception as e:
                if self.retry_count == self.init_retry_count:
                    self.slack.error(f"[`Uncatched Exception`] occured while filling user/pass, please check [`/var/spool/mail/<you>`]")
                self.retry_count -= 1
                time.sleep(self.retry_interval)
                continue
        if self.retry_count <= 0:
            self.slack.error(f"Error occured during login process. Already retried `{self.init_retry_count}` times, Exit ...")
            sys.exit("Error occured during login process.")

    def _click_xpath_button(self, xpath):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
        except:
            self.driver.close()
            self.slack.error("ERROR: while waiting Button. (func: [_click_xpath_button])")
        button = self.driver.find_element(By.XPATH, xpath)
        self.slack.debug(f"Clicking: {button.text}")
        button.click()

    def punch(self):
        self._click_xpath_button('//*[@id="loginForm"]/div[4]/button')
        self._click_xpath_button('//*[@id="punchButton"]')
        self._click_xpath_button('//*[@id="Attendance_submit"]/div/div[3]/div/button[1]')
        self.driver.close()
        self.slack.info(f"Punch successed !")

    def quit(self):
        self.driver.quit()


pw = PunchWorker(email_address=next(iter(config['users'])))
pw.login()
pw.punch()
pw.quit()
