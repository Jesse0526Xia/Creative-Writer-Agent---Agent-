"""
LLM 调用层 - 统一接口封装
支持豆包/Kimi API
"""
import os
import json
from typing import Optional, List, Dict, Any, Generator
from openai import OpenAI, AsyncOpenAI
from app.config import settings


class LLMClient:
    """大语言模型统一调用客户端"""

    def __init__(self, provider: str = None):
        """
        初始化LLM客户端

        Args:
            provider: "doubao" 或 "kimi"，默认使用配置中的active_llm
        """
        self.provider = provider or settings.active_llm
        self._client = None
        self._async_client = None

    @property
    def client(self) -> OpenAI:
        """同步客户端"""
        if self._client is None:
            if self.provider == "doubao":
                self._client = OpenAI(
                    api_key=settings.doubao_api_key,
                    base_url=settings.doubao_base_url
                )
            elif self.provider == "kimi":
                self._client = OpenAI(
                    api_key=settings.kimi_api_key,
                    base_url=settings.kimi_base_url
                )
            elif self.provider == "deepseek":
                self._client = OpenAI(
                    api_key=settings.deepseek_api_key,
                    base_url=settings.deepseek_base_url
                )
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        return self._client

    @property
    def async_client(self) -> AsyncOpenAI:
        """异步客户端"""
        if self._async_client is None:
            if self.provider == "doubao":
                self._async_client = AsyncOpenAI(
                    api_key=settings.doubao_api_key,
                    base_url=settings.doubao_base_url
                )
            elif self.provider == "kimi":
                self._async_client = AsyncOpenAI(
                    api_key=settings.kimi_api_key,
                    base_url=settings.kimi_base_url
                )
            elif self.provider == "deepseek":
                self._async_client = AsyncOpenAI(
                    api_key=settings.deepseek_api_key,
                    base_url=settings.deepseek_base_url
                )
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        return self._async_client

    @property
    def model(self) -> str:
        """获取当前模型"""
        if self.provider == "doubao":
            return settings.doubao_model
        elif self.provider == "kimi":
            return settings.kimi_model
        elif self.provider == "deepseek":
            return settings.deepseek_model
        return "unknown"

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        同步调用LLM生成文本

        Args:
            prompt: 用户提示
            system: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他OpenAI参数

        Returns:
            生成的文本
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content

    async def acomplete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        异步调用LLM生成文本

        Args:
            prompt: 用户提示
            system: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他OpenAI参数

        Returns:
            生成的文本
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content

    def stream_complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        流式调用LLM生成文本

        Args:
            prompt: 用户提示
            system: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他OpenAI参数

        Yields:
            逐步生成的文本片段
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def structured_complete(
        self,
        prompt: str,
        response_format: Dict[str, Any],
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        结构化输出调用

        Args:
            prompt: 用户提示
            response_format: 期望的响应格式 (JSON Schema)
            system: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            解析后的结构化数据
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({
            "role": "user",
            "content": prompt + "\n\n请按照以下JSON格式返回:\n```json\n" +
                      json.dumps(response_format, ensure_ascii=False) + "\n```"
        })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    return json.loads(content[start:end].strip())
            raise ValueError(f"Failed to parse JSON response: {content[:200]}")

    def chat_complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        多轮对话调用

        Args:
            messages: 对话历史 [{"role": "user/assistant/system", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的回复
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content


# 全局LLM客户端实例
llm_client = LLMClient()


def get_llm_client(provider: str = None) -> LLMClient:
    """获取LLM客户端"""
    return LLMClient(provider)
