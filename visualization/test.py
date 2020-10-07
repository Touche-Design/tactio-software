import numpy as np
a = np.zeros((1,4,4))
b = np.array([[1,2,3,4],[1,2,3,4],[1,2,3,4],[1,2,3,4]])
print(a)
print(b)

a = np.append(a,np.expand_dims(b,axis=0),axis=0)
print(a)
print(a.shape)
for x in np.arange(a.shape[0]):
    print(x)