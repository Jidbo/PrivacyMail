import difflib
import hashlib
import base64
import urllib


# From https://stackoverflow.com/questions/774316/python-difflib-highlighting-differences-inline/788780#788780
def inline_diff(a, b):
    matcher = difflib.SequenceMatcher(None, a, b)

    def process_tag(tag, i1, i2, j1, j2):
        if tag == "replace":
            return "{" + matcher.a[i1:i2] + " -> " + matcher.b[j1:j2] + "}"
        if tag == "delete":
            return "{- " + matcher.a[i1:i2] + "}"
        if tag == "equal":
            # return matcher.a[i1:i2]
            return ""
        if tag == "insert":
            return "{+ " + matcher.b[j1:j2] + "}"
        assert False, "Unknown tag %r" % tag

    return "".join(process_tag(*t) for t in matcher.get_opcodes())


def generate_match_dict(mailaddr):
    hashdict = {}
    encdict = {}

    hashdict.update({"Mailaddress": mailaddr})
    hashdict.update({"Email Account": mailaddr.split("@")[0]})
    hashdict.update({"Address Domain": mailaddr.split("@")[1]})

    def create_upper_lower(dict, only_up=False):
        tempdict = {}
        for key, value in dict.items():
            if not key.startswith("up"):
                tempdict.update({"up(" + key + ")": value.upper()})
            if only_up:
                continue
            if (not key.startswith("plain") and not key.startswith("low")
                    and not key.startswith("domain")):
                tempdict.update({"low(" + key + ")": value.lower()})
        return tempdict

    def create_algo_dict(old_dict):
        algorithms = ["md5", "md4", "sha1", "sha256", "sha512", "sha384"]
        # Add upper and lower versions to be hashed, but don't add those to the enc dict.
        # Comparison takes place on casefold URL
        temp_dict = create_upper_lower(old_dict, True)
        temp_dict.update(old_dict)
        new_dict = {}
        for key, value in temp_dict.items():
            for algo in algorithms:
                h = hashlib.new(algo)
                h.update(value.encode("utf8"))
                new_dict.update({algo + "(" + key + ")": h.hexdigest()})
        return new_dict

    hashdict.update(create_algo_dict(hashdict))

    # One level of nesting
    hashdict.update(create_algo_dict(hashdict))

    encdict = {}

    for key, val in hashdict.items():
        encdict.update({
            "base64(" + key + ")":
            base64.b64encode(val.encode("utf8")).decode(
                "utf-8", "replace")
        })

    encdict.update({"urlencode(plain)": urllib.parse.quote(mailaddr)})

    # put dicts together
    hashdict.update(encdict)

    return hashdict
