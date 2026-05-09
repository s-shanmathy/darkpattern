path = r'C:\Users\Shanmathy\AppData\Local\Programs\Python\Python311\Lib\site-packages\imgaug\imgaug.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old1 = 'NP_FLOAT_TYPES = set(np.sctypes["float"])'
new1 = 'NP_FLOAT_TYPES = {np.float16, np.float32, np.float64}'
old2 = 'NP_INT_TYPES = set(np.sctypes["int"])'
new2 = 'NP_INT_TYPES = {np.int8, np.int16, np.int32, np.int64}'
old3 = 'NP_UINT_TYPES = set(np.sctypes["uint"])'
new3 = 'NP_UINT_TYPES = {np.uint8, np.uint16, np.uint32, np.uint64}'

content = content.replace(old1, new1)
content = content.replace(old2, new2)
content = content.replace(old3, new3)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('imgaug patched for NumPy 2.0 compatibility.')
