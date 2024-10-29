from fastapi import APIRouter, HTTPException, Query, Depends

import json
import os

from ..dependencies import verify_api_key

from ..utils.web_scraper import WebScraper

router = APIRouter()

@router.get("/fetch_web_content", dependencies=[Depends(verify_api_key)])
def fetch_web_content(url: str = Query(...)):
    a1 = os.getenv('XHS_A1')
    web_session = os.getenv('XHS_WEB_SESSION')

    custom_url_rules_json = json.dumps([
        {
            "name": "xiaohongshu",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cookie': f'xsecappid=xhs-pc-web; a1={a1}; webId=3e16d3174d2fb0af5596ef71c539b7bb; gid=yYYjjd2SiqyDyYYjjd2SS0WMdqiDdY4Mqi3yu1ukKIKh3q28MWJIxY888y2JWy88i8jY2D2J; gid.sign=miPRUSOnqLWPB8SKtgEt9jRvDq8=; abRequestId=3e16d3174d2fb0af5596ef71c539b7bb; websectiga=a9bdcaed0af874f3a1431e94fbea410e8f738542fbb02df1e8e30c29ef3d91ac; acw_tc=7dd30b3c137d956245d2354831701bc7c864a30b2b950fe5953ed135792305d8; webBuild=4.16.0; sec_poison_id=1976a19a-1c8f-4290-8f54-2729230d1b55; web_session={web_session}; unread={{"ub":"6645c49a000000001e031ca3","ue":"662a033a000000000401bc1e","uc":29}}'
            }
        },
        {
            "name": "wechat",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/18A373 MicroMessenger/8.0.1(0x18000129) NetType/WIFI Language/zh_CN',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
        }
    ])
    
    scraper = WebScraper(url, custom_url_rules_json)   
    return scraper.scrape()