import os,json
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field

from zhipu_utils import LLMExtractionStrategyCustom 

from crawl4ai import config
# os.environ["GLM_API_KEY"] =  "you api key"
# config.PROVIDER_MODELS.update({"GLM-4-Flash-250414":os.getenv("GLM_API_KEY")})
# base_url = "https://open.bigmodel.cn/api/paas/v4/"
from api_config import *  ## 包含自己信息
provider = "GLM-4-Flash-250414"

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")

async def main():
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=1,
        extraction_strategy=LLMExtractionStrategyCustom(
            # Here you can use any provider that Litellm library supports, for instance: ollama/qwen2
            # provider="ollama/qwen2", api_token="no-token", 
            llm_config = LLMConfig(provider=provider, api_token=os.getenv('GLM_API_KEY'),base_url=base_url), 
            schema=OpenAIModelFee.model_json_schema(),
            extraction_type="schema",
            instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
            Do not miss any models in the entire content. One extracted model JSON format should look like this: 
            {"model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens"}."""
        ),            
        cache_mode=CacheMode.BYPASS,
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url='https://openai.com/api/pricing/',
            config=run_config
        )
        print(json.dumps(json.loads(result.extracted_content),ensure_ascii=False,indent=4))


async def main1():
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=1,
        extraction_strategy=LLMExtractionStrategyCustom(
            llm_config = LLMConfig(provider=provider, api_token=os.getenv('GLM_API_KEY'),base_url=base_url), 
            # schema=OpenAIModelFee.model_json_schema(),
            extraction_type="text",   ## extraction_type: "block" or "schema" or text.
            instruction="""上面是一篇网页爬取的html内容整理成markdown的形式，其中包含广告和其他无用的信息，请帮我去除掉。

要求：
- 提取的信息以markdown文本的格式展示正文的层次结构
- 图片需要严格按照![xxx](xxxxxx)格式整理，图片信息单独成行显示 
- 先识别出哪些内容是渲染在网页两边的，哪些是渲染在中间的；正文一般是中间部分的内容，请帮我提取这部分正文内容，正文部分可能包含广告请帮我过滤掉这些内容
- 底部要是有评论，请保留，用户头像可以用 ![用户名](图像链接) 的markdown形式生成
- 正文中间和正文相关的引用的图片链接和非广告链接不能省略,不要遗漏，以 ![图片title](图片链接) 的markdown形式生成
- 代码示例如果为了网页渲染需求有不规范的语法内容请帮我整理成合规的语法(一般是去除掉一些无用的渲染字符)
- 表格采用markdown的表格展示，表格信息不能省略

示例:
```markdown
提取的正文信息
![图片title](图片链接)
```python
python code
```
```
"""
        ),            
        cache_mode=CacheMode.BYPASS,
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            # url='https://blog.csdn.net/qq_36387683/article/details/80578480',
            url='https://data.eastmoney.com/bkzj/BK0729.html',
            config=run_config
        )
        # print(result.extracted_content)
        print(type(result.extracted_content))
        print(json.loads(result.extracted_content)[0]["content"])

if __name__ == "__main__":
    asyncio.run(main1())