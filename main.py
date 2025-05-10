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
            instruction="""请帮我提取出网页中间的正文的全部信息，不包含广告、评论和网页两侧的其他信息。
要求：
其中的图片链接和非广告链接不要省略
如果涉及到链接不要插入空格、换行等会使链接失效的操作
信息以markdown文本的格式展示

示例:
```markdown
正文信息
```
"""
        ),            
        cache_mode=CacheMode.BYPASS,
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url='https://blog.csdn.net/qq_36387683/article/details/80578480',
            config=run_config
        )
        # print(result.extracted_content)
        print(type(result.extracted_content))
        print(json.loads(result.extracted_content)[0]["content"])


if __name__ == "__main__":
    asyncio.run(main1())