#!/usr/bin/env python
import logging
import os
import re
import sys
import signal
import time
import json
from algosdk.v2client import indexer
import requests
from arc19 import ARC19
from ipfs import IPFS
from time import gmtime

logging.Formatter.converter = gmtime
logging.basicConfig(format="[%(asctime)s.%(msecs)03dZ][%(levelname)s]: %(message)s", datefmt="%Y-%m-%dT%H:%M:%S", level=logging.INFO)

indexerAddress = os.environ.get("INDEXER_HOST") or "https://algoindexer.algoexplorerapi.io"
creatorAddress = os.environ.get("CREATOR_ADDRESS") or "KANIGZX2NQKJKYJ425BWYKCT5EUHSPBRLXEJLIT2JHGTWOJ2MLYCNIVHFI"
ipfsNodeName = os.environ.get("IPFS_HOST") or "ipfs"
ipfsNodePort = os.environ.get("IPFS_PORT") or "5001"
ipfsNodeProto = os.environ.get("IPFS_PROTO") or "http"
ipfsNodeAddress = os.environ.get("IPFS_NODE") or f"{ipfsNodeProto}://{ipfsNodeName}:{ipfsNodePort}"

algoIndexer = indexer.IndexerClient(indexer_token="", indexer_address=indexerAddress)
ipfsClient = IPFS(ipfsNodeAddress)

def signal_handler(signal, frame):
    logging.warning(f"Received signal {signal}, exiting...")
    sys.exit(0)

def extractCID(asset):
    url = asset["params"]["url"]
    cid = ARC19(url, asset["params"]["reserve"]).getCID()
    if cid is not None:
        return "json", cid

    return extractCIDFromURL(url)

def extractCIDFromURL(url):
    ipfsPattern = re.compile("ipfs://(?P<cid>[a-zA-Z0-9]+)(#.*)?")
    matches = ipfsPattern.match(url)
    if matches is not None:
        return "image", matches.group("cid")

    httpPattern = re.compile("http(s)?://[a-zA-Z0-9.]+/ipfs/(?P<cid>[a-zA-Z0-9]+)(\\?.*)?(#.*)?")
    matches = httpPattern.match(url)
    if matches is not None:
        return "image", matches.group("cid")

    return None, None

def pin(cid):
    if ipfsClient.exists(cid):
        return

    logging.info(f"Copying {cid} to local node...")
    ipfsClient.cp(f"/ipfs/{cid}", f"/{cid}")

    logging.info(f"Pinning {cid} to local node...")
    ipfsClient.pin(cid)

def main() -> int:
    while True:
        nextToken = ""
        while nextToken is not None:
            response = algoIndexer.lookup_account_asset_by_creator(creatorAddress, next_page=nextToken)
            nextToken = response.get("next-token")
            for asset in response["assets"]:
                index = asset["index"]
                unit = asset["params"]["unit-name"]
                logging.info(f"Processing ASA {unit} ({index})")

                type, cid = extractCID(asset)
                if cid is None:
                    raise Exception("Could not extract CID from: " + json.dumps(asset, indent=2, sort_keys=True))

                pin(cid)
                if type == "json":
                    logging.info(f"{unit} uses ARC19, retrieving metadata from IPFS...")
                    metadata = ipfsClient.catJson(cid)
                    if metadata is None:
                        raise Exception(f"Could not retrieve {cid} from IPFS!")
                    type, imageCID = extractCIDFromURL(metadata["image"])
                    if imageCID is None:
                        raise Exception("Could not extract ARC19 image CID from: " + json.dumps(metadata, indent=2, sort_keys=True))

                    pin(imageCID)

        sleepTime = int(os.environ.get("POLL_PERIOD") or 3600)
        logging.info(f"Sleeping for {sleepTime} seconds before next check...")
        time.sleep(sleepTime)
    return 0

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    sys.exit(main())
