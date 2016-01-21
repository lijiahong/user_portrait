#-*- coding:utf-8 -*-

import os
import time
import json
from flask import Blueprint, url_for, render_template, request, abort, flash, session, redirect
from user_portrait.time_utils import datetime2ts, ts2datetime
from user_portrait.global_utils import R_SOCIAL_SENSING as r
from user_portrait.global_utils import es_user_portrait as es
from user_portrait.parameter import INDEX_MANAGE_SOCIAL_SENSING as index_manage_sensing_task
from user_portrait.parameter import DOC_TYPE_MANAGE_SOCIAL_SENSING as task_doc_type
from user_portrait.parameter import DETAIL_SOCIAL_SENSING as index_sensing_task
from user_portrait.parameter import finish_signal, unfinish_signal
from utils import get_warning_detail, get_text_detail

mod = Blueprint('social_sensing', __name__, url_prefix='/social_sensing')

index_group_manage = "group_manage"
doc_type_group = "group"

# 前台设置好的参数传入次函数，创建感知任务,放入es, 从es中读取所有任务信息放入redis:sensing_task 任务队列中
# parameters: task_name, create_by, stop_time, remark, social_sensors, keywords
# other parameters: create_at, warning_status,
# warning_status: 0-no, 1-burst, 2-tracking, 3-ever_brusing, now no
# task_type：任务类型：{"0": no keywords and no sensors, "1": no keywords and some sensors, "2": "some keywords and no sensors", "3": "some keywords and some sensors"}
@mod.route('/create_task/')
def ajax_create_task():
    # task_name forbid illegal enter
    task_name = request.args.get('task_name','') # must
    create_by = request.args.get('create_by', '') # must
    stop_time = request.args.get('stop_time', "default") #timestamp, 1234567890
    social_sensors = request.args.get("social_sensors", "") #uid_list, split with ","
    keywords = request.args.get("keywords", "") # keywords_string, split with ","
    remark = request.args.get("remark", "")

    if task_name and create_by:
        task_detail = dict()
        task_detail["task_name"] = task_name
        task_detail["create_by"] = create_by
        task_detail["stop_time"] = stop_time
        task_detail["remark"] = remark
        task_detail["social_sensors"] = json.dumps(social_sensors.split(','))
        task_detail["keywords"] = json.dumps(keywords.split(","))
        now_ts = int(time.time())
        task_detail["create_at"] = now_ts
        task_detail["warning_status"] = '0'
        task_detail["finish"] = "0" # not end the task
        task_detail["history_status"] = json.dumps([]) # ts, keywords, warning_status
        task_detail['burst_reason'] = ''
        if keywords:
            if social_sensors:
                task_detail["task_type"] = "3"
            else:
                task_detail["task_type"] = "2"
        else:
            if social_sensors:
                task_detail["task_type"] = "1"
            else:
                task_detail["task_type"] = "0"
    else:
        return json.dumps([])


    # store task detail into es
    es.index(index=index_manage_sensing_task, doc_type=task_doc_type, id=task_name, body=task_detail)


    return json.dumps(["1"])


@mod.route('/delete_task/')
def ajax_delete_task():
    # delete task based on task_name
    task_name = request.args.get('task_name','') # must
    if task_name:
        #r.pop("task_name", task_name)
        es.delete(index=index_manage_sensing_task, doc_type=task_doc_type, id=task_name)
        #es.delete(index_sensing_task, task_name)
        return json.dumps(['1'])
    else:
        return json.dumps([])


# 终止任务，即在到达终止时间前就终止任务
@mod.route('/stop_task/')
def ajax_stop_task():
    task_name = request.args.get('task_name','') # must
    if task_name:
        task_detail = es.get(index=index_manage_sensing_task, doc_type=task_doc_type, id=task_name)['_source']
        task_detail["finish"] = finish_signal
        es.index(index=index_manage_sensing_task, doc_type=task_doc_type, id=task_name, body=task_detail)
        return json.dumps(['1'])
    else:
        return json.dumps([])


# 修改任务终止时间
@mod.route('/revise_task/')
def ajax_revise_task():
    task_name = request.args.get('task_name','') # must
    finish = request.args.get("finish", "")
    stop_time = request.args.get('stop_time', '') # timestamp

    now_ts = time.time()
    if stop_time and stop_time < now_ts:
        return json.dumps([])

    if task_name:
        task_detail = es.get(index=index_manage_sensing_task, doc_type=task_doc_type, id=task_name)['_source']
        if stop_time:
            task_detail['stop_time'] = stop_time
        if int(finish) == 0:
            task_detail['finish'] = finish
        if stop_time or int(finish) == 0:
            es.index(index=index_manage_sensing_task, doc_type=task_doc_type, id=task_name, body=task_detail)
            return json.dumps(['1'])
    return json.dumps([])



@mod.route('/show_task/')
def ajax_show_task():
    # show all working task
    status = request.args.get("finish", "01")
    length = len(status)
    query_body = {
        "query":{
            "filtered":{
                "filter":{
                }
            }
        },
        "sort": {"create_at": {"order": "desc"}},
        "size": 10000
    }
    if length == 2:
        category_list = [status[0], status[1]]
        query_body['query']['filtered']['filter']['terms'] = {"finish": category_list}
    elif length == 1:
        query_body['query']['filtered']['filter']['term'] = {"finish": status}
    else:
        print "error"

    search_results = es.search(index=index_manage_sensing_task, doc_type=task_doc_type, body=query_body)['hits']['hits']

    results = []
    for item in search_results:
        results.append(item['_source'])

    return json.dumps(results)

# unfinished
@mod.route('/get_group_list/')
def ajax_get_group_list():
    # get all group list from group manage
    results = [] # 
    query_body = {
        "query":{
            "match_all": {}
        },
        "sort": {"submit_date": {"order": "desc"}},
        "size": 10000
    }

    search_results = es.search(index=index_group_manage, doc_type=doc_type_group, body=query_body, timeout=600)['hits']['hits']
    for item in search_results:
        temp = []
        temp.append(item['task_name'])
        temp.append(json.loads(item['uid_list']))
        results.append(temp)

    return json.dumps(results)



# 返回某个预警事件的详细信息，包括微博量、情感和参与的人
@mod.route('/get_warning_detail/')
def ajax_get_warning_detail():
    task_name = request.args.get('task_name','') # task_name
    keywords = request.args.get('keywords', '') # warning keywords
    ts = request.args.get('ts', '') # timestamp: 123456789

    results = get_warning_detail(task_name, keywords, ts)

    return json.dumps(results)


# 返回某个时间段特定的文本，按照热度排序
@mod.route('/get_text_detail/')
def ajax_get_text_detail():
    task_name = request.args.get('task_name','') # task_name
    keywords = request.args.get('keywords', '') # warning keywords
    ts = request.args.get('ts', '') # timestamp: 123456789

    results = get_text_detail(task_name, keywords, ts)

    return json.dumps(results)

