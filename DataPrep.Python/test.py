import sys
#sys.path.append("utils")
from readApi import readApi
from header-footer import json2df

dat = readApi("../dataset/pdfs/_au_cases_act_ACAT_2020_117.pdf")
df = json2df(dat)

print(df)
