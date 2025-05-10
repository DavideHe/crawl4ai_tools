import json
import time
from typing import Any, List, Dict, Optional
from openai import OpenAI 

from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.utils import (
    sanitize_html,
    escape_json_string,
    perform_completion_with_backoff,
    extract_xml_data,
    split_and_parse_json_objects,
    sanitize_input_encode,
    merge_chunks,
)
from crawl4ai.prompts import PROMPT_EXTRACT_BLOCKS, PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION, PROMPT_EXTRACT_SCHEMA_WITH_INSTRUCTION, JSON_SCHEMA_BUILDER_XPATH, PROMPT_EXTRACT_INFERRED_SCHEMA
from crawl4ai.models import TokenUsage

class LLMExtractionStrategyCustom(LLMExtractionStrategy):
        
    def extract(self, url: str, ix: int, html: str) -> List[Dict[str, Any]]:
        """
        Extract meaningful blocks or chunks from the given HTML using an LLM.

        How it works:
        1. Construct a prompt with variables.
        2. Make a request to the LLM using the prompt.
        3. Parse the response and extract blocks or chunks.

        Args:
            url: The URL of the webpage.
            ix: Index of the block.
            html: The HTML content of the webpage.

        Returns:
            A list of extracted blocks or chunks.
        """
        if self.verbose:
            # print("[LOG] Extracting blocks from URL:", url)
            print(f"[LOG] Call LLM for {url} - block index: {ix}")

        variable_values = {
            "URL": url,
            "HTML": escape_json_string(sanitize_html(html)),
        }

        prompt_with_variables = PROMPT_EXTRACT_BLOCKS
        if self.instruction:
            variable_values["REQUEST"] = self.instruction
            prompt_with_variables = PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION

        if self.extract_type == "schema" and self.schema:
            variable_values["SCHEMA"] = json.dumps(self.schema, indent=2) # if type of self.schema is dict else self.schema
            prompt_with_variables = PROMPT_EXTRACT_SCHEMA_WITH_INSTRUCTION

        if self.extract_type == "schema" and not self.schema:
            prompt_with_variables = PROMPT_EXTRACT_INFERRED_SCHEMA

        for variable in variable_values:
            prompt_with_variables = prompt_with_variables.replace(
                "{" + variable + "}", variable_values[variable]
            )

        try:
            # print("-------------------------------prompt_with_variables-----------------------------")
            # print(prompt_with_variables)
            if "glm" in self.llm_config.provider.lower():
                # print("----------------------------custom_completion processing------------------------------------")
                response = self.custom_completion(
                    self.llm_config.provider,
                    prompt_with_variables,
                    self.llm_config.api_token,
                    base_url=self.llm_config.base_url,
                    json_response=self.force_json_response,
                    extra_args=self.extra_args,
                )
            else:
                response = perform_completion_with_backoff(
                    self.llm_config.provider,
                    prompt_with_variables,
                    self.llm_config.api_token,
                    base_url=self.llm_config.base_url,
                    json_response=self.force_json_response,
                    extra_args=self.extra_args,
                )  # , json_response=self.extract_type == "schema")
            # Track usage
            usage = TokenUsage(
                completion_tokens=response.usage.completion_tokens,
                prompt_tokens=response.usage.prompt_tokens,
                total_tokens=response.usage.total_tokens,
                completion_tokens_details=response.usage.completion_tokens_details.__dict__
                if response.usage.completion_tokens_details
                else {},
                prompt_tokens_details=response.usage.prompt_tokens_details.__dict__
                if response.usage.prompt_tokens_details
                else {},
            )
            self.usages.append(usage)

            # Update totals
            self.total_usage.completion_tokens += usage.completion_tokens
            self.total_usage.prompt_tokens += usage.prompt_tokens
            self.total_usage.total_tokens += usage.total_tokens

            try:
                response = response.choices[0].message.content
                blocks = None

                if self.force_json_response:
                    blocks = json.loads(response)
                    if isinstance(blocks, dict):
                        # If it has only one key which calue is list then assign that to blocks, exampled: {"news": [..]}
                        if len(blocks) == 1 and isinstance(list(blocks.values())[0], list):
                            blocks = list(blocks.values())[0]
                        else:
                            # If it has only one key which value is not list then assign that to blocks, exampled: { "article_id": "1234", ... }
                            blocks = [blocks]
                    elif isinstance(blocks, list):
                        # If it is a list then assign that to blocks
                        blocks = blocks
                else: 
                    # blocks = extract_xml_data(["blocks"], response.choices[0].message.content)["blocks"]
                    blocks = extract_xml_data(["blocks"], response)["blocks"]
                    blocks = json.loads(blocks)

                for block in blocks:
                    block["error"] = False
            except Exception:
                parsed, unparsed = split_and_parse_json_objects(
                    response.choices[0].message.content
                )
                blocks = parsed
                if unparsed:
                    blocks.append(
                        {"index": 0, "error": True, "tags": ["error"], "content": unparsed}
                    )

            if self.verbose:
                print(
                    "[LOG] Extracted",
                    len(blocks),
                    "blocks from URL:",
                    url,
                    "block index:",
                    ix,
                )
            return blocks
        except Exception as e:
            if self.verbose:
                print(f"[LOG] Error in LLM extraction: {e}")
            # Add error information to extracted_content
            return [
                {
                    "index": ix,
                    "error": True,
                    "tags": ["error"],
                    "content": str(e),
                }
            ]

    def custom_completion(self,provider,prompt_with_variables,api_token,json_response=False,base_url=None,**kwargs,):
        max_attempts = 3
        base_delay = 2
        client = OpenAI(api_key=api_token,base_url=base_url)
        extra_args = {"temperature": 0.7,"top_p":0.98}
        if json_response:
            extra_args["response_format"] = {"type": "json_object"}
        for attempt in range(max_attempts):
            try:
                response = client.chat.completions.create(
                        model=provider,  
                        messages=[     
                            {"role": "user", "content": prompt_with_variables} 
                        ],
                        **extra_args
                    ) 
                return response  # Return the successful response
            except Exception as e:
                # raise e  # Raise any other exceptions immediately
                if attempt < max_attempts - 1:
                    # Calculate the delay and wait
                    delay = base_delay * (2**attempt)  # Exponential backoff formula
                    print(f"Waiting for {delay} seconds before retrying...")
                    time.sleep(delay)
                    print(e)
        return [
                        {
                            "index": 0,
                            "tags": ["error"],
                            "content": ["post llm error. Please try again later."],
                        }
                    ]



if __name__ == "__main__":
    client = OpenAI(
        api_key="9d216ac2bdd92ec3fe9b9d66c32651f0.L3RR9tqTrWBICEMj",
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    ) 

    completion = client.chat.completions.create(
        model="GLM-4-Flash-250414",  
        messages=[    
            {"role": "system", "content": "你是一个聪明且富有创造力的小说作家"},    
            {"role": "user", "content": "请你作为童话故事大王，写一篇短篇童话故事，故事的主题是要永远保持一颗善良的心，要能够激发儿童的学习兴趣和想象力，同时也能够帮助儿童更好地理解和接受故事中所蕴含的道理和价值观。"} 
        ],
        top_p=0.7,
        temperature=0.9,
        response_format = {"type": "json_object"}
    ) 
    print(completion)
    print(completion.usage)
    print("===>:",completion.choices[0].message.content)
    print(json.dumps(json.loads(completion.choices[0].message.content),ensure_ascii=False,indent=4))