import re
from algosdk import encoding
from cid import make_cid
import multihash

regex = re.compile("template-ipfs://{ipfscid:(?P<version>[01]):(?P<codec>[a-z0-9\-]+):(?P<field>[a-z0-9\-]+):(?P<hash>[a-z0-9\-]+)}")

class ARC19:
    def __init__(self, url, reserveAddress):
        self.url = url
        self.reserveAddress = reserveAddress

        matches = regex.match(self.url);
        if matches is None:
            if self.url.startswith("template-ipfs://"):
                raise Exception("unsupported template-ipfs spec")

            self.cid = None
            return

        version = int(matches.group("version"))
        codec = matches.group("codec")
        field = matches.group("field")
        hash = matches.group("hash")

        if field != "reserve":
            raise Exception("unsupported ipfscid field '" + field + "', only reserve is currently supported")

        address = encoding.decode_address(reserveAddress)

        if version == 0 and (codec != "dag-pb" or hash != "sha2-256"):
            raise Exception("cid v0 must always be dag-pb and sha2-256 codec/hash type")

        self.cid = str(make_cid(version, codec, multihash.encode(address, hash)))


    def getCID(self):
        return self.cid;

    def getIPFSURL(self):
        if self.cid is None:
            return self.url

        return "ipfs://" + self.cid
