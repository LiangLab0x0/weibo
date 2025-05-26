"""
Browser Use AI代理基类

封装Browser Use的Agent创建和基础操作
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable
from browser_use import Agent
from langchain_openai import ChatOpenAI

from app.core.config import settings


logger = logging.getLogger(__name__)


class BaseAgent:
    """Browser Use基础代理类"""
    
    def __init__(
        self, 
        task_description: str = "执行浏览器自动化任务",
        temperature: float = 0.1,
        max_retries: int = 3
    ):
        """
        初始化基础代理
        
        Args:
            task_description: 任务描述
            temperature: LLM温度参数
            max_retries: 最大重试次数
        """
        self.task_description = task_description
        self.temperature = temperature
        self.max_retries = max_retries
        self.llm = self._create_llm()
        self.agent = None
        
    def _create_llm(self) -> ChatOpenAI:
        """创建DeepSeek LLM实例"""
        return ChatOpenAI(
            model="deepseek-chat",  # 使用deepseek-chat而不是deepseek-reasoner，因为reasoner不支持工具调用
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=self.temperature,
            max_tokens=8192  # 增加最大token数以避免截断
        )
    
    def _create_agent(self, task_prompt: str) -> Agent:
        """为特定任务创建Browser Use Agent实例"""
        import os
        
        # 设置环境变量确保无头模式
        os.environ['PLAYWRIGHT_HEADLESS'] = 'true'
        os.environ['DISPLAY'] = ':99'
        
        return Agent(
            task=task_prompt,
            llm=self.llm
        )
    
    async def execute_task(
        self, 
        task_prompt: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        执行浏览器自动化任务
        
        Args:
            task_prompt: 任务提示词
            progress_callback: 进度回调函数
            
        Returns:
            任务执行结果
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"开始执行任务 (尝试 {attempt + 1}/{self.max_retries})")
                
                if progress_callback:
                    progress_callback(f"正在执行任务... (尝试 {attempt + 1})")
                
                # 在Docker环境中，通过monkeypatch禁用input调用
                import builtins
                original_input = builtins.input
                builtins.input = lambda prompt="": ""
                
                try:
                    # 启动xvfb虚拟显示
                    import subprocess
                    import asyncio
                    
                    # 启动xvfb进程
                    xvfb_process = subprocess.Popen(
                        ['Xvfb', ':99', '-screen', '0', '1024x768x24', '-ac'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    
                    # 等待xvfb启动
                    await asyncio.sleep(2)
                    
                    try:
                        # 为当前任务创建专门的Agent
                        agent = self._create_agent(task_prompt)
                        
                        # 执行任务 - Browser Use的Agent.run()不接受参数
                        result = await agent.run()
                    finally:
                        # 清理xvfb进程
                        try:
                            xvfb_process.terminate()
                            xvfb_process.wait(timeout=5)
                        except:
                            try:
                                xvfb_process.kill()
                            except:
                                pass
                finally:
                    # 恢复原始input函数
                    builtins.input = original_input
                
                logger.info("任务执行成功")
                return {
                    "success": True,
                    "result": result,
                    "attempt": attempt + 1
                }
                
            except Exception as e:
                logger.error(f"任务执行失败 (尝试 {attempt + 1}): {str(e)}")
                
                if attempt == self.max_retries - 1:
                    # 最后一次尝试失败
                    return {
                        "success": False,
                        "error": str(e),
                        "attempt": attempt + 1
                    }
                
                # 等待后重试
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        return {
            "success": False,
            "error": "达到最大重试次数",
            "attempt": self.max_retries
        }
    
    async def close(self):
        """关闭代理资源"""
        if self.agent:
            # Browser Use可能需要清理资源
            try:
                await self.agent.close()
            except Exception as e:
                logger.warning(f"关闭代理时出现警告: {str(e)}")
            finally:
                self.agent = None 