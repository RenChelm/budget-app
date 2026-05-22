import urllib.request
import json
url = "https://api.github.com/search/code?q=presplash_color+repo:kivy/python-for-android"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    print(urllib.request.urlopen(req).read().decode('utf-8'))
except Exception as e:
    print(e)
