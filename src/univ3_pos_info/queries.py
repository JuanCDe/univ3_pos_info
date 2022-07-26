import urllib.request
import json


def query_thegraph(query, variables):
    req = urllib.request.Request("https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3")
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = {"query": query, "variables": variables}
    jsondataasbytes = json.dumps(jsondata).encode('utf-8')
    req.add_header('Content-Length', len(jsondataasbytes))
    response = urllib.request.urlopen(req, jsondataasbytes)
    resp = json.load(response)
    return resp