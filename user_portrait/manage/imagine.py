# -*- coding:utf-8 -*-

import sys
from elasticsearch import Elasticsearch

from user_portrait.global_utils import es_user_portrait as es

def imagine(uid, query_fields_dict,index_name="user_portrait", doctype='user'):

    """
    uid: search users relate to uid
    query_fields_dict: defined search field weight
    fields: domain, topic, keywords, psycho_status, psycho_feature, activity_geo, hashtag
    for example: "domain": 2

    """

    personal_info = es.get(index="user_portrait", doc_type="user", id=uid, _source=True)['_source']

    query_body = {
        'query':{
            'function_score':{
                'query':{
                    'bool':{
                        'must':[
                        ]
                    }
                },
                "field_value_factor":{
                }
            }
        }
    }

    score_standard = {}
    score_standard["modifier"] = "log1p"
    if query_fields_dict['field'] == "activeness":
        score_standard['field'] = "activeness"
        score_standard['factor'] = 100
    elif query_fields_dict['field'] == "importance":
        score_standard['field'] = "importance"
        score_standard['factor'] = 0.01
    else:
        score_standard['field'] = "influence"
        score_standard['factor'] = 0.1

    query_body['query']['function_score']['field_value_factor'] = score_standard

    query_fields_dict.pop('field')

    for (k,v) in query_fields_dict.items():

        if k == "field": # field specific for outer weight
            continue

        temp = {}
        if v == 1:
            temp[k] = personal_info[k]
        else:
            temp[k] = {'query':personal_info[k],'boost':v}

        query_body['query']['function_score']['query']['bool']['must'].append({'match':temp})



    result = es.search(index=index_name, doc_type=doctype, body=query_body)['hits']['hits']

    uid_list = []
    for item in result:
        info = {}
        info['uid'] = item['_id']
        info['score'] = item['_score']
        uid_list.append(info)

    return uid_list




if __name__ == '__main__':
    print imagine(2001627641, {'topic':1, 'uname':2,'field':'influence'}, index_name='user_portrait', doctype='user')

