import json
import requests
import urllib.parse

class IPFS:
    def __init__(self, nodeAddress):
        self.nodeAddress = nodeAddress

    def exists(self, cid):
        response = requests.post(f"{self.nodeAddress}/api/v0/files/ls?arg=%2F{urllib.parse.quote(cid)}")
        jsonData = json.loads(response.text)
        return jsonData.get("Type") != "error"

    def cat(self, cid):
        response = requests.post(f"{self.nodeAddress}/api/v0/cat?arg={urllib.parse.quote(cid)}")
        self.errorCheck(response)
        return response.content

    def catJson(self, cid):
        response = requests.post(f"{self.nodeAddress}/api/v0/cat?arg={urllib.parse.quote(cid)}")
        self.errorCheck(response)
        return json.loads(response.text)

    def cp(self, src, dst):
        response = requests.post(f"{self.nodeAddress}/api/v0/files/cp?arg={urllib.parse.quote(src)}&arg={urllib.parse.quote(dst)}")
        self.errorCheck(response)

    def pin(self, cid):
        response = requests.post(f"{self.nodeAddress}/api/v0/pin/add?arg={urllib.parse.quote(cid)}")
        self.errorCheck(response)
        return json.loads(response.text)

    def errorCheck(self, response):
        if response.headers.get("Content-Type") == "application/json" and len(response.text) > 0:
            jsonData = json.loads(response.text)
            if jsonData.get("Type") == "error":
                code = jsonData.get("Code")
                message = jsonData.get("Message")
                raise Exception(f"IPFS Error ({code}): {message}")
        elif not response.ok:
            response.raise_for_status()
