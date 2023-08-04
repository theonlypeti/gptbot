import pytest
from EdgeGPT.EdgeGPT import Chatbot
from EdgeGPT.EdgeGPT import ConversationStyle
from EdgeGPT.EdgeUtils import Cookie
import json

from EdgeGPT.EdgeUtils import Query
pytest_plugins = ("pytest_asyncio",)



def test_query():
    Cookie.current_filepath = r"./bing_cookies_my.json"
    # Cookie.import_data()
    cookies = json.loads(open("./bing_cookies_my.json", encoding="utf-8").read())  # might omit cookies option
    # bot = await Chatbot.create(cookies=cookies)
    q = Query("What are you?", cookie_files={r"./bing_cookies_my.json"})
    print(q)
    print(q.output)
    # print(q.sources)
    # print(q.suggestions)

    assert q is not None

def test_image():
    from pathlib import Path
    Cookie.current_filepath = r"./bing_cookies_my.json"
    # Cookie.import_data()
    cookies = json.loads(open("./bing_cookies_my.json", encoding="utf-8").read())  # might omit cookies option
    from EdgeGPT.EdgeUtils import ImageQuery
    Query.image_dirpath = Path("./to_another_folder")

    q = ImageQuery("liminal space")
