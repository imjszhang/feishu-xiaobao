from fastapi import APIRouter, HTTPException, Query, Depends, Body

import json
import re
from ..dependencies import verify_api_key

from typing import Dict, Optional, List, Union
import random
import asyncio
from ..handlers.feishu_docx_api_handler_async import FeishuDocxAPIHandler, BlockFactory, BlockType


class FeishuDocxContentManager:
    """飞书文档内容管理器，用于管理文档中的内容块"""
    
    # 可用的背景颜色和边框颜色
    AVAILABLE_COLORS = list(range(1, 14))  # 1-13的颜色值
    
    # 可用的emoji列表
    AVAILABLE_EMOJIS = [
        "smile", "heart", "ok", "bulb", "star", "sun", "moon", "cloud",
        "rain", "zap", "trophy", "medal", "gift", "fire", "leaf", "music",
        "bell", "thumbsup", "coffee", "game", "flag", "book", "gear",
        "clock", "rocket", "target", "calendar", "pin", "paperclip",
        "scissors", "pencil", "folder", "inbox", "camera", "video",
        "microphone", "headphones", "art", "chart", "graph", "link",
        "lock", "key", "hammer", "wrench", "package", "truck"
    ]
    
    def __init__(self, app_id: str, app_secret: str):
        """
        初始化飞书文档内容管理器
        
        Args:
            app_id: 飞书应用的APP ID
            app_secret: 飞书应用的APP Secret
        """
        self.docx_handler = FeishuDocxAPIHandler(app_id, app_secret)
    
    async def initialize(self):
        """
        初始化 FeishuDocxAPIHandler
        """
        await self.docx_handler.initialize()
    
    def _get_random_callout_style(self) -> tuple:
        """
        随机生成callout的样式
        
        Returns:
            tuple: (background_color, border_color, emoji_id)
        """
        background_color = random.choice(self.AVAILABLE_COLORS)
        border_color = random.choice(self.AVAILABLE_COLORS)
        emoji_id = random.choice(self.AVAILABLE_EMOJIS)
        return background_color, border_color, emoji_id
    
    async def _get_parent_info(self, document_id: str, target_block_id: str) -> tuple:
        """
        获取父块ID和目标块索引
        
        Returns:
            tuple: (parent_id, target_index)
        """
        # 获取目标块的信息
        target_block_info = await self.docx_handler.get_block_contents(document_id, target_block_id)
        if not target_block_info or not target_block_info.get('data'):
            raise ValueError("获取目标块信息失败")
            
        parent_id = target_block_info['data']['block']['parent_id']
        
        # 获取父块的所有子块
        parent_children = await self.docx_handler.get_block_children(document_id, parent_id)
        if not parent_children or not parent_children.get('data'):
            raise ValueError("获取父块子块信息失败")
            
        # 找到目标块在父块中的位置
        target_index = next(
            (i for i, block in enumerate(parent_children['data'].get('items', []))
             if block.get('block_id') == target_block_id),
            -1
        )
        
        if target_index == -1:
            raise ValueError("未找到目标块位置")
            
        return parent_id, target_index
    



    async def _add_single_callout(self, 
                        document_id: str, 
                        parent_id: str, 
                        index: int, 
                        content: Dict[str, any]) -> Optional[int]:
        """
        添加单个callout块及其内容
        
        Args:
            document_id: 文档ID
            parent_id: 父块ID
            index: 插入位置
            content: callout内容数据
            
        Returns:
            Optional[int]: 成功返回下一个插入位置的索引，失败返回None
        """
        try:
            # 1. 创建空的callout块
            bg_color, border_color, emoji = self._get_random_callout_style()
            empty_callout = BlockFactory.create_callout_block(
                content=" ",
                background_color=bg_color,
                border_color=border_color,
                emoji_id=emoji
            )
            
            callout_response = await self.docx_handler.create_block(
                document_id=document_id,
                block_id=parent_id,
                children=[empty_callout],
                index=index
            )
            
            if not callout_response or callout_response.get('code') != 0:
                raise ValueError(f"创建callout块失败: {callout_response.get('msg')}")
            
            # 获取新创建的callout块的ID
            callout_block_id = callout_response['data']['children'][0]['block_id']
            
            # 2. 准备并添加callout的子块
            child_blocks = []
            
            # 添加标题
            title_block = BlockFactory.create_block(
                block_type=BlockType.HEADING2,
                text_runs=[{
                    "content": content.get("title", ""),
                    "text_element_style": {
                        "bold": True,
                        "inline_code": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False
                    }
                }]
            )
            child_blocks.append(title_block)
            
            # 添加bullet points
            for bullet in filter(None, content.get("bullets", [])):
                bullet_block = BlockFactory.create_block(
                    block_type=BlockType.BULLET,
                    text_runs=[{
                        "content": bullet,
                        "text_element_style": {}
                    }]
                )
                child_blocks.append(bullet_block)
            
            # 添加链接
            if link := content.get("link"):
                link_block = BlockFactory.create_block(
                    block_type=BlockType.TEXT,
                    text_runs=[
                        {
                            "content": "原文链接：",
                            "text_element_style": {"bold": True}
                        },
                        {
                            "content": "查看原文",
                            "text_element_style": {
                                "link": {"url": link}
                            }
                        }
                    ]
                )
                child_blocks.append(link_block)
            
            # 添加子块到callout中
            child_response = await self.docx_handler.create_block(
                document_id=document_id,
                block_id=callout_block_id,
                children=child_blocks
            )
            
            if not child_response or child_response.get('code') != 0:
                raise ValueError(f"创建子块失败: {child_response.get('msg')}")
            
            # 3. 删除callout中的第一个空白子块
            callout_children = await self.docx_handler.get_block_children(document_id, callout_block_id)
            
            if callout_children and callout_children.get('code') == 0:
                delete_response = await self.docx_handler.delete_block(
                    document_id=document_id,
                    block_id=callout_block_id,
                    start_index=0,
                    end_index=1
                )
                
                if not delete_response or delete_response.get('code') != 0:
                    print(f"警告：删除第一个子块失败: {delete_response.get('msg')}")
            
            return index + 1
            
        except Exception as e:
            print(f"添加callout块失败: {str(e)}")
            return None

    async def add_content_blocks(self, 
                        document_id: str, 
                        target_block_id: str, 
                        date_str: str, 
                        content_data: Union[Dict[str, any], List[Dict[str, any]]]) -> bool:
        try:
            # 初始化 FeishuDocxAPIHandler
            await self.initialize()

            # 获取父块信息
            parent_id, target_index = await self._get_parent_info(document_id, target_block_id)
            
            # 确保content_data是列表
            contents = content_data if isinstance(content_data, list) else [content_data]
        
            # 1. 添加所有callout块
            for content in contents:
                next_index = await self._add_single_callout(
                    document_id=document_id,
                    parent_id=parent_id,
                    index=target_index+1,
                    content=content
                )
                await asyncio.sleep(1)  # 添加等待
            
            # 2. 最后添加日期标题
            date_heading = BlockFactory.create_block(
                block_type=BlockType.HEADING2,
                text_runs=[{
                    "content": date_str,
                    "text_element_style": {
                        "bold": False,
                        "inline_code": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False
                    }
                }],
                style={
                    "align": 1,
                    "folded": False
                }
            )
            
            heading_response = await self.docx_handler.create_block(
                document_id=document_id,
                block_id=parent_id,
                children=[date_heading],
                index=target_index+1
            )
            
            if not heading_response or heading_response.get('code') != 0:
                raise ValueError(f"创建日期标题失败: {heading_response.get('msg')}")
            
            return True
            
        except Exception as e:
            print(f"添加内容块失败: {str(e)}")
            return False


async def context_to_json(context):
    # 使用正则表达式匹配 **标题** 和内容
    pattern = r'\*\*(.*?)\*\*(.*?)(?=\*\*|$)'
    matches = re.findall(pattern, context, re.DOTALL)
    
    # 构建JSON数组
    result = []
    for match in matches:
        title = match[0].strip()
        content = match[1].strip()
        
        # 提取每个段落的要点（以 - 开头的行），并过滤掉包含 "原文链接" 的行
        bullets = [bullet for bullet in re.findall(r'- (.*?)(?=\n|$)', content) if not bullet.startswith("原文链接")]
        
        # 提取链接（以 "原文链接：" 开头的URL）
        link_match = re.search(r'原文链接：(https?://[^\s]+)', content)
        link = link_match.group(1) if link_match else None
        
        # 构建字典
        result.append({
            "title": title,
            "bullets": bullets,
            "link": link
        })
    
    # 返回JSON格式的字符串
    return json.dumps(result, ensure_ascii=False, indent=4)


router = APIRouter()

@router.post("/update_feishu_xiaobao", dependencies=[Depends(verify_api_key)])
async def update_feishu_xiaobao_post(payload: dict = Body(...)):
    FEISHU_APP_ID = payload.get("feishu_app_id")
    FEISHU_APP_SECRET = payload.get("feishu_app_secret")
    DOC_ID = payload.get("doc_id")
    TARGET_BLOCK_ID = payload.get("target_block_id")
    DATE_STR = payload.get("date_str")
    CONTENT_DATA = await context_to_json(payload.get("content_data"))

    # 初始化
    content_manager = FeishuDocxContentManager(FEISHU_APP_ID, FEISHU_APP_SECRET)

    # 添加内容块
    result = await content_manager.add_content_blocks(DOC_ID, TARGET_BLOCK_ID, DATE_STR, CONTENT_DATA)
    if result:
        return {"status": "success","result":result}
    else:
        return {"status": "failed","result":result}