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
    #GET ????????? ???????????? // ???????????? ?????? ?????? ?????? ????????? ????????? ?????? ???????????? ????????????
    ###############################################################################
    parser = boardList.parser()
    parser.add_argument('Authorization', type = str, required = False, location='headers', help ='????????? ?????? ??????') #????????? ???????????? ???????????? ????????? ????????? ????????? ?????????
    parser.add_argument('searchType', type = str, required = False, location = 'body', help='????????????(writer, contents, title)')
    parser.add_argument('searchText', type = str, required = False, location = 'boady', help='?????????')
    parser.add_argument('page', type = int, required = False, location = 'body', help='????????? ?????? default : 1')
    parser.add_argument('pageSize', type = int, required = False, location = 'body', help='???????????? ????????? ??? default : 20' )
    @boardList.expect(parser)

    @boardList.doc(model = boardListGetModel)
    def get(self):
        """????????? ?????????
        ?????? :
        ?????? : Authorization, searchType, searchText, page, pageSize
        """

        statusCode = 200
        data = {'timestamp' : datetime.datetime.now().isoformat()}

        serverType, host, ip = get_server_type(request)

        #????????? ?????? ?????? ??????
        payload = decode_jwt(request.headers)

        parser = reqparse.RequestParser()
        parser.add_argument('searchType', type = str , required = False)
        parser.add_argument('searchText', type = str , required = False)
        parser.add_argument('page', type = int , required = False)
        parser.add_argument('pageSize', type = int , required = False)
        parameter = parser.parse_args()

        #DB START
        cursor = mysql_cursor(mysql_conn(serverType))
        try :

            hasParam = True
            
            if hasParam :

                #????????? ????????? ????????? ??????
                userId = None
                if payload is not None :
                    userId = payload['userId']

                searchType = None
                if parameter['searchType'] is not None :
                    searchType = parameter['searchType']

                searchText = None
                if parameter['searchText'] is not None :
                    searchText = parameter['searchText']

                page = 1
                if parameter['page'] is not None :
                    page = parameter['page']

                pageSize = 20
                if parameter['pageSize'] is not None :
                    pageSize = parameter['pageSize']            

                #????????? ?????? ????????????
                sql = """ SELECT count(BT.boardNo) AS cnt """
                cnt_sql = board_list(userId, sql, searchType, searchText)
                cursor.execute(query=cnt_sql)
                cnt_res = cursor.fetchone()

                #????????? ????????? ????????????
                sql = """ SELECT BT.boardNo, BT.title, FT.fileNo, UT.userId, BT.createdDate, BT.counting  """
                list_sql = board_list(userId, sql, searchType, searchText)

                #Page : Limit
                list_sql = list_sql + " LIMIT %d, %d " %(pageSize * (page -1) , pageSize + 1)
                cursor.execute(query=list_sql)

                item_list = []
                for row in cursor.fetchall() :
                    item = {}
                    item['boardNo'] = row['boardNo']
                    item['title'] = row['title']

                    #????????? ????????? True ????????? False
                    item['fileNo'] = False    
                    if row['fileNo'] :
                        item['fileNo'] = True

                    item['userId'] = row['userId']
                    item['counting'] = row['counting']

                    #?????? ???????????? HH:MM?????? ???????????? ????????? YYYY-MM-DD??? ????????????
                    item['createdDate'] = row['createdDate'].strftime('%Y-%m-%d')
                    if row['createdDate'].strftime('%Y%m%d') == datetime.datetime.now().strftime('%Y%m%d') :
                        item['createdDate'] = row['createdDate'].strftime('%H:%M')

                    item_list.append(item)
                    
                data['total_cnt'] = cnt_res['cnt'] #????????? ??? ??????
                data['page'] = page
                data['pageSize']  =  pageSize

                #?????????????????? ????????? ??????
                nextPage = False
                if len(item_list) > pageSize :
                    del item_list[-1]
                    nextPage = True

                data['nextPage']  = nextPage
                data['boardList'] = item_list
                
            else : 
                statusCode = 404
                data['error'] = 'Not in parameter'

        except Exception as e :
            logging.error(traceback.format_exc())
            statusCode = 505
            data['error'] = 'exception error ' + str(e)

            return statusCode, data

        finally :
            #db ??????
            cursor.close()

        return data, statusCode