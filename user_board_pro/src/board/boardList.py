#-*- coding : utf-8 -*-
import logging
import traceback
logging.basicConfig(level=logging.ERROR)

from flask import request
from flask_restx import Resource, Namespace, reqparse
import datetime
from src.common.util import *

boardList = Namespace('boardList')

boardListGetModel = boardList.schema_model('boardListGetModel',{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timestamp": {
            "type": "string"
        },
        "total_cnt": {
            "type": "integer"
        },
        "page": {
            "type": "integer"
        },
        "pageSize": {
            "type": "integer"
        },
        "nextPage": {
            "type": "boolean"
        },
        "boardList": {
            "type": "array",
            "items": [{
                "type": "object",
                "properties": {
                    "boardNo": {
                        "type": "integer"
                    },
                    "title": {
                        "type": "string"
                    },
                    "fileNo": {
                        "type": "boolean"
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
                    "boardNo",
                    "title",
                    "fileNo",
                    "writer",
                    "counting",
                    "createdDate"
                    ]
            }]
        }
    },
    "required": [
        "timestamp",
        "total_cnt",
        "page",
        "pageSize",
        "nextPage",
        "boardList"
    ]
})

@boardList.route('',methods=['GET'])
class boardListApi(Resource):
    ###############################################################################
    #GET 게시판 불러오기 // 로그인을 인증 했을 경우 회원이 작성한 글만 리스트로 보여주기
    ###############################################################################
    parser = boardList.parser()
    parser.add_argument('Authorization', type = str, required = False, location='headers', help ='로그인 인증 토큰') #회원이 로그인을 인증하면 자신이 작성한 게시글 보여줌
    parser.add_argument('category', type = str, required = False, location = 'body', help='검색구분(writer, contents, title)')
    parser.add_argument('searchText', type = str, required = False, location = 'boady', help='검색어')
    parser.add_argument('page', type = int, required = False, location = 'body', help='페이지 번호 default : 0')
    parser.add_argument('pageSize', type = int, required = False, location = 'body', help='페이지당 데이터 수 default : 20' )
    @boardList.expect(parser)

    @boardList.doc(model = boardListGetModel)
    def get(self):
        """게시판 리스트
        필수 :
        일반 : Authorization, category, searchText, page, pageSize
        """

        statusCode = 200
        data = {'timestamp' : datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

        #로그인 인증 토큰 확인
        payload = decode_jwt(request.headers)

        parser = reqparse.RequestParser()
        parser.add_argument('category', type = str , required = False)
        parser.add_argument('searchText', type = str , required = False)
        parser.add_argument('page', type = int , required = False)
        parser.add_argument('pageSize', type = int , required = False)
        parameter = parser.parse_args()

        #DB START
        cursor = mysql_cursor(mysql_conn(serverType))
        try :

            hasParam = True
            
            if hasParam :

                #로그인 토큰이 있는지 판단
                userId = None
                if payload is not None :
                    userId = payload['userId']

                category = None
                if parameter['category'] is not None :
                    category = parameter['category']

                searchText = None
                if parameter['searchText'] is not None :
                    searchText = parameter['searchText']

                page = 0
                if parameter['page'] is not None :
                    page = parameter['page']

                pageSize = 20
                if parameter['pageSize'] is not None :
                    pageSize = parameter['pageSize']            

                #게시글 개수 불러오기
                sql = """ SELECT count(*) AS cnt FROM BOARD_TABLE WHERE disabled = 0 """

                #회원이 자신의 게시글을 조회했을 때
                if userId is not None :

                    #회원테이블에 정말 있는 회원있는지 확인
                    user_chk_sql = """SELECT count(*) cnt FROM USER_TABLE WHERE disabled = 0 AND userId = %s """
                    cursor.execute(query=user_chk_sql, args=userId)
                    result = cursor.fetchone()

                    #정상적인 회원이 맞다면 해당 게시글 개수 조회
                    if result['cnt'] == 1 :
                        sql = sql + """ AND writer = '%s' """ %userId

                #로그인 인증을 안 한 회원의 게시글 개수 조회
                else :
                    sql =sql + " "

                #검색어에 따른 개수 구하는 sql 
                if category is not None :
                    search_sql = """ AND %s like '%%%s%%' """ %(category, searchText)
                    sql = sql + search_sql
                    
                cursor.execute(query = sql)
                total_res = cursor.fetchone()
                
                # 게시글이 있으면 게시판 리스트를 불러옴
                if total_res['cnt'] > 0 :
                    
                    list_sql = """ SELECT boardNo, title, fileNo, writer, createdDate, counting  FROM BOARD_TABLE BT WHERE disabled = 0 """

                    #회원이 자신의 게시글 리스트 조회 // 게시글 개수를 조회할 때 userId가 올바르게 들어왔는지 확인 했기 때문에 따로 확인 안 함
                    if userId is not None :
                        list_sql = list_sql + """ AND writer = '%s' """%userId

                    #검색 기능                    
                    if category is not None :
                        search_sql = """ AND %s like '%%%s%%' """ %(category, searchText)
                        list_sql = list_sql + search_sql

                    #order by 
                    list_sql = list_sql + " ORDER BY boardNo desc "

                    #limit
                    list_sql = list_sql + " LIMIT %d, %d " %(pageSize * page, pageSize + 1)
                    cursor.execute(query=list_sql)
                    
                    item_list = []
                    for row in cursor.fetchall() :
                        item = {}
                        item['boardNo'] = row['boardNo']
                        item['title'] = row['title']

                        #파일이 있으면 True 없으면 False
                        item['fileNo'] = False    
                        if row['fileNo'] :
                            item['fileNo'] = True

                        item['writer'] = row['writer']
                        item['counting'] = row['counting']

                        #오늘 날짜이면 HH:MM으로 보여주고 다르면 YYYY-MM-DD로 보여주기
                        item['createdDate'] = row['createdDate'].strftime('%Y-%m-%d')
                        if row['createdDate'].strftime('%Y%m%d') == datetime.datetime.now().strftime('%Y%m%d') :
                            item['createdDate'] = row['createdDate'].strftime('%H:%M')

                        item_list.append(item)

                    data['total_cnt'] = total_res['cnt'] #게시글 총 개수
                    data['page'] = page
                    data['pageSize']  =  pageSize

                    #다음페이지가 있음을 알림
                    nextPage = False
                    if len(item_list) > pageSize :
                        del item_list[-1]
                        nextPage = True

                    data['nextPage']  = nextPage
                    data['boardList'] = item_list

                else :
                    statusCode = 400
                    data['error'] = '게시글이 없습니다.'   

            else : 
                statusCode = 404
                data['error'] = 'Not in parameter'

        except Exception as e :
            logging.error(traceback.format_exc())
            statusCode = 505
            data['error'] = 'exception error ' + str(e)

            return statusCode, data

        finally :
            #db 종료
            cursor.close()

        return data, statusCode