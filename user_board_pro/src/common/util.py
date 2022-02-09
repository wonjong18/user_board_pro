#-*-coding : utf-8 -*-
import pymysql
import datetime
import jwt #pyJWT
import re #정규표현식
from secrets import token_bytes
from base64 import b64encode
from src.common.config import *


def mysql_conn(server_type = ""):
    db_name = MysqlConfig.DATABASE
    host = MysqlConfig.HOST
    port = MysqlConfig.PORT

    conn = pymysql.connect(host= host, port= port, db= db_name, user= MysqlConfig.USER, passwd=MysqlConfig.PASSWORD, charset="utf8mb4", autocommit= True)

    return conn

def mysql_cursor(conn) :
    curs = conn.cursor(pymysql.cursors.DictCursor)    
    return curs

def get_server_type (request) :
    host = request.headers.get('Host')    
    host_split = host.split('.')
    server_type = host_split[0]
    ip = request.remote_addr

    return server_type, host, ip

# openssl rand -base 64 32 생성기    
def get_rand_base64_token():
    return b64encode(token_bytes(32)).decode()

#Access token 생성
def jwt_token_generator(user_no, user_id, user_name):
    date_time_obj = datetime.datetime
    exp_time = date_time_obj.timestamp(date_time_obj.now() + datetime.timedelta(hours= 9))

    payload = {
        'userNo' : user_no,
        'userId' : user_id,
        'userName' : user_name,
        'exp' : int(exp_time)
    }
    return jwt.encode(payload=payload, key=JWTConfig.SECRET, algorithm='HS256')    

#refresh token 생성
def jwt_refresh_token_generator(user_no):
    date_time_obj = datetime.datetime
    exp_time = date_time_obj.timestamp(date_time_obj.now()+datetime.timedelta(days= 7))
    refresh_payload = {
        'userNo' : user_no,
        'exp' : int(exp_time)
    }
    return jwt.encode(payload=refresh_payload, key=JWTConfig.SECRET, algorithm='HS256')

#토큰 decoding
def decode_jwt(headers):
    try :
        if 'Authorization' in headers :
            access_token = headers['Authorization'].replace('Bearer ', '')

            if access_token :
                try :
                    payload = jwt.decode(access_token, JWTConfig.SECRET, algorithms="HS256")
                except jwt.InvalidTokenError as e:
                    payload = None

                if payload is not None :
                    exp = int(payload['exp'])
                    date_time_obj = datetime.datetime
                    now_time = int(date_time_obj.timestamp(date_time_obj.now()))

                    #만기 시간이 더 크면 사용할 수 있는 토큰
                    if exp > now_time:
                        return payload

    except BaseException:
        return None
    return None



#유효성 검사
def chk_input_match(in_type, in_value):    
    #정규식으로 입력값 체크
    if in_type == 'userPhone':
        chk = re.compile('\d{3}\d{3,4}\d{4}') #(-)을 제외한 연락처 01055559999
    elif in_type == 'userPwd' :
        chk  = re.compile('^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[$@$!%*?&])[A-Za-z\d$@$!%*?&]{8,10}')  #비밀번호 8~16자 영문 대 소문자, 숫자, 특수문자 검사
    elif in_type == 'userBirth' :
        chk = re.compile('^(19[0-9][0-9]|20\d{2})(0[0-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])$')  #YYYYMMDD 8자리  
    elif in_type == 'userEmail' :
        chk = re.compile('^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')    #test12@naver.com
    else :
        pass

    val = chk.match(in_value)

    #결과 리턴
    if val is not None:
        return True
    else :
        return False        