import os
import time
import requests
import logging
import sys

from mcp.server import FastMCP
from mcp.types import TextContent

from .write_xiaohongshu import XiaohongshuPoster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('xhs_server.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('xhs_server')

mcp = FastMCP("xhs")
phone = os.getenv("phone", "")
path = os.getenv("json_path", "/Users/bruce/")

logger.info(f"XHS_COOKIES_FILE: {os.getenv('XHS_COOKIES_FILE')}")
logger.info(f"json_path: {path}")

def login():
    try:
        logger.info("Starting login process...")
        poster = XiaohongshuPoster(path)
        poster.login(phone)
        time.sleep(1)
        poster.close()
        logger.info("Login completed successfully")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise

@mcp.tool()
def create_note(title: str, content: str, images: list = None):
    """Creates a note on Xiaohongshu.
    
    Args:
        title: The title of the note
        content: The content of the note
        images: A list of image paths or URLs
        
    Returns:
        A message indicating success or failure
    """
    print(f"开始创建笔记: {title}")
    print(f"笔记内容: {content[:50]}...") 
    print(f"图片数量: {len(images) if images else 0}")
    
    local_images = []
    
    if images:
        print("处理图片...")
        for i, img in enumerate(images):
            if img.startswith(('http://', 'https://')):
                print(f"下载远程图片 {i+1}/{len(images)}: {img}")
                try:
                    local_path = download_image(img)
                    if local_path:
                        local_images.append(local_path)
                        print(f"图片下载成功: {local_path}")
                    else:
                        print(f"图片下载失败: {img}")
                except Exception as e:
                    print(f"图片下载异常: {str(e)}")
            else:
                # 可能是本地路径
                if os.path.exists(img):
                    local_images.append(img)
                    print(f"使用本地图片: {img}")
                else:
                    print(f"本地图片不存在: {img}")
    
    try:
        print(f"准备发布, 图片列表: {local_images}")
        poster = XiaohongshuPoster()
        result = poster.post_article(title, content, local_images)
        print(f"发布结果: {result if result else '成功'}")
        return {"success": True, "message": f"笔记已发布: {title}"}
    except Exception as e:
        error_msg = f"发布笔记失败: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return {"success": False, "message": error_msg}


@mcp.tool()
def create_video_note(title: str, content: str, videos: list) -> list[TextContent]:
    """Create a note (post) to xiaohongshu (rednote) with title, description, and videos

    Args:
        title: the title of the note (post), which should not exceed 20 words
        content: the description of the note (post).
        videos: the list of video paths or URLs to be included in the note (post)
    """
    poster = XiaohongshuPoster(path)
    poster.login(phone)
    res = ""
    try:
        # 下载网络图片到本地缓存地址
        local_images = []
        for video in videos:
            if video.startswith("http"):
                local_path = download_image(video)
                local_images.append(local_path)
            else:
                local_images.append(video)

        poster.post_video_article(title, content, local_images)
        poster.close()
        res = "success"
    except Exception as e:
        res = "error:" + str(e)

    return [TextContent(type="text", text=res)]


def download_image(url):
    local_filename = url.split('/')[-1]
    local_path = os.path.join("/tmp", local_filename)  # 假设缓存地址为/tmp
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_path

def main():
    try:
        logger.info("Starting XHS MCP server...")
        mcp.run()
    except Exception as e:
        logger.error(f"Error running XHS MCP server: {e}")
        raise

if __name__ == "__main__":
    main()