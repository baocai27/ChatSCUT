from flask import Flask, request,jsonify
from flask_cors import CORS

import time
app = Flask(__name__)
CORS(app)
# 这里放函数什么的


def test():
    for i in range(10):
        print(1)
        time.sleep(1)





# 这下面就是具体接口
@app.route("/",methods=['POST'])
def metaHuman():
    if request.is_json:
        text = request.get_json()["message"]
        #text已经是字符串了，直接放入函数即可,下面调用函数
        test()#测试用，随便删
        #到此为止 
        return jsonify({'done': 'done'}) 
    else:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    
if __name__ == "__main__":
    app.run('0.0.0.0',port=3050,debug=True)
