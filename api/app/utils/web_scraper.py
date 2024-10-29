#version: 1.0
import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import html

class WebScraper:
    default_url_rules = [
        {
            "pattern": r"https://www.xiaohongshu.com/explore/\w+",
            "parser": "html.parser",
            "name": "xiaohongshu",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
            },
            "extractor": "extract_xiaohongshu_content"
        },
        {
            "pattern": r"http[s]?://mp\.weixin\.qq\.com/s(?:\?[\w=&%]+|/\w+)",
            "parser": "html.parser",
            "name": "wechat",
            "headers": {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/18A373 MicroMessenger/8.0.1(0x18000129) NetType/WIFI Language/zh_CN"
            },
            "extractor": "extract_wechat_content"
        },
        {
            "pattern": r".*",
            "parser": "html.parser",
            "name": "general",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
            },
            "extractor": "extract_general_content"
        }
    ]

    def __init__(self, url, url_rules_json=None):
        self.url = url
        self.content = None
        self.soup = None
        self.url_rules = self.default_url_rules.copy()

        if url_rules_json:
            custom_url_rules = json.loads(url_rules_json)
            self.update_headers(custom_url_rules)

    def update_headers(self, custom_url_rules):
        for custom_rule in custom_url_rules:
            name = custom_rule.get("name")
            headers = custom_rule.get("headers", {})

            # 找到匹配的默认规则并更新 headers
            for rule in self.url_rules:
                if rule["name"] == name:
                    rule["headers"].update(headers)

    def fetch_content(self):
        rule = self.detect_url_type()
        headers = rule.get("headers", {})


        def clean_url(url):
            # 先将 HTML 实体解码为普通字符
            url = html.unescape(url)
            
            # 解析URL
            parsed_url = urlparse(url)
            
            # 解析查询参数
            query_params = parse_qs(parsed_url.query)
            
            # 删除不需要的参数
            query_params.pop('chksm', None)
            query_params.pop('scene', None)
            
            # 将查询参数重新编码为字符串
            cleaned_query = urlencode(query_params, doseq=True)
            
            # 构造新的URL
            cleaned_url = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                cleaned_query,
                parsed_url.fragment
            ))
            
            return cleaned_url

        if rule["name"] == "wechat":
            self.url = clean_url(self.url)
            print(f"Cleaned URL: {self.url}")

        try:
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()  # 检查请求是否成功
            self.content = response.text
        except requests.RequestException as e:
            print(f"Error fetching {self.url}: {e}")
            self.content = None

    def detect_url_type(self):
        # 遍历URL规则进行匹配
        for rule in self.url_rules:
            if re.match(rule["pattern"], self.url):
                return rule
        return None

    def parse_content(self):
        if self.content is None:
            print("No content to parse")
            return None

        rule = self.detect_url_type()
        if rule:
            parser = rule["parser"]
            name = rule["name"]
            print(f"Detected {name} content page, using parser: {parser}")
            self.soup = BeautifulSoup(self.content, parser)
        else:
            print("No matching rule found, using default parser: html.parser")
            self.soup = BeautifulSoup(self.content, "html.parser")

    def extract_content(self):
        rule = self.detect_url_type()
        if not rule or not self.soup:
            return {}

        extractor_method_name = rule.get("extractor")
        extractor_method = getattr(self, extractor_method_name, None)

        if extractor_method:
            return extractor_method()
        else:
            print(f"No extractor method found for {rule['name']}")
            return {}

    def extract_xiaohongshu_content(self):
        # 针对小红书的内容提取逻辑
        soup=self.soup
        # 提取标题
        title_meta = soup.find('meta', {'name': 'og:title'})
        title = title_meta['content'] if title_meta else '未找到标题'
        title = title[:-6]

        # 提取正文
        desc_meta = soup.find('meta', {'name': 'description'})
        desc_text = desc_meta['content'] if desc_meta else '未找到正文'
        content=desc_text

        # 提取图片链接
        image_urls = []
        for meta in soup.find_all('meta', {'name': 'og:image'}):
            image_urls.append(meta['content'])

        # 提取评论数
        note_comment_meta= soup.find('meta', {'name': 'og:xhs:note_comment'})
        note_comment = note_comment_meta['content'] if note_comment_meta else '未找到评论数'


        # 提取点赞数
        note_like_meta= soup.find('meta', {'name': 'og:xhs:note_like'})
        note_like = note_like_meta['content'] if note_like_meta else '未找到点赞数'

        # 提取收藏数
        note_collect_meta= soup.find('meta', {'name': 'og:xhs:note_collect'})
        note_collect = note_collect_meta['content'] if note_collect_meta else '未找到收藏数'
        # 查找所有的script标签
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'window.__INITIAL_STATE__=' in script.string:
                #print(script.string)
                #将字符串前面的部分去掉
                data = script.string.replace('window.__INITIAL_STATE__=', '')
                # Regular expressions to match user information
                user_id_pattern = re.compile(r'"userId"\s*:\s*"([^"]+)"')
                nickname_pattern = re.compile(r'"nickname"\s*:\s*"([^"]+)"')
                # Search for the patterns in the data
                user_id_match = user_id_pattern.search(data)
                nickname_match = nickname_pattern.search(data)
                #输出匹配到的用户信息
                user_id = user_id_match.group(1) if user_id_match else '未找到用户ID'
                nickname= nickname_match.group(1) if nickname_match else '未找到用户昵称'
                user_url = f"https://www.xiaohongshu.com/user/profile/{user_id}"

        return {
            "title": title,
            "description": desc_text,
            "content": content,
            "image_urls": image_urls,
            "note_comment": note_comment,
            "note_like": note_like,
            "note_collect": note_collect,
            "user_id": user_id,
            "nickname": nickname,
            "user_url": user_url        
        }

    def extract_wechat_content(self):
        # 针对微信公众号的内容提取逻辑
        soup=self.soup
        # 提取标题
        title = soup.find('h1', {'class': 'rich_media_title'}).get_text(strip=True)

        # 提取概述
        desc_meta = soup.find('meta', {'name': 'description'})
        desc_text = desc_meta['content'] if desc_meta else '未找到概述'

        # 提取头图链接
        cover_meta = soup.find('meta', {'property': 'og:image'})
        cover_url = cover_meta['content'] if cover_meta else ''

        # 提取作者
        author_meta = soup.find('meta', {'name': 'author'})
        author_text = desc_meta['content'] if author_meta else '未找到作者'       

        # 提取正文
        content_div = soup.find('div', {'class': 'rich_media_content'})

        # 定义一个函数来递归处理标签
        def extract_text_with_newlines(element):
            text = ''
            for child in element.children:
                if child.name == 'img':
                    # 处理 img 标签，提取 src 和 alt 属性
                    img_src = child.get('data-src', '')
                    img_alt = child.get('alt', '')
                    # 将 img 标签转换为 Markdown 格式的图片标记
                    text += f'\n![{img_alt}]({img_src})\n'
                elif child.name == 'h1':
                    text += f'# {extract_text_with_newlines(child)}\n\n'
                elif child.name == 'h2':
                    text += f'## {extract_text_with_newlines(child)}\n\n'
                elif child.name == 'h3':
                    text += f'### {extract_text_with_newlines(child)}\n\n'
                elif child.name == 'h4':
                    text += f'#### {extract_text_with_newlines(child)}\n\n'
                elif child.name == 'h5':
                    text += f'##### {extract_text_with_newlines(child)}\n\n'
                elif child.name == 'h6':
                    text += f'###### {extract_text_with_newlines(child)}\n\n'
                elif child.name == 'p':
                    # 段落，添加换行符
                    text += f'{extract_text_with_newlines(child)}\n\n'
                elif child.name == 'strong' or child.name == 'b':
                    # 加粗文本
                    text += f'**{extract_text_with_newlines(child)}**'
                elif child.name == 'em' or child.name == 'i':
                    # 斜体文本
                    text += f'*{extract_text_with_newlines(child)}*'
                elif child.name == 'ul':
                    # 无序列表
                    text += f'{extract_text_with_newlines(child)}\n'
                elif child.name == 'ol':
                    # 有序列表
                    text += f'{extract_text_with_newlines(child)}\n'
                elif child.name == 'li':
                    # 列表项，判断是有序还是无序列表
                    if child.parent.name == 'ul':
                        text += f'- {extract_text_with_newlines(child)}\n'
                    elif child.parent.name == 'ol':
                        text += f'1. {extract_text_with_newlines(child)}\n'
                elif child.name == 'a':
                    # 超链接
                    href = child.get('href', '#')
                    link_text = extract_text_with_newlines(child)
                    text += f'[{link_text}]({href})'
                elif child.name:  # 如果是其他标签，继续递归处理其子节点
                    text += extract_text_with_newlines(child)
                else:  # 如果是NavigableString（文本节点），直接添加其内容
                    text += child.string or ''
            
            return text

        content = extract_text_with_newlines(content_div).strip()
        content = re.sub(r'\n\n+', '\n\n', content)  # 将多个连续的换行符替换为两个


        return {
            "title": title, 
            "cover_url": cover_url,
            "description": desc_text,
            "author": author_text,
            "content": content
       }

    def extract_general_content(self):
        # 针对一般网页的内容提取逻辑
        title = self.soup.title.string if self.soup.title else ""
        content = self.soup.get_text()
        return {"title": title, "content": content}

    def scrape(self):
        self.fetch_content()
        if self.content:
            self.parse_content()
            extracted_data = self.extract_content()
            return {"error": "0","data": extracted_data}
        else:
            return {"error": "1","detail": "Failed to fetch content"}