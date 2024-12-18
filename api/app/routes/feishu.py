from fastapi import APIRouter, HTTPException, Query, Depends, Body, BackgroundTasks
from pydantic import BaseModel
import json
import re
from ..dependencies import verify_api_key
from typing import Dict, Optional, List, Union, Any
import random
import asyncio
from ..handlers.feishu_docx_api_handler_async import FeishuDocxAPIHandler, BlockFactory, BlockType
from ..utils.feishu_emoji import EMOJI_DICT

class UpdateFeishuPayload(BaseModel):
    feishu_app_id: str
    feishu_app_secret: str 
    doc_id: str
    target_block_id: str
    date_str: str
    content_data: str

class FeishuDocxContentManager:
    """飞书文档内容管理器，用于管理文档中的内容块"""
    
    # 可用的背景颜色和边框颜色
    AVAILABLE_COLORS = list(range(1, 7))  # 1-7的颜色值
    
    # 可用的emoji列表
    AVAILABLE_EMOJIS = list(EMOJI_DICT.values())
    
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
                        content: Dict[str, Any]) -> Optional[int]:
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
            children_ids, descendants = BlockFactory.create_content_blocks(content)

            # 然后可以将这些结果传给 create_descendant_blocks 方法
            child_response = await self.docx_handler.create_descendant_blocks(
                document_id=document_id,
                block_id=callout_block_id,
                children_ids=children_ids,
                descendants=descendants
            )
            
            if not child_response or child_response.get('code') != 0:
                raise ValueError(f"创建子块失败: {child_response.get('msg')}")
                       
            return index + 1
            
        except Exception as e:
            print(f"添加callout块失败: {str(e)}")
            return None

    async def add_content_blocks(self, 
                        document_id: str, 
                        target_block_id: str, 
                        date_str: str, 
                        content_data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        try:
            # 初始化 FeishuDocxAPIHandler
            await self.initialize()

            # 获取父块信息
            parent_id, target_index = await self._get_parent_info(document_id, target_block_id)
            
            # 确保content_data是列表
            contents = content_data if isinstance(content_data, list) else [content_data]

            #设置更新的content数量限制
            content_limit = 3
        
            # 1. 添加所有callout块
            for i, content in enumerate(contents):
                if i >= content_limit:
                    break
                next_index = await self._add_single_callout(
                    document_id=document_id,
                    parent_id=parent_id,
                    index=target_index+1,
                    content=content
                )
                await asyncio.sleep(0.5)  # 添加等待
                
            
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


def context_to_json(context):
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
    
    # 返回JSON
    return result


router = APIRouter()

async def background_task(
    content_manager: FeishuDocxContentManager,
    DOC_ID: str,
    TARGET_BLOCK_ID: str,
    DATE_STR: str,
    CONTENT_DATA: List[Dict[str, Any]]
):
    await content_manager.add_content_blocks(DOC_ID, TARGET_BLOCK_ID, DATE_STR, CONTENT_DATA)

@router.post("/update_feishu_xiaobao", dependencies=[Depends(verify_api_key)])
async def update_feishu_xiaobao_post(
    payload: UpdateFeishuPayload,
    background_tasks: BackgroundTasks
):
    CONTENT_DATA = context_to_json(payload.content_data)
    
    # 初始化
    content_manager = FeishuDocxContentManager(payload.feishu_app_id, payload.feishu_app_secret)
    
    # 将任务添加到后台
    background_tasks.add_task(
        background_task, 
        content_manager, 
        payload.doc_id, 
        payload.target_block_id, 
        payload.date_str, 
        CONTENT_DATA
    )
    
    return {"status": "processing", "message": "任务已提交，正在后台处理"}


class FindBlockPayload(BaseModel):
    feishu_app_id: str
    feishu_app_secret: str
    doc_id: str
    target_content: str = "每日推荐"
    target_block_type: int = 3  # 默认为h1块类型

def find_block_by_content_and_type(data: List[Dict], target_content: str, target_block_type: int, block_map: Dict) -> Optional[str]:
    """
    递归查找包含特定文字内容和block_type的块，并返回该块的ID
    
    Args:
        data: JSON数据（字典或列表）
        target_content: 要查找的文字内容
        target_block_type: 要查找的block_type
        block_map: 用于查找block_id对应的块的字典
        
    Returns:
        Optional[str]: 符合条件的块ID，若未找到则返回None
    """
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if item.get('block_type') == target_block_type:
                    if 'heading1' in item:  # 对于heading1类型
                        elements = item['heading1'].get('elements', [])
                        for element in elements:
                            if 'text_run' in element and target_content in element['text_run'].get('content', ''):
                                return item.get('block_id')
                    elif 'text' in item:  # 对于普通文本类型
                        elements = item['text'].get('elements', [])
                        for element in elements:
                            if 'text_run' in element and target_content in element['text_run'].get('content', ''):
                                return item.get('block_id')

                if 'children' in item:
                    children_blocks = [block_map.get(child_id) for child_id in item['children']]
                    children_blocks = [block for block in children_blocks if block is not None]
                    result = find_block_by_content_and_type(children_blocks, target_content, target_block_type, block_map)
                    if result:
                        return result
    return None

def build_block_map(blocks: List[Dict]) -> Dict:
    """构建block_id到block的映射字典"""
    return {block['block_id']: block for block in blocks 
            if isinstance(block, dict) and 'block_id' in block}

@router.post("/find_block", dependencies=[Depends(verify_api_key)])
async def find_block_post(payload: FindBlockPayload):
    try:
        # 初始化 handler
        docx_handler = FeishuDocxAPIHandler(payload.feishu_app_id, payload.feishu_app_secret)
        await docx_handler.initialize()
        
        # 获取文档块
        document_blocks = await docx_handler.get_document_blocks(payload.doc_id)
        if not document_blocks or 'data' not in document_blocks:
            raise HTTPException(status_code=400, detail="Failed to get document blocks")
            
        blocks = document_blocks.get('data', {}).get('items', [])
        
        # 构建block_map
        block_map = build_block_map(blocks)
        
        # 查找特定内容和类型的块
        block_id = find_block_by_content_and_type(
            blocks, 
            payload.target_content, 
            payload.target_block_type, 
            block_map
        )
        
        if block_id:
            return {
                "status": "success",
                "block_id": block_id,
                "block_content": block_map.get(block_id)
            }
        else:
            return {
                "status": "not_found",
                "message": "No matching block found"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))