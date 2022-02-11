#-*- coding : utf-8 -*-
import logging
import traceback
logging.basicConfig(level=logging.ERROR)

from flask import request
from flask_restx import Resource, Namespace, reqparse
import datetime
from src.common.util import *


join = Namespace('join')

joinPostModel = join.schema_model('joinPostModel',{

    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timestamp": {
            "type": "string"
        },
        "userNo": {
            "type": "integer"
        }
    },
    "required": [
        "timestamp",
        "userNo"
    ]
})

@join.route('', methods=['POST'])
class JoinApi(Resource):
    #################################################################################
    #POST 회원가입
    #################################################################################
    parser = join.parser()
    parser.add_argument('userId', type = str, required = True, location='body', help='회원 ID')
    parser.add_argument('userPwd', type = str, required = True, location='body', help='회원 PASSWORD (8~16자 영문 대 소문자, 숫자, 특수문자 한 개 이상씩)')
    parser.add_argument('reUserPwd', type = str, required = True, location='body', help='PASSWORD 확인')
    parser.add_argument('userName', type = str, required = True, location='body', help='회원 이름')
    parser.add_argument('userGender', type = str, required = True, location='body', help='회원 성별 M(기본값)/F')
    parser.add_argument('userPhone', type = str, required = True, location='body', help='회원 연락처(-제외)')
    parser.add_argument('userBirth', type = str, required = True, location='body', help='회원 생년월일(YYYYMMDD)')

    parser.add_argument('userEmail', type = str, required = False, location='body', help='회원 확인 이메일')
    @join.expect(parser)

    @join.doc(model=joinPostModel)
    def post(self):
        """
        회원가입
        필수 : ID, PASSWORD, PASSWORD확인, 이름, 성별, 연락처
        일반 : 생년월일
        """
        statusCode = 200
        data = {'timestamp' : datetime.datetime.now().isoformat()}
        # data['get_SECRET'] =  get_rand_base64_token()
        serverType, host, ip = get_server_type(request)

        parser = reqparse.RequestParser()
        parser.add_argument('userId', type = str, required = True)
        parser.add_argument('userPwd', type = str, required = True)
        parser.add_argument('reUserPwd', type = str, required = True)
        parser.add_argument('userName', type = str, required = True)
        parser.add_argument('userGender', type = str, required = True)
        parser.add_argument('userPhone', type = str, required = True)
        parser.add_argument('userBirth', type = str, required = True)

        parser.add_argument('userEmail', type = str, required = False)
        parameter = parser.parse_args()

        #DB start
        cursor = mysql_cursor(mysql_conn(serverType))
        try:
            hasParam = True
            if 'userId' not in parameter  or parameter['userId'] =='' :
                hasParam = False
            if 'userPwd' not in parameter  or parameter['userPwd'] =='' :
                hasParam = False
            if 'reUserPwd' not in parameter  or parameter['reUserPwd'] =='' :
                hasParam = False
            if 'userName' not in parameter  or parameter['userName'] =='' :
                hasParam = False                
            if 'userGender' not in parameter  or parameter['userGender'] =='' :
                hasParam = False      
            if 'userPhone' not in parameter or parameter['userPhone'] == '' :
                hasParam = False
            if 'userBirth' not in parameter or parameter['userBirth'] == '' :
                hasParam = False    

            if hasParam :
                userId = parameter['userId']
                userPwd = parameter['userPwd']
                reUserPwd = parameter['reUserPwd']
                userName = parameter['userName']
                userGender = parameter['userGender']
                userPhone = parameter['userPhone']
                userBirth = parameter['userBirth']

                userEmail = None
                if parameter['userEmail'] is not None  :
                    userEmail = parameter['userEmail']

                #입력값 체크
                hasProcess = True
                
                #비밀번호 일치 검사
                if userPwd != reUserPwd :
                    statusCode = 400
                    data['password_fail1'] = '비밀번호가 일치하지 않습니다.'
                    hasProcess = False
                
                #[정규식]비밀번호 8~16자 영문 대 소문자, 숫자, 특수문자 검사
                if userPwd is not None :
                    pwd_chk = chk_input_match('userPwd', userPwd)
                    if not pwd_chk :
                        statusCode = 400
                        data['password_fail2'] = '8~16자 영문 대 소문자, 숫자, 특수문자를 사용하세요.'
                        hasProcess = False

                #[정규식]연락처 확인
                phone_chk = chk_input_match('userPhone', userPhone) 
                if not phone_chk : 
                    statusCode = 400
                    data['userPhone_fail'] = '올바른 연락처가 아닙니다.'
                    hasProcess = False
            
                #[정규식]생년월일 8자리 확인 YYYYMMDD
                if userBirth is not None :
                    birth_chk = chk_input_match('userBirth', userBirth)
                    if not birth_chk :
                        statusCode = 400
                        data['userBirth_fail'] = '생년월일 8자리를 입력하세요.'
                        hasProcess = False

                #[정규식]이메일 확인
                if userBirth is not None :
                    birth_chk = chk_input_match('userEmail', userEmail)
                    if not birth_chk :
                        statusCode = 400
                        data['userEmail_fail'] = '올바른 이메일이 아닙니다.'
                        hasProcess = False

                #모든 입력값이 정상일 때
                if hasProcess :

                    #아이디 중복 체크
                    sql  = """SELECT count(userId) AS id_chk FROM USER_TABLE WHERE userId = %s"""
                    cursor.execute(query= sql, args=userId)
                    result = cursor.fetchone()

                    #아이디 중복 체크까지 완수 했을 때 INSERT
                    if result['id_chk'] == 0 :
                        
                        sql = """INSERT INTO user_table (userId, userName, userPwd, userPhone, userGender, userBirth, userEmail)
                        VALUES (%s, %s, sha2(%s,256), %s, %s, %s, %s)
                        """
                        cursor.execute(query=sql, args=(userId, userName, userPwd, userPhone, userGender, userBirth, userEmail))
                        userNo = cursor.lastrowid
                        data['userNo'] = userNo

                    else :
                        statusCode = 400
                        data['userId_fail'] = '아이디 중복입니다. 다른 아이디를 사용하세요.'
            else : 
                statusCode = 404
                data['error'] = 'No parameter'
                    
        except Exception as e:
            logging.error(traceback.format_exc())
            data['error'] = 'exception error ' +str(e)
            statusCode = 505
            return data, statusCode
        finally :
            #db close
            cursor.close()
            
        return data, statusCode