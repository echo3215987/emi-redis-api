# coding:utf-8

import os
import json
from response import initResponse, parseResponseJson, setErrorResponse
from log import logging
import redis
import datetime
from sqlalchemy import create_engine
import pandas as pd

from flask import Flask, request
app = Flask(__name__)

# host = 'localhost'
host = '10.142.3.61'
password = 'emi2wsx'
port = 6379
pool = redis.ConnectionPool(host=host, port=port, decode_responses=True)
r = redis.Redis(host=host, port=port, password=password, decode_responses=True)

engine = create_engine('mysql+pymysql://root:123456@'+host+':3306/ipcamera?charset=utf8mb4', echo=False)

# new round
@app.route('/emi/roundinfo/<string:line>/<string:station>/', methods = ['GET'])
def queryRound(line, station):
    jsObj = r.hgetall(line + station)
    return parseResponseJson(jsObj)

# camera quality
@app.route('/emi/cameraquality/<string:line>/<string:station>/', methods = ['GET'])
def queryCameraQuality(line, station):
    jsObj = r.get(line + station + 'Q')
    return parseResponseJson(jsObj)

# (no use)top 3 class error
@app.route('/emi/classerror/<string:line>/<string:station>/<string:op_id>/', methods = ['GET'])
def queryClassError(line, station, op_id):
    jsObj = r.hgetall(line + station+op_id)
    return parseResponseJson(jsObj)

# save op info
@app.route('/emi/opinfo/<string:line>/<string:station>/<string:instation_time>/<string:op_id>/<string:op_name>/', methods = ['GET'])
def saveOPInfo(line, station, instation_time, op_id, op_name):
    try:
        request_data = {}
        request_data['line'] = line
        request_data['station'] = station
        in_station_time = datetime.datetime.strptime(instation_time, '%Y%m%d%H%M%S')
        request_data['in_station_time'] = str(in_station_time)
        request_data['op_id'] = op_id
        request_data['op_name'] = op_name
        ## save redis
        r.hmset(line + station + 'op_info', request_data)
        ## save mysql
        op_df = pd.DataFrame(request_data, index=[0])
        op_df.to_sql('op_info', con=engine, index=False, if_exists='append')
        return initResponse()
    except KeyError:
        logging.error("KeyError: parameter error")
        return setErrorResponse(10001, "parameter error")
    except TypeError:
        logging.error("TypeError: format must json type")
        return setErrorResponse(10002, "format must json type")
    except redis.exceptions.DataError:
        logging.error("redis.exceptions.DataError")
        return setErrorResponse(10003, "redis.exceptions.DataError")
    except ValueError:
        logging.error("ValueError: date format error")
        return setErrorResponse(10004, "time format invalid(rule: only number and 14 character)")

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=False, port=33000)
