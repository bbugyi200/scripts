#!/bin/python
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import sys

url = urlopen('http://www.surfline.com/surf-forecasts/mid-atlantic/new-jersey_2147')
bsObj = BeautifulSoup(url, "html.parser")
top_tag = bsObj.find_all(attrs={'class':'obs-bx'})[0]
strong_tags = top_tag.find_all('strong')
labels = [s.get_text() for s in strong_tags]

mask = 0
regBad = re.compile('poor|none')
regGood = re.compile('fair|good|epic')
for i in range(3):
    label = labels[i]
    if label == 'poor to fair':
        num = 1
    elif regBad.search(label):
        num = 0
    elif regGood.search(label):
        num = 2
    else:
        num = 3

    mask += num * (10**(2-i))

sys.exit(mask)
