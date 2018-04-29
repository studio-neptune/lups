#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    LINE Unofficial PushMessage Service
    =======================================
        To send a message with one key.
    :version 2018.04.26 using [OLSB-SuperLineApi LiteCore]
    :copyright 2018 Star Inc.(https://starinc.xyz) All Rights Reserved.
"""

from core.ObjectTypes import ApplicationType, IdentityProvider, loginRequest, LoginResultType, Message
from thrift.transport import THttpClient
from thrift.protocol import TCompactProtocol
import os, re, rsa, json, platform, requests, core.TalkService

# Initializing
Seq = 0
cert_dir = "./certs/"
HttpHeaders = {}
email_check = re.compile(r"[^@]+@[^@]+\.[^@]+")

# The Codes was removed to protect the system of LINE Corp.
LINE_HOST        = '' #
LINE_LOGIN       = '' #
LINE_AUTH        = '' #
LINE_COMMAND     = '' #
LINE_CERTIFICATE = '' #
### You still can find these paths from other source ;) ###

APP_TYPE    = ApplicationType._VALUES_TO_NAMES[96]
APP_VER     = '5.5.1.1587'
SYSTEM_NAME = 'OLSB_LiteCore'
SYSTEM_VER  = '6.1.7600-7-x64'
IP_ADDR     = '0.0.0.0'
EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

if not os.path.exists(cert_dir):
   try:
       os.makedirs(cert_dir)
   except:
       raise Exception("Make a directory and name it \"%s\"" % (cert_dir,))

# Functions
def get_json(url, _headers):
    return json.loads(requests.get(url, headers=_headers).text)

def LineShake(self, host, headers):
    transport = THttpClient.THttpClient(host)
    transport.setCustomHeaders(headers)
    protocol = TCompactProtocol.TCompactProtocol(transport)
    return self.Client(protocol)

def login(loginid, passwd, setcrt=None, systemName=None, appName=None, keepLoggedIn=True):
    certificate = ""
    if systemName is None:
        systemName = SYSTEM_NAME
    if email_check.match(loginid):
        provider = IdentityProvider.LINE
    else:
        provider = IdentityProvider.NAVER_KR
    if appName is None:
        appName='%s\t%s\t%s\t%s' % (APP_TYPE, APP_VER, systemName, SYSTEM_VER)
    HttpHeaders['X-Line-Application'] = appName
    _client = LineShake(core.TalkService, LINE_HOST+LINE_AUTH, HttpHeaders)
    rsaKey = _client.getRSAKeyInfo(provider)
    message = (chr(len(rsaKey.sessionKey)) + rsaKey.sessionKey +
                chr(len(loginid)) + loginid +
               chr(len(passwd)) + passwd).encode('utf-8')
    pub_key = rsa.PublicKey(int(rsaKey.nvalue, 16), int(rsaKey.evalue, 16))
    crypto = rsa.encrypt(message, pub_key).hex()
    try:
        with open(cert_dir + loginid + '.crt', 'r') as crtfile:
            certificate = crtfile.read()
    except:
        if setcrt is not None:
            certificate = setcrt
            if os.path.exists(setcrt):
                with open(setcrt, 'r') as crtfile:
                    certificate = crtfile.read()
    _client = LineShake(core.TalkService, LINE_HOST + LINE_LOGIN, HttpHeaders)
    LoginReq = loginRequest()
    LoginReq.type = 0
    LoginReq.identityProvider = provider
    LoginReq.identifier = rsaKey.keynm
    LoginReq.password = crypto
    LoginReq.keepLoggedIn = keepLoggedIn
    LoginReq.accessLocation = IP_ADDR
    LoginReq.systemName = systemName
    LoginReq.certificate = certificate
    LoginReq.e2eeVersion = 0
    result = _client.loginZ(LoginReq)
    if result.type == LoginResultType.REQUIRE_DEVICE_CONFIRM:
        print("請於智慧型手機的LINE輸入認證碼：%s" % (result.pinCode,))
        HttpHeaders['X-Line-Access'] = result.verifier
        getAccessKey = get_json(LINE_HOST+LINE_CERTIFICATE, HttpHeaders)
        _client = LineShake(core.TalkService, LINE_HOST + LINE_LOGIN, HttpHeaders)
        try:
            LoginReq = loginRequest()
            LoginReq.type = 1
            LoginReq.verifier = getAccessKey['result']['verifier']
            LoginReq.e2eeVersion = 0
            result = _client.loginZ(LoginReq)
        except:
            raise Exception("登入時發生錯誤！")
        if result.type == LoginResultType.SUCCESS:
            if result.certificate is not None:
                with open(cert_dir + loginid + '.crt', 'w') as crtfile:
                    crtfile.write(result.certificate)
            if result.authToken is not None:
                return tokenLogin(result.authToken, appName)
            else:
                return False
        else:
            raise Exception("登入時發生錯誤！")
    elif result.type == LoginResultType.REQUIRE_QRCODE:
        raise Exception("未知錯誤:QR Code Login Require")
    elif result.type == LoginResultType.SUCCESS:
        return tokenLogin(result.authToken, appName)

def tokenLogin(authToken=None, appName=None):
    if appName is None:
        appName='%s\t%s\t%s\t%s' % (APP_TYPE, APP_VER, SYSTEM_NAME, SYSTEM_VER)
    if authToken is None:
        raise Exception('No AuthToken!')
    HttpHeaders = {
        'X-Line-Application': appName,
        'X-Line-Access': authToken
    }
    return LineShake(core.TalkService, LINE_HOST + LINE_COMMAND, HttpHeaders)

def sendText(self, ToID, msg):
    if ToID:
        message = Message(to=ToID, text=msg)
        self.send_sendMessage(Seq, message)

def CleanMSG():
    if "Windows" in platform.platform():
            _ = os.system("cls")
    else:
        _ = os.system("clear")

def main():
    CleanMSG()
    check = True
    print("LINE Unofficial廣播系統\n=======================================\n\t一鍵發送訊息到所有好友\n\nVersion 2018.04.26_zh-TW Free Edition\nCopyright 2018 Star Inc.(https://starinc.xyz) All Rights Reserved.\n\n")
    print("請輸入您的帳號及密碼：")
    while check:
        email = input("Email: ")
        passwd = input("Password: ")
        if email_check.match(email):
            if passwd.replace(" ", "") == "":
                print("警告！您輸入的密碼為\"空白\"，請重新輸入...")
            else:
                try:
                    client = login(email, passwd)
                    check = False
                except:
                    print("帳號/密碼/認證錯誤！請重試...")
        else:
            print("信箱格式錯誤！請重新輸入！")
    CleanMSG()
    Profile = client.getProfile()
    print("歡迎%s使用本服務^^" % (Profile.displayName,))
    print("\n\n請輸入您需要的服務...\n(1:透過識別碼廣播文字訊息 2:從群組取得所有成員的識別碼  其他代碼為退出)")
    try:
        action = input("服務代碼：")
        action = int(action)
    except:
        action = 0
    if action == 1: 
        ContactIds = []
        mids = input("識別碼資料(JSON格式)：")
        try:
            mids = json.loads(mids)
        except:
            raise Exception("JSON Decode Error!")
        checked_cons = client.getContacts(mids)
        for contact in checked_cons:
            if contact.mid != Profile.mid and contact.mid not in ContactIds and "u" == contact.mid[0]:
                ContactIds.append(contact.mid)
        CleanMSG()
        actionCheck = True
        retry = False
        while actionCheck:
            if retry:
                print("警告！您尚未輸入任何訊息，請重新輸入...")
            print("請輸入您要輸入的訊息...(輸入完成後，請先換行再輸入 Ctrl + C )")
            print("請注意，每次換行後便無法刪除！\n===============================\n")
            str_saver = ""
            check = True
            while check:
                try:
                    str_saver+=input()+"\n"
                except:
                    check = False
            CleanMSG()
            print("您的訊息為\n" + str_saver)
            print("是否發送？")
            try:
                if str_saver.replace(" ", "") == "":
                    retry = True
                    action = 2
                else:
                    action = input("(1:確定 2:重新輸入 其他代碼為退出)")
                    action = int(action)
            except:
                action = 0
            if action == 1:
                for mid in ContactIds:
                    sendText(client, mid, str_saver)
                print("發送完成!")
                return True
            elif action == 2:
                    CleanMSG()
            else:
                return True
    elif action == 2:
        Count = 0
        GroupIds = client.getGroupIdsJoined()
        Groups = client.getGroups(GroupIds)
        CleanMSG()
        print("已加入的群組列表：")
        for group in Groups:
            print("[%d] => %s\n" % (Count, group.name,))
            Count+=1
        group = input("請輸入群組編號：")
        CleanMSG()
        group = Groups[int(group)]
        mids = str([contact.mid for contact in group.members]).replace("\'", "\"")
        print(mids)
        try:
            action = input("是否要輸出到output.txt(1:好的 2:不用了)")
            action = int(action)
        except:
            action = 0
        if action == 1:
            with open("output.txt", "w") as midfile:
                midfile.write(mids)
            if os.path.exists("output.txt"):
                print("\n已成功儲存在 %s" % (os.getcwd(),))
                return True
            else:
                print("儲存失敗！請檢查檔案系統寫入權限")
                return True
        else:
            return True
    else:
        return True

# Start
if __name__ == "__main__":
    try:
        main()
    except:
        print("發生嚴重錯誤!請聯絡相關技術人員協助問題\nStar Inc. Email Address: star_inc(a)aol.com")
    if "Windows" in platform.platform():
        _ = os.system("pause")
