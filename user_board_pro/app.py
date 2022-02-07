#-*- coding : utf8 -*-
from flask import Flask
from flask_restx import Api
from flask_cors import CORS

#################################
# src -> user, board
#################################
from src.user.join import join
from src.user.login import login
from src.board.board import board
from src.board.boardList import boardList

app = Flask(__name__)
api = Api(app, version=1.0, title="user_board_pro", terms_url="/")

#CORS처리
CORS(app, resource = {r'*' :{"origins" :"http:192.168.0.116:8087"}})
CORS(app, resource = {r'*' :{"origins" :"http:192.168.0.116:8088"}})

api.add_namespace(join, '/join')
api.add_namespace(login, '/login')
api.add_namespace(board, '/board')
api.add_namespace(boardList, '/boardList')

if __name__ == '__main__' :
    app.run(debug=True, host='0.0.0.0', port=8087)