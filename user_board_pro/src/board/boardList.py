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

})

@boardList.route('',methods=['GET'])
class boardListApi(Resource):
    #############################################################
    #게시판 불러오기
    #############################################################
    parser = boardList.parser()
    parser.add_argument('category', type = str, required = False, location = 'body', help='검색구분(writer, contents, title)')
    parser.add_argument('searchText', type = str, required = False, location = 'boady', help='검색어')
    parser.add_argument('page', type = int, required = False, location = 'body', help='페이지 번호 default : 0')
    parser.add_argument('pageSize', type = int, required = False, location = 'body', help='페이지당 데이터 수 default : 20' )
    @boardList.expect(parser)

    @boardList.doc(model = boardListGetModel)
    def get(self):
        """게시판 리스트
        필수 :
        일반 : category, searchText, page, pageSize
        """

        statusCode = 200
        data = {'timestamp' : datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

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

            #총 개수 구하는 sql -base-
            sql = """SELECT count(*) as cnt FROM BOARD_TABLE WHERE DISABLED = 0"""
            cursor.execute(sql)
            total_res = cursor.fetchall()

            #TODO 총 개수를 구하면서 별개의 개수 구하기


            data['total'] = total_res['cnt'] #게시글 총 개수

        except Exception as e :
            logging.error(traceback.format_exc())
            statusCode = 505
            data['error'] = 'exception error ' + str(e)

            return statusCode, data
        finally :
            #db 종료
            cursor.close()

        return data, statusCode