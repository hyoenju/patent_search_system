from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from gensim.models.word2vec import Word2Vec
from text_search.models import Patent
from text_search.models import PatentEmbedding
from django.db.models import Q

from django.core import serializers
#
# import re
# import json
import pickle
import operator
import multiprocessing
from functools import reduce
from datetime import datetime

import numpy as np
# from sklearn.manifold import TSNE
from MulticoreTSNE import MulticoreTSNE as TSNE
from sklearn.cluster import KMeans


model = Word2Vec.load('word2vec.model')
# patent_list, embedding_list = pickle.load(open("patent_field_best_model.embed", "rb"))


def index(request):
    return render(request, 'text_search/index.html')


def wordcloud_search(request):
    search_keyword = request.GET['keyword']
    list_search_keyword = [word.lower().strip() for word in search_keyword.split() if word != 'and']
    try:
        similar_words = model.wv.most_similar(list_search_keyword, topn=30)
        similar_words = [{'word': w, 'size': 60 - (i * 1.5)} for i, (w, _) in enumerate(similar_words)]
    except Exception:
        similar_words = []
    context = {"myWords": similar_words}
    return JsonResponse(context)


patent_id_list = []


def text_result(request):
    global patent_id_list
    final_keyword = request.GET['keyword']
    keyword_list = [word.lower().strip() for word in final_keyword.split() if word != 'and']
    # 특허는 최신순서로 정렬
    time_1 = datetime.now()
    print(time_1)
    # data_list = Patent.objects.filter(reduce(operator.and_, (Q(abstract__contains=k) for k in keyword_list))).order_by('-date')[:10000]
    # data_list = Patent.objects.filter(reduce(operator.and_, (Q(abstract__contains=k) for k in keyword_list))).order_by('-date')
    data_list = Patent.objects.filter(reduce(operator.and_, (Q(abstract__contains=k) for k in keyword_list))).order_by('-date')
    time = datetime.now()
    print(time-time_1)
    time_1 = time

    data_list = list(data_list.values('patent_id', 'title', 'abstract', 'country', 'date', 'kind', 'number'))
    # data_list = data_list.values('patent_id', 'title', 'abstract', 'country', 'date', 'kind', 'number')
    #data_list = data_list.values_list('patent_id', 'title', 'abstract', 'country', 'date', 'kind', 'number')

    patent_id_list = [data['patent_id'] for data in data_list]
    result = {"data_list": data_list}

    time = datetime.now()
    print(time-time_1)

    return JsonResponse(result, safe=False)

    # serialized_qs = serializers.serialize('json', data_list)
    # time = datetime.now()
    # print(time - time_1)
    # return HttpResponse(serialized_qs, content_type='application/json; charset=UTF-8')


# def tsne_transform(data, lr=100, n_jobs=-1):
#     tsne = TSNE(learning_rate=lr, n_jobs=n_jobs)
#     transformed = tsne.fit_transform(data)
#     return transformed[:, 0].tolist(), transformed[:, 1].tolist()


def kmeans_clustering(data, n_cluster=10, n_jobs=-1):
    kmeans = KMeans(n_clusters=n_cluster, n_jobs=n_jobs)
    kmeans.fit(data)
    return kmeans.labels_


from tsnecuda import TSNE
from collections import defaultdict


def tsne_transform(data):
    tsne = TSNE()
    transformed = tsne.fit_transform(data)
    return transformed
    # return transformed[:, 0].tolist(), transformed[:, 1].tolist()

#
# def kmeans_clustering(data, n_cluster=10):
#     kmeans = KMeans(n_clusters=n_cluster)
#     kmeans.fit(data)
#     return kmeans.labels_


def convert_string_to_npy(data):
    data['embedding'] = np.fromstring(data['embedding'], dtype=np.float32, sep=' ')
    return data['patent_id'], data['embedding']


def get_patent_embedding(query_data):
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        patent_embedding = list(p.imap(convert_string_to_npy, query_data))
    return zip(*patent_embedding)


def clustering_map(request):
    global patent_id_list
    time_1 = datetime.now()
    print(time_1)
    # patent_id_list = request.GET['patent_id'].split(',')
    patent_embedding = PatentEmbedding.objects.filter(patent_id__in=patent_id_list).values()

    time = datetime.now()
    print(time-time_1)

    patent_ids, embedding_list = get_patent_embedding(patent_embedding)
    embedding_list = np.array(embedding_list)

    time = datetime.now()
    print(time-time_1)

    transformed = tsne_transform(embedding_list).tolist()
    # return JsonResponse(transformed, safe=False)

    labels = kmeans_clustering(embedding_list).tolist()

    grouped_tsne = defaultdict(list)
    for label, pid, xy in zip(labels, patent_ids, transformed):
        grouped_tsne[label].append(xy)
        # x, y = xy
        # grouped_tsne[label].append({'x': x, 'y': y})

    # results = []
    # for key in range(10):
    #     print(key, len(grouped_tsne[key]))
    #     results.append({'label': key, 'data': grouped_tsne[key]})
    results = [{'label': key, 'data': grouped_tsne[key]} for key in grouped_tsne]
    return JsonResponse(results, safe=False)



    x_values, y_values = tsne_transform(embedding_list)

    time = datetime.now()
    print(time-time_1)

    labels = kmeans_clustering(embedding_list)
    labels = list(map(lambda x: "cluster_"+str(x), labels))


    time = datetime.now()
    print(time-time_1)

    # x_values = transformed[:, 0].tolist()
    # y_values = transformed[:, 1].tolist()
    #
    # s_x, b_x = min(x_values), max(x_values)
    # s_y, b_y = min(y_values), max(y_values)
    xy_value = [{'x_value': x, "y_value": y, "cluster": label}
                for x, y, label in zip(x_values, y_values, labels)]

    axis_value = {'s_x': min(x_values),
                  'b_x': max(x_values),
                  's_y': min(y_values),
                  'b_y': max(y_values)}

    # b_x = max(transformed[:, 0]).tolist()
    # s_x = min(transformed[:, 0]).tolist()
    # b_y = max(transformed[:, 1]).tolist()
    # s_y = min(transformed[:, 1]).tolist()

    time = datetime.now()
    print(time-time_1)
# <<<<<<< HEAD
#     # print(data_list)
#     return JsonResponse(data_list, safe=False)
# =======
    # result = {"x_value" : transformed[:, 0].tolist(),
    #             "y_value" : transformed[:, 1].tolist()}
    # print(type(result['x_value'].tolist()[0]))
    # print(result)
    # result = serialize('json', result)
    # result = json.dumps(result, cls=NumpyEncoder)
    # result = json.dumps(str(result))
    # result = serializers.serialize("json", result)
    # print(result)
    result = {'xy': xy_value, 'axis': axis_value}
    return JsonResponse(result, safe=False)
