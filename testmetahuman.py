# -*- coding: utf-8 -*-
import re
import requests

text = "要拿到奖学金，首先需要关注学校奖学金和社会捐赠奖学金的申请条件。你好。"

#url是你接口的地址
url = "http://localhost:8080"
ans = requests.post(url=url,json={"message":text})
print(ans)