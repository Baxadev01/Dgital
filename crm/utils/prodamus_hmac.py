import json
import hmac
import hashlib


class HmacProdamus:
    @staticmethod
    def dict_string_value(obj: dict):
        for key, value in obj.items():
            if isinstance(value, list):
                for listKey, listValue in enumerate(value):
                    obj[key][listKey] = HmacProdamus.dict_string_value(listValue)
            elif isinstance(value, dict):
                obj[key] = HmacProdamus.dict_string_value(value)
            elif isinstance(value, int):
                obj[key] = str(value)

        return obj

    @staticmethod
    def create(api_secret: str, obj: dict):
        obj_stringify = HmacProdamus.dict_string_value(obj)
        obj_json = json.dumps(obj_stringify, ensure_ascii=False, separators=(',', ':'), sort_keys=True)
        obj_json = obj_json.replace('/', '\/')

        return hmac.new(bytes(api_secret, 'utf-8'),
                        msg=bytes(obj_json, 'utf-8'),
                        digestmod=hashlib.sha256).hexdigest()

    @staticmethod
    def verify(api_secret: str, obj: dict, sign: str):
        _sign = HmacProdamus.create(api_secret, obj)
        return _sign and (_sign == sign.lower())
    
    
def normalize_dict(dict):
    new_dict = {}

    for key in dict:
        ar = key.replace('][',',').replace('[',',').replace(']','').split(',')
        
        if len(ar) > 1:
            if new_dict.get(ar[0], None) == None:
                new_dict[ar[0]] = [{}]
            new_dict[ar[0]][int(ar[1])][ar[2]] = dict[key]
        else:
            new_dict[ar[0]] = dict[key]

    return new_dict