#-*- coding:utf-8 -*-

import os
import time
import sys
import json
from flask import Blueprint, url_for, render_template, request, abort, flash, session, redirect
from search_user_index_function import search_top_index, search_influence_detail, user_index_range_distribution,\
                                       search_max_single_field, search_portrait_history_active_info
from rank_portrait_in_active_user import search_portrait_user_in_activity, portrait_user_vary
from search_vary_index_function import query_vary_top_k

from user_portrait.global_utils import ES_CLUSTER_FLOW1 as es

portrait_index = "copy_user_portrait" # user_portrait_database
portrait_type = "user"

mod = Blueprint('influence_application', __name__, url_prefix='/influence_application')

@mod.route('/all_active_rank/')
def ajax_all_active_rank():
    date = request.args.get('date', '') # '2013-09-01'
    number = request.args.get('number', 100) # "100"
    date = str(date)
    number = int(number)
    if not date:
        results = []
    else:
        index_name = date.replace('-','')
        results = search_top_index(index_name, number)

    return json.dumps(results)


@mod.route('/portrait_user_in_active/')
def ajax_portrait_user_in_active():
    date = request.args.get('date', '') # '2013-09-01'
    number = request.args.get('number', 100) # "100"
    date = str(date)
    number = int(number)
    if not date:
        results = []
    else:
        index_name = date.replace('-','')
        results = search_portrait_user_in_activity(es, number, index_name, "bci", portrait_index, portrait_type)

    return json.dumps(results)


@mod.route('/specified_user_active/')
def ajax_specified_user_active():
    date = request.args.get('date', '') # '2013-09-01'
    uid = request.args.get('uid', '') # 123456,123456
    date = str(date)

    if not date or not uid:
        results = []
    else:
        index_name = date.replace('-','')
        list_1 = []
        uid_list = [item for item in uid.split(',')]
        results = search_influence_detail(uid_list, index_name, "bci") 

    return json.dumps(results)



@mod.route('/user_index_distribution/')
def ajax_user_index_distribution():
    date = request.args.get('date', '') # '2013-09-01'
    date = str(date)

    if not date:
        results = []
    else:
        index_name = date.replace('-','')
        results = user_index_range_distribution(index_name, "bci", "user_index")

    return json.dumps(results)

@mod.route('/portrait_user_index_distribution/')
def ajax_portrait_user_index_distribution():
    date = request.args.get('date', '') # '2013-09-01'
    date = str(date)

    if not date:
        results = []
    else:
        date = date.replace('-','')
        results = user_index_range_distribution("copy_user_portrait","user", date)

    return json.dumps(results)

"""
@mod.route('/portrait_user_domain_rank/')
def ajax_portrait_user_domain_rank():
    results = []
    date = request.args.get('date', '')
    domain = request.args.get('domain', '')
    number = request.args.get('number', '')
    if date and domain:
        results = portrait_user_domain_rank(date, domain, number)

    return json.dumps(results)
"""
@mod.route('/hot_origin_weibo/')
def ajax_hot_origin_weibo():
    date = request.args.get('date', '') # '2013-09-01'
    number = request.args.get('number', 100) # default
    date = str(date)
    number= int(number)

    results = []
    if date:
        index_name = date.replace('-','')
        dict_1 = search_max_single_field("origin_weibo_retweeted_top_number", index_name, "bci", number)
        dict_2 = search_max_single_field("origin_weibo_comment_top_number", index_name, "bci", number)
        results.append(dict_1)
        results.append(dict_2)

    return json.dumps(results)

@mod.route('/hot_origin_weibo_brust/')
def ajax_hot_origin_weibo_brust():
    date = request.args.get('date', '') # '2013-09-01'
    number = request.args.get('number', 100) # default
    date = str(date)
    number = int(number)

    if not date:
        results = []
    else:
        index_name = date.replace('-','')

        results = []
        dict_1 = search_portrait_user_in_activity(es, number, index_name, "bci", portrait_index, portrait_type, field="origin_weibo_retweeted_brust_average")
        dict_2 = search_portrait_user_in_activity(es, number, index_name, "bci", portrait_index, portrait_type, field="origin_weibo_comment_brust_average")
        results.append(dict_1)
        results.append(dict_2)

    return json.dumps(results)


@mod.route('/portrait_history_active/')
def ajax_portrait_history_active():
    date = request.args.get('date', '')# 2013-09-01
    uid = request.args.get('uid', '')

    if not uid or not date:
        results = []
    else:
        date = str(date).replace('-','')
        results = search_portrait_history_active_info(uid, date)

    return json.dumps(results)

@mod.route('/vary_top_k/')
def ajax_vary_top_k():
    results = []
    number = request.args.get('number', 100) # "100"
    number = int(number)

    results = query_vary_top_k("vary", "bci", number)

    return json.dumps(results)



@mod.route('/portrait_user_in_vary/')
def ajax_portrait_user_in_vary():
    number = request.args.get('number', 100) # "10"
    results = portrait_user_vary(es, number, "vary", "bci", portrait_index, portrait_type, "vary")

    return json.dumps(results)

