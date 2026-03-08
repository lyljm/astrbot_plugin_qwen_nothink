"""
AstrBot Plugin: Qwen Deep Thinking Toggle

This plugin allows users to toggle Qwen3.5 deep thinking mode via /setthink command.
When enabled, the LLM request will include enable_thinking parameter.
"""

from typing import Optional

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.provider import ProviderRequest
from astrbot.api import logger


@register("astrbot_plugin_qwen_think", "eifying", "Qwen3.5 深度思考模式切换", "1.0.1")
class QwenThinkPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.command("setthink")
    async def setthink(self, event: AstrMessageEvent, enable: Optional[str] = None):
        """切换 Qwen3.5 深度思考模式。
        
        用法:
        - /setthink on - 开启深度思考
        - /setthink off - 关闭深度思考
        - /setthink - 查看当前状态
        """
        if enable is None:
            # 查看当前状态
            current = await self.get_kv_data(f"think_mode", False)
            status = "开启" if current else "关闭"
            yield event.plain_result(f"当前深度思考模式: {status}")
        else:
            # 设置状态
            think_enabled = enable.lower() in ("on", "true", "1", "开启")
            await self.put_kv_data(f"think_mode", think_enabled)
            status = "开启" if think_enabled else "关闭"
            yield event.plain_result(f"深度思考模式已设置为: {status}")

    @filter.on_llm_request()
    async def modify_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """Hook to modify LLM request based on user's think mode setting."""

        # Get user's think mode setting
        think_enabled = await self.get_kv_data(f"think_mode", False)
        
        # Add enable_thinking parameter to request
        # The extra_params dict is passed to the LLM API call
        #req.contexts.append({"think":think_enabled})

        try:
            provider = self.context.get_using_provider(event.unified_msg_origin)
            if provider and hasattr(provider, 'provider_config'):
                # 获取当前的 custom_extra_body（复制一份，避免影响原始配置）
                custom_extra_body = dict(provider.provider_config.get('custom_extra_body', {}))
                # 设置 think 参数
                custom_extra_body['chat_template_kwargs'] = {
                    "enable_thinking": think_enabled,
                }
                provider.provider_config['custom_extra_body'] = custom_extra_body
                logger.info(f"[think_mode] 已设置 custom_extra_body = {provider.provider_config.get('custom_extra_body', {})}")
                logger.info(f"[think_mode] Provider type: {type(provider).__name__}, api_base: {provider.provider_config.get('api_base', 'N/A')}")
            else:
                logger.warning(f"[think_mode] 未找到 Provider 或 provider_config 属性")
        except Exception as e:
            logger.error(f"[think_mode] 设置 Provider custom_extra_body 失败: {e}")

