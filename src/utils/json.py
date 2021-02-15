import simplejson


class _DynamicDictMetadata(object):
    def __init__(self):
        self.construct_mode = False


class DynamicDict(dict):
    METADATA = '__DynamicDict_metadata__'

    def __init__(self, **kwargs):
        self[DynamicDict.METADATA] = _DynamicDictMetadata()

        dict.__init__(self, kwargs)

    def has(self, expr):
        if hasattr(expr, '__call__'):
            try:
                expr()
                return True
            except AttributeError as _:
                return False

        return expr in self

    def nested_get(self, paths):
        path_list = paths

        if isinstance(paths, str):
            path_list = paths.split('.')

        d = self
        for p in path_list:
            d = d.get(p, None)
            if d is None:
                return None

        return d

    def nested_set(self, paths, value):
        path_list = paths

        if isinstance(paths, str):
            path_list = paths.split('.')

        if len(path_list) == 1:
            self[path_list[0]] = value
            return

        key = path_list[-1]
        path_list = path_list[:-1]
        source = self
        for p in path_list:
            target = source.get(p, None)
            if target is None:
                target = DynamicDict()
                source[p] = target

            source = target

        source[key] = value

    def _enter_construct_mode(self):
        self[DynamicDict.METADATA].construct_mode = True

    def _exit_construct_mode(self):
        self[DynamicDict.METADATA].construct_mode = False

    def __enter__(self):
        self._enter_construct_mode()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit_construct_mode()

        def recursively_exit(d):
            for value in d.values():
                if not isinstance(value, DynamicDict):
                    continue

                recursively_exit(value)
                value._exit_construct_mode()

        recursively_exit(self)

    def __getattr__(self, item):
        if self[DynamicDict.METADATA].construct_mode is False and item not in self:
            return None

        if item not in self:
            d = DynamicDict()
            d._enter_construct_mode()
            self[item] = d

        return self[item]

    def __setattr__(self, key, value):
        self[key] = value

    @staticmethod
    def from_dict(schema_dict):
        assert schema_dict is not None, 'schema_dict cannot be null'

        def construct(target, source):
            for key, value in source.items():
                if not isinstance(value, dict):
                    target[key] = value
                    continue

                target[key] = DynamicDict()
                construct(target[key], value)

        ret = DynamicDict()
        construct(ret, schema_dict)
        return ret

    @staticmethod
    def from_json(jstr):
        return DynamicDict.from_dict(loads_as_dict(jstr))

    def to_dict(self):
        return loads_as_dict(self.as_json())

    def as_json(self):
        j = {}
        j.update(self)

        def remove_metadata(d):
            del d[DynamicDict.METADATA]
            for value in d.values():
                if not isinstance(value, DynamicDict):
                    continue

                remove_metadata(value)

        remove_metadata(j)

        return dumps_non_dynamic_dict(j)


def dumps(obj):
    # type: (object) -> str

    if isinstance(obj, DynamicDict):
        return obj.as_json()
    else:
        return dumps_non_dynamic_dict(obj)


def dumps_non_dynamic_dict(obj):
    # type: (object) -> str
    return simplejson.dumps(obj, default=lambda x: x if not hasattr(x, '__dict__') else x.__dict__)


def loads_as_dict(json_str):
    # type: (str) -> dict

    try:
        return simplejson.loads(json_str)
    except simplejson.decoder.JSONDecodeError as ex:
        raise Exception("Unable to json.loads() the string, %s; string to load is:\n%s" % (str(ex), json_str))


def loads(json_str):
    # type: (str) -> DynamicDict

    return DynamicDict.from_json(json_str)
