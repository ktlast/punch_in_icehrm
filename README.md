# punch_in_icehrm
Automatically punch-in and -out on IceHRM


### A) Steps:

1. scp punch.zip 到測試機，可以放在 /home/<you>/ 底下；自行決定
2. unzip punch.zip
3. 用 root 執行 setup.sh (權限如果不足再自行 chmod)
4. 等待安裝，可能需要五分鐘左右
5. follow 安裝完成的提示；如果有其他錯誤訊息再排除

---

### B) yaml 詳細說明:

```
users:
  ktlast@example.com:  # 記得改成自己的登入信箱，這個就是 HR 帳號
    delay-seconds:   # Total = (basic + random(rand_start ~ rand_end) 秒 ); 各個值上限是 1800
      basic: 100
      random-start: 0
      random-end: 100
    user-agent: "<貼上自己的 user agent>"
    slack:
      verbose: 1     # (0: error, 1: info, 2: debug)
      hookurl: "<貼上自己的 hook url>"
    password: "<貼上自己的密碼>"
    leave:  # 如果有請假可以填日期，依照以下格式：
      - 2020-01-01

global:
  enabled: True
  system:
    driver-path: /opt/chromedriver  # 預設放在這邊，路徑如果不一樣再自行調整
    hrm-url: "https://<HRM_URL>/app/?g=modules&n=attendance&m=modules_Attendance"   # 測試完成後可以改成正式 HRM 環境
  holidays:
    - 2022-02-28
    - 2022-04-04
    - 2022-04-05
    - 2022-06-03
    - 2022-09-09
    - 2022-10-10

```

---

### C) Note：

1. 記得用 crontab
2. 注意不能用 root 執行 punch.py



### D) pip freeze

- list

```
Package            Version
------------------ ---------
async-generator    1.10
attrs              21.4.0
certifi            2021.10.8
cffi               1.15.0
charset-normalizer 2.0.12
cryptography       36.0.1
h11                0.13.0
idna               3.3
outcome            1.1.0
pip                21.1.2
pycparser          2.21
pyOpenSSL          22.0.0
PyYAML             6.0
requests           2.27.1
selenium           4.1.0
setuptools         57.0.0
sniffio            1.2.0
sortedcontainers   2.4.0
trio               0.19.0
trio-websocket     0.9.2
typing-extensions  4.0.1
urllib3            1.26.8
wheel              0.36.2
wsproto            1.0.0

```


- freeze

```
async-generator==1.10
attrs==21.4.0
certifi==2021.10.8
cffi==1.15.0
charset-normalizer==2.0.12
cryptography==36.0.1
h11==0.13.0
idna==3.3
outcome==1.1.0
pycparser==2.21
pyOpenSSL==22.0.0
PyYAML==6.0
requests==2.27.1
selenium==4.1.0
sniffio==1.2.0
sortedcontainers==2.4.0
trio==0.19.0
trio-websocket==0.9.2
typing-extensions==4.0.1
urllib3==1.26.8
wsproto==1.0.0
```
