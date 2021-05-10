import json
import functools
import pathlib

def memoize(function):
    cache = {}
    @functools.wraps(function)
    def result(*args, clear_cache=False, ignore_cache=False, skip_cache=False, **kwargs):
        nonlocal cache
        call = (args, tuple(kwargs.items()))
        if clear_cache:
            cache = {}
        if call in cache and not ignore_cache:
            return cache[call]
        res = function(*args, **kwargs)
        if not skip_cache:
            cache[call] = res
        return res
    return result

@memoize
def load_json_config(path="renderConf.json", mode="r"):
    # Update the path to reflect location
    path = f"{pathlib.Path(__file__).parent.absolute()}/{path}"
    with open(path, mode) as stream:
        js = json.load(stream)
    return js


class Configuration(dict):
    def __getitem__(self, key):
        return load_json_config()[key]
    def __setitem__(self, _k, _v):
        pass

config = Configuration()
