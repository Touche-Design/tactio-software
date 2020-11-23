from json import JSONEncoder
import numpy as np

'''
This class implements a custom enocder for serializing Numpy arrays
'''
class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)