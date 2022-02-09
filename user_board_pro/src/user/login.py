#-*- coding : utf-8 -*-
import logging
import traceback

logging.basicConfig(level=logging.ERROR)

from flask import request
from flask_restx import Resource, Namespace, reqparse
import datetime
from src.common.util import *

login = Namespace('login')

loginPostModel = login.schema_model('loginPostModel', {

    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timestamp": {
            "type": "string"
        },
        "userNo": {
            "type": "integer"
        },
        "userName": {
            "type": "string"
        },
        "token": {
            "type": "string"
        },
        "refresh_token": {
            "type": "string"
        }
    },
    "required": [
        "timestamp",
        "userNo",
        "userName",
        "token",
        "refresh_token"
    ]

})

@login.route('', methods = ['POST'])
class LoginApi(Resource):
    #############################################################
    # POST 로그인
    #############################################################
    parser = login.parser()
    parser.add_argument('userId', type=str, required = True, location = 'body', help = '회원 ID')
    parser.add_argument('userPwd', type=str, required = True, location = 'body', help='회원 PASSWORD')
    @login.expect(parser)

    @login.doc(loginPostModel)
    def post(self):
        """
        로그인
        필수 : userId, userPwd
        일반 :
        """

        statusCode = 200
        data = {'timestamp' : datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

        parser = reqparse.RequestParser()
        parser.add_argument('userId', type=str, required = True )
        parser.add_argument('userPwd', type=str, required = True )
        parameter = parser.parse_args()

        #DB START
        cursor = mysql_cursor(mysql_conn(serverType))
        try:
            hasParam = True
            if 'userId' not in parameter or parameter['userId'] is None :
                hasParam = False
            if 'userPwd' not in parameter or parameter['userPwd'] is None :
                hasParam = False
            
            if hasParam :
                userId = parameter['userId']
                userPwd = parameter['userPwd']

                sql = """SELECT userNo, userId, userName FROM USER_TABLE  
                WHERE DISABLED = 0 AND userId = %s AND userPwd = sha2(%s,256)"""
                cursor.execute(query=sql, args=(userId, userPwd))
                result = cursor.fetchone()

                if result is not None :
                    userNo = result['userNo']
                    userId = result['userId']
                    userName = result['userName']

                    #token 생성
                    token = jwt_token_generator(userNo, userId, userName)

                    #refreshtoken 생성
                    refresh_token = jwt_refresh_token_generator(userNo)

                    #refreshtoken 업데이트
                    sql = 'UPDATE USER_TABLE SET refreshToken = %s WHERE userNo = %s'
                    cursor.execute(query=sql, args=(refresh_token, userNo))

                    data['userNo'] = userNo
                    data['userName'] = userName
                    data['token'] = token
                    data['refresh_token'] = refresh_token

                else :
                    statusCode = 400
                    data['error'] = '아이디 또는 비밀번호가 일치하지 않습니다.'    

            else :
                statusCode = 404
                data['error'] = 'Not in parameter'

        except Exception as e:
            logging.error(traceback.format_exc())
            data['error'] = 'exception error ' +str(e)
            statusCode = 505
            return data, statusCode

        finally:
            #DB CLOSE
            cursor.close()    

        return data, statusCode

