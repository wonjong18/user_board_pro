#-*- coding : utf-8 -*-
import logging
import traceback
from attr import has
logging.basicConfig(level=logging.ERROR)

from flask import request
from flask_restx import Resource, Namespace, reqparse
import datetime
from src.common.util import *

board = Namespace('board')

boardGetModel = board.schema_model('boardGetModel', {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timestamp": {
            "type": "string"
        },
        "title": {
            "type": "string"
        },
        "writer": {
            "type": "string"
        },
        "counting": {
            "type": "integer"
        },
        "createdDate": {
            "type": "string"
        }
    },
    "required": [
        "timestamp",
        "title",
        "writer",
        "counting",
        "createdDate"
    ]
})
boardPostModel = board.schema_model('boardPostModel' , {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timestamp": {
            "type": "string"
        },
        "boardNo": {
            "type": "integer"
        }
    },
    "required": [
        "timestamp",
        "boardNo"
]
})
boardPutModel = board.schema_model('boardPutModel', {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timestamp": {
            "type": "string"
        },
        "success": {
            "type": "string"
        }
    },
    "required": [
        "timestamp",
        "success"
    ]
})
boardDeletModel = board.schema_model('boardDeletModel', {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timestamp": {
            "type": "string"
        },
        "success": {
            "type": "string"
        }
    },
    "required": [
        "timestamp",
        "success"
    ]
})

@board.route('', methods = ['GET', 'POST', 'PUT', 'DELETE'] )
class boardApi(Resource):
    #################################################################
    #GET : 게시판 상세조회하기 // 회원 비회원 상관 없이 조회 가능
    #################################################################

    parser = board.parser()
    parser.add_argument("boardNo", type = int, required = True, location= 'body', help='게시글 번호')
    @board.expect(parser)

    @board.doc(model=boardGetModel)
    def get(self):
        """
        게시글 상세 조회
        필수 : boardNo
        알반 :
        """
        statusCode = 200
        data = {'timestamp' : datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

        parser = reqparse.RequestParser()
        parser.add_argument("boardNo", type = int, required= True)
        parameter = parser.parse_args()

        #DB START
        cursor = mysql_cursor(mysql_conn(serverType))
        try:
            hasParam = True
            if 'boardNo' not in parameter or parameter['boardNo'] =='' :
                hasParam = False

            if hasParam :
                boardNo = parameter['boardNo']

                sql = """SELECT count(*) AS cnt FROM BOARD_TABLE BT WHERE disabled = 0  AND boardNo =%s"""
                cursor.execute(query=sql, args=boardNo)
                res = cursor.fetchone()

                if res['cnt'] == 1 :
                    #조회수 처리
                    sql = """UPDATE BOARD_TABLE SET counting = counting + 1 WHERE boardNo = %s"""
                    cursor.execute(query=sql, args=boardNo)

                    #게시글 상세 조회
                    sql = """SELECT title, writer, counting, createdDate, updatedDate  
                    FROM BOARD_TABLE BT 
                    WHERE disabled= 0 AND boardNo = %s"""
                    cursor.execute(query= sql, args=boardNo)
                    result =  cursor.fetchone()

                    data['title'] = result['title']
                    data['writer'] = result['writer']
                    data['counting'] = result['counting']
                    data['createdDate'] = result['createdDate'].strftime('%Y-%m-%d %H:%M')

                else :
                    statusCode = 400
                    data['error'] ='등록된 데이터가 없습니다.'

            else :
                statusCode = 404
                data['error'] = 'Not in parameter'    
        except Exception as e :
            logging.error(traceback.format_exc())
            statusCode = 505
            data['error'] = 'exception error ' + str(e)

            return statusCode, data
        finally :
            #DB CLOSE
            cursor.close()

        return data, statusCode

    #################################################################
    #POST : 게시글 작성하기 //로그인이 된 사람만 작성할 수 있음
    #################################################################
    parser = board.parser()
    parser.add_argument("Authorization", type=str, required = True, location = 'headers', help='로그인 인증 토큰' )
    parser.add_argument("title", type=str, required=True, location ='body', help='제목')
    parser.add_argument("contents", type = str, required=True, location = 'body', help='내용')
    @board.expect(parser)

    @board.doc(model = boardPostModel)
    def post(self):
        """
        게시글 작성하기
        필수 : Authorization, title, contents
        일반 : 
        """
        
        statusCode = 200
        data ={'timestamp': datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

        #로그인 인증 토큰이 있는지 확인
        payload = decode_jwt(request.headers)
        if payload is None :
            statusCode = 401
            #TODO refreshtoken을 이용한 accesstoken 재발급..?으로 권한 재생성 해야함
            data['error'] = '토큰이 만료되었거나, 인증되지 않은 사용자입니다.'
            return data, statusCode

        parser = reqparse.RequestParser()
        parser.add_argument("title", type = str, required=True)
        parser.add_argument("contents", type = str, required=True)
        parameter = parser.parse_args()
        
        #DB START
        cursor = mysql_cursor(mysql_conn(serverType))
        try:
            hasParam = True
            if 'userId' not in payload or payload['userId'] == '' :
                hasParam = False
            if 'title' not in parameter or parameter['title'] == '' :
                hasParam = False
            if 'contents' not in parameter or parameter['contents'] == '':
                hasParam = False
            
            if hasParam :
                userId = payload['userId']
                title = parameter['title']
                contents = parameter['contents']       

                sql = """SELECT count(userNo) AS cnt FROM USER_TABLE UT WHERE disabled = 0 AND userId = %s""" 
                cursor.execute(query= sql, args= userId)
                result = cursor.fetchone()

                #정상적인 경로로 왔을 때
                if result['cnt'] == 1: 
                    sql = """INSERT INTO BOARD_TABLE (writer, title, contents) VALUES (%s, %s, %s)  """
                    cursor.execute(query=sql, args=(userId, title, contents))
                    boardNo= cursor.lastrowid
                    data['boardNo'] = boardNo
                else : 
                    statusCode = 400
                    data['error'] = '접근경로가 잘 못 되었습니다.'    

                
            else :
                statusCode = 404
                data['error'] = 'Not in parameter'
        except Exception as e :
            logging.error(traceback.format_exc())
            statusCode = 505
            data['error'] = 'exception error ' + str(e)

            return statusCode, data   

        finally :
            #DB CLOSE
            cursor.close()     
        return data, statusCode



    #################################################################
    #PUT : 게시글 수정하기 //로그인을 하고 해당 사람만 수정할 수 있음
    #################################################################
    parser = board.parser()
    parser.add_argument("Authorization", type = str, required = True, location = 'headers', help = '로그인 인증 토큰')
    parser.add_argument("boardNo", type=int, required = True, location = "body", help='게시글 no')
    parser.add_argument('title', type =str, required = False, location = 'body', help='제목')
    parser.add_argument('contents', type =str, required = False, location = 'body', help='내용')
    @board.expect(parser)

    @board.doc(model = boardPutModel)
    def put(self) :
        """
        게시글 수정하기
        필수 : Authorization, boardNo
        일반 : title, contents
        """

        statusCode = 200
        data = {'timestamp' : datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

        #로그인 인증 토큰이 있는지 확인
        payload = decode_jwt(request.headers)
        if payload is None :
            statusCode = 401
            #TODO refreshtoken을 이용한 accesstoken 재발급..?으로 권한 재생성 해야함
            data['error'] = '토큰이 만료되었거나, 인증되지 않은 사용자입니다.'
            return data, statusCode

        parse = reqparse.RequestParser()
        parse.add_argument("boardNo", type = int, required = True)    
        parse.add_argument("title", type = str, required = False)
        parse.add_argument("contents", type = str, required = False)
        parameter = parse.parse_args()

        #DB START
        cursor = mysql_cursor(mysql_conn(serverType))
        try :
            hasParam = True
            if 'userId' not in payload or payload['userId'] =='':
                hasParam = False
            if 'boardNo' not in parameter or parameter['boardNo']  =='':
                hasParam = False
            
            if hasParam :    
                userId = payload['userId']
                boardNo = parameter['boardNo']

                title = None
                if 'title' in parameter :
                    title = parameter['title']

                contents = None
                if 'contents' in parameter :
                    contents = parameter['contents']    

                sql = """SELECT count(*) AS cnt 
                FROM USER_TABLE UT 
                LEFT JOIN BOARD_TABLE BT ON ut.userId = bt.writer 
                WHERE ut.disabled = 0 AND bt.disabled = 0 AND ut.userId = %s AND bt.boardNo = %s """

                cursor.execute(query=sql , args=(userId, boardNo))
                result = cursor.fetchone()

                #올바른 경로로 왔다면 수정을 허용함
                if result['cnt'] == 1:

                    sql = """UPDATE BOARD_TABLE  SET title = %s, contents = %s WHERE writer = %s AND boardNo = %s """
                    cursor.execute(query=sql, args= (title, contents, userId, boardNo) )
                    data['success'] = '수정 완료'
                else :
                    statusCode = 400
                    data['error'] = '해당 작성자의 게시물이 아닙니다.'

            else:
                statusCode = 404
                data['error'] = 'Not in parameter'

        except Exception as e :
            logging.error(traceback.format_exc())
            statusCode = 505
            data['error'] = 'exception error ' + str(e)

            return data, statusCode
        finally :
            #db 종료
            cursor.close()    
        return data, statusCode    


    #################################################################
    #DELETE : 게시글 삭제하기 //로그인을 하고 해당 사람만 삭제할 수 있음
    #################################################################
    parser = board.parser()
    parser.add_argument("Authorization", type = str, required = True, location = 'headers', help = '로그인 인증 토큰')
    parser.add_argument("boardNo", type=int, required = True, location = "body", help='게시글 no')
    @board.expect(parser)

    @board.doc(model= boardDeletModel)
    def delete(self):
        """
        게시글 삭제
        필수 : Authorization, boardNo
        일반 :
        """

        statusCode = 200
        data = {'timestamp' : datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

        #로그인 인증 토큰이 있는지 확인
        payload = decode_jwt(request.headers)
        if payload is None :
            statusCode = 401
            #TODO refreshtoken을 이용한 accesstoken 재발급..?으로 권한 재생성 해야함
            data['error'] = '토큰이 만료되었거나, 인증되지 않은 사용자입니다.'
            return data, statusCode
        
        parse = reqparse.RequestParser()
        parse.add_argument('boardNo', type = int, required= True)
        parameter = parse.parse_args()

        #DB START
        cursor = mysql_cursor(mysql_conn(serverType))
        try :
            hasParam = True
            if "userId" not in payload or payload['userId'] == '' :
                hasParam = False
            if "boardNo" not in parameter or parameter['boardNo'] == '' :
                hasParam = False

            if hasParam :
                userId = payload['userId']
                boardNo = parameter['boardNo']        

                sql = """SELECT count(*) AS cnt 
                FROM USER_TABLE UT 
                LEFT JOIN BOARD_TABLE BT ON ut.userId = bt.writer 
                WHERE ut.disabled = 0 AND bt.disabled = 0 AND ut.userId = %s AND bt.boardNo = %s """

                cursor.execute(query=sql , args=(userId, boardNo))
                result = cursor.fetchone()

                #올바른 경로로 왔다면 disabled 수정을 허용함
                if result['cnt'] == 1:

                    sql = """ UPDATE BOARD_TABLE SET disabled = 1 WHERE writer = %s AND boardNo = %s """
                    cursor.execute(query=sql, args=(userId, boardNo))
                    data['success'] = 'disabled 수정 완료' 

                else : 
                    statusCode = 400
                    data['error'] = '해당 작성자의 게시물이 아닙니다.' 

            else:
                statusCode = 404
                data['error'] = 'Not in parameter'

        except Exception as e :
            logging.error(traceback.format_exc())
            statusCode = 505
            data['error'] = 'exception error ' + str(e)

            return data, statusCode
        finally :
            #db 종료
            cursor.close()
        return data, statusCode        