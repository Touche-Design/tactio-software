import numpy as np
import json
from json import JSONEncoder

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


ids = [5, 6]

myDict = {id : np.zeros((1,4,4)) for id in ids}

with open("dict_out.json", "w") as outfile:  
    json.dump(myDict, outfile, cls=NumpyArrayEncoder) 