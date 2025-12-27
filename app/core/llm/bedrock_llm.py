"""
AWS Bedrock LLM integration using LangChain v1.1.0+
"""
from typing import Any, Dict, List, Optional, Union

import boto3
from botocore.config import Config as BotoConfig
from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from app.core.config.environment_config import settings
from app.core.logging.logger import logger
from app.common.exceptions.research_exceptions import LLMRateLimitError


class BedrockLLM:
    """
    Wrapper for AWS Bedrock Claude model via LangChain
    Provides async invoke methods with structured output parsing
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        region: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize Bedrock LLM client

        Args:
            model_id: AWS Bedrock model ID (defaults to config)
            region: AWS region (defaults to config)
            max_tokens: Max output tokens (defaults to config)
            temperature: Model temperature (defaults to config)
        """
        self.model_id = model_id or settings.BEDROCK_MODEL_ID
        self.region = region or settings.AWS_REGION
        self.max_tokens = max_tokens or settings.BEDROCK_MAX_TOKENS
        self.temperature = temperature or settings.BEDROCK_TEMPERATURE

        # Create boto3 client with explicit credentials
        boto_kwargs = {
            'service_name': 'bedrock-runtime',
            'region_name': self.region,
        }

        # Use explicit credentials if provided
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            boto_kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
            boto_kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
            logger.debug('Using explicit AWS credentials from config')
        else:
            logger.debug('Using default AWS credential chain')

        # Create boto3 client with increased timeout
        boto_config = BotoConfig(
            read_timeout=120,
            connect_timeout=10,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
        )
        boto_kwargs['config'] = boto_config

        self.bedrock_client = boto3.client(**boto_kwargs)

        # Initialize LangChain ChatBedrock
        self.llm = ChatBedrock(
            model_id=self.model_id,
            client=self.bedrock_client,
            model_kwargs={
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
            },
        )

        # Output parsers
        self.json_parser = JsonOutputParser()
        self.str_parser = StrOutputParser()

        logger.info(f'Initialized BedrockLLM with model: {self.model_id}')

    async def ainvoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parse_json: bool = False,
    ) -> Union[Dict[str, Any], str]:
        """
        Invoke the LLM asynchronously

        Args:
            prompt: User prompt/query
            system_prompt: Optional system prompt
            parse_json: If True, parse response as JSON

        Returns:
            Parsed response (dict if parse_json, otherwise str)
        """
        try:
            messages = []

            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))

            messages.append(HumanMessage(content=prompt))

            logger.debug(f'Invoking LLM with prompt: {prompt[:100]}...')

            response = await self.llm.ainvoke(messages)

            if parse_json:
                result = self.json_parser.parse(response.content)
            else:
                result = response.content

            logger.debug(f'LLM response received (length: {len(str(result))})')

            return result

        except Exception as e:
            error_msg = str(e).lower()
            if 'rate' in error_msg or 'throttl' in error_msg:
                logger.error(f'LLM rate limit error: {e}')
                raise LLMRateLimitError(f'LLM rate limit exceeded: {e}')
            logger.error(f'LLM invoke error: {e}')
            raise

    async def ainvoke_with_history(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        parse_json: bool = False,
    ) -> Union[Dict[str, Any], str]:
        """
        Invoke LLM with conversation history

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            parse_json: If True, parse response as JSON

        Returns:
            Parsed response
        """
        try:
            lc_messages = []

            if system_prompt:
                lc_messages.append(SystemMessage(content=system_prompt))

            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')

                if role == 'user':
                    lc_messages.append(HumanMessage(content=content))
                elif role == 'assistant':
                    lc_messages.append(AIMessage(content=content))
                elif role == 'system':
                    lc_messages.append(SystemMessage(content=content))

            response = await self.llm.ainvoke(lc_messages)

            if parse_json:
                return self.json_parser.parse(response.content)
            return response.content

        except Exception as e:
            error_msg = str(e).lower()
            if 'rate' in error_msg or 'throttl' in error_msg:
                raise LLMRateLimitError(f'LLM rate limit exceeded: {e}')
            raise

    def invoke_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        parse_json: bool = False,
    ) -> Union[Dict[str, Any], str]:
        """
        Synchronous invoke for CLI commands

        Args:
            prompt: User prompt/query
            system_prompt: Optional system prompt
            parse_json: If True, parse response as JSON

        Returns:
            Parsed response
        """
        try:
            messages = []

            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))

            messages.append(HumanMessage(content=prompt))

            response = self.llm.invoke(messages)

            if parse_json:
                return self.json_parser.parse(response.content)
            return response.content

        except Exception as e:
            error_msg = str(e).lower()
            if 'rate' in error_msg or 'throttl' in error_msg:
                raise LLMRateLimitError(f'LLM rate limit exceeded: {e}')
            raise


def get_llm() -> BedrockLLM:
    """Factory function to get LLM instance"""
    return BedrockLLM()


