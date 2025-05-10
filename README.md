## 这是一个crawl4ai爬虫自用工具

## 目的
crawl4ai只支持llmlite支持的api，这会给国内用户带来比较大的麻烦，很多api都很贵且不定能访问  
仓库工具支持了glm的api（因为它提供了免费的flash版本，目前使用起来指令上基本没问题）

## 步骤
1. 安装crawl4ai以及依赖,建议py3.12->[crawl4ai-github](https://github.com/unclecode/crawl4ai)
2. 去glm注册账号，获取api_key -> [glm-4 文档](https://bigmodel.cn/dev/activities/free/glm-4-flash)
3. 运行`main.py`,里面有两个demo，一个是通过网页获取信息，json格式返回，另一个是爬取网页的text内容。都试了下，flash的准确度还可以。

