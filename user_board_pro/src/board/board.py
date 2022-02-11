#-*- coding : utf-8 -*-
import logging
import shutil
import traceback
logging.basicConfig(level=logging.ERROR)

from flask import request
from flask_restx import Resource, Namespace, reqparse
from werkzeug.datastructures import FileStorage  #파일 업로드
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
        "contents": {
            "type": "string"
        },
        "fileName": {
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
        "contents",
        "fileName",
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
boardDeleteModel = board.schema_model('boardDeletModel', {
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
                    sql = """SELECT bt.title, bt.writer, bt.contents, bt.counting, bt.createdDate, ft.fileNameOrigin
                    FROM BOARD_TABLE BT
                    LEFT JOIN FILE_TABLE FT  ON bt.fileNo = ft.fileNo 
                    WHERE bt.disabled= 0 AND bt.boardNo = %s"""
                    cursor.execute(query= sql, args=boardNo)
                    result =  cursor.fetchone()

                    data['title'] = result['title']
                    data['writer'] = result['writer']
                    data['contents'] = result['contents']

                    #파일이 있으면 파일 이름을 보여줌
                    data['fileName'] = None
                    if result['fileNameOrigin'] is not None :
                        data['fileName'] = result['fileNameOrigin']

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
    parser.add_argument("file", type = FileStorage, required = False, location = 'files', help='파일')
    @board.expect(parser)

    @board.doc(model = boardPostModel)
    def post(self):
        """
        게시글 작성하기
        필수 : Authorization, title, contents
        일반 : file
        """
        
        statusCode = 200
        data = {'timestamp': datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

        #로그인 인증 토큰이 있는지 확인
        payload = decode_jwt(request.headers)
        if payload is None :
            statusCode = 401
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

                #파일 등록
                file = None
                if 'file' in request.files :
                    file = request.files['file']

                #정상적인 토큰을 가진 회원인지 조회
                sql = """SELECT count(userNo) AS cnt FROM USER_TABLE UT WHERE disabled = 0 AND userId = %s""" 
                cursor.execute(query= sql, args= userId)
                result = cursor.fetchone()

                #정상적인 경로로 왔을 때
                if result['cnt'] == 1: 

                    hasProcess = True
                    if file is None:
                        fileNo = None
                        hasProcess = False

                    #request.file에 파일이 있으면 파일 저장을 진행함
                    if hasProcess :    
                        filePath = 'files/board/'

                        #원본 파일명
                        fileNameOrigin = file.filename

                        #저장될 파일 이름 변경
                        fileName = str(uuid.uuid4()) +pathlib.Path(fileNameOrigin).suffix

                        #파일 전체 경로
                        fileFullPath = filePath + fileName

                        #파일 타입
                        contentType = file.content_type

                        #파일 저장
                        file.save(fileFullPath)

                        #파일 크기
                        fileSize = os.path.getsize(fileFullPath)

                        file_sql = """INSERT INTO FILE_TABLE (fileName, fileNameOrigin, contentType, filesize, fileFullPath)
                        VALUES (%s,%s,%s,%s,%s) """
                        cursor.execute(query=file_sql, args=(fileName, fileNameOrigin,contentType,fileSize, fileFullPath))
                        fileNo = cursor.lastrowid

                    sql = """INSERT INTO BOARD_TABLE (writer, title, contents, fileNo) 
                    VALUES (%s, %s, %s, %s)  """
                    cursor.execute(query=sql, args=(userId, title, contents, fileNo))
                    boardNo = cursor.lastrowid

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
    parser.add_argument("file", type = FileStorage, required = False, location = 'files', help='파일')
    @board.expect(parser)

    @board.doc(model = boardPutModel)
    def put(self) :
        """
        게시글 수정하기
        필수 : Authorization, boardNo
        일반 : title, contents, file
        """

        statusCode = 200
        data = {'timestamp' : datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

        #로그인 인증 토큰이 있는지 확인
        payload = decode_jwt(request.headers)
        if payload is None :
            statusCode = 401
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
                
                file = None
                if 'file' in request.files :
                    file = request.files['file']
                
                #정상적인 토큰을 가진 회원이 해당 게시물 번호를 가지고 있는지 확인
                sql = """SELECT count(*) AS cnt, ft.fileFullPath AS prefilePath, ft.fileNo
                FROM USER_TABLE UT 
                LEFT JOIN BOARD_TABLE BT ON ut.userId = bt.writer
                LEFT JOIN FILE_TABLE FT ON bt.fileNo = ft.fileNo 
                WHERE ut.disabled = 0 AND bt.disabled = 0 AND ut.userId = %s AND bt.boardNo = %s """

                cursor.execute(query=sql , args=(userId, boardNo))
                result = cursor.fetchone()

                #올바른 경로로 왔다면 수정을 허용함   
                if result['cnt'] == 1:

                    hasProcess = True
                    if file is None :
                        hasProcess = False

                    #request.file에 파일이 있으면 이전 파일을 삭제하고 파일 저장을 진행함
                    if hasProcess :

                        #이전 파일을 삭제
                        os.remove(result['prefilePath'])
                        
                        filePath = 'files/board/'

                        #원본 파일명
                        fileNameOrigin = file.filename

                        #저장될 파일 이름 변경
                        fileName = str(uuid.uuid4()) +pathlib.Path(fileNameOrigin).suffix

                        #파일 전체 경로
                        fileFullPath = filePath + fileName

                        #파일 타입
                        contentType = file.content_type

                        #파일 저장
                        file.save(fileFullPath)

                        #파일 크기
                        fileSize = os.path.getsize(fileFullPath)
                        
                        file_sql = """ UPDATE FILE_TABLE SET fileName = %s, fileNameOrigin=%s, contentType=%s, fileSize=%s, fileFullPath=%s WHERE fileNo = %s """
                        cursor.execute(query= file_sql, args= (fileName, fileNameOrigin, contentType, fileSize, fileFullPath, result['fileNo']))

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

    @board.doc(model= boardDeleteModel)
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

                #정상적인 토큰을 가진 사용자와 사용자의 게시물인지 조회 및 그 게시물의 파일정보를 추가로 불러옴
                sql = """SELECT count(*) AS cnt, ft.fileNo, ft.fileName, ft.fileFullPath AS delFilePath
                FROM USER_TABLE UT 
                LEFT JOIN BOARD_TABLE BT ON ut.userId = bt.writer
                LEFT JOIN FILE_TABLE FT ON bt.fileNo = ft.fileNo 
                WHERE ut.disabled = 0 AND bt.disabled = 0 AND ut.userId = %s AND bt.boardNo = %s """

                cursor.execute(query=sql , args=(userId, boardNo))
                result = cursor.fetchone()

                #올바른 경로로 왔다면 disabled 수정을 허용함
                if result['cnt'] == 1:

                    sql = """ UPDATE BOARD_TABLE SET disabled = 1 WHERE writer = %s AND boardNo = %s """
                    cursor.execute(query=sql, args=(userId, boardNo))
                    data['success'] = 'disabled 수정 완료' 

                    #게시글 데이터가 삭제되면 해당 파일도 disabled = 1로 변환 /// 로컬의 원본 파일은 지우지 않고 휴지통(trash)폴더에 보관
                    hasProcess = True
                    if result['fileNo'] is None:
                        hasProcess = False

                    if hasProcess :
                        delFilePath = 'files/board/trash/' #휴지통 PATH
                        delFileFullPath = delFilePath+result['fileName']
                        shutil.move(result['delFilePath'], delFileFullPath )

                        file_sql = """ UPDATE FILE_TABLE SET disabled = 1, fileFullPath = %s WHERE fileNo = %s  """
                        cursor.execute(query= file_sql, args=(delFileFullPath, result['fileNo']))

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