import re
import json
import urllib.request
import urllib.parse
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from agents.gemini_client import global_gemini_client

logger = logging.getLogger(__name__)

class YouTubeSummaryOutput(BaseModel):
    title: str = Field(description="Tiêu đề tin tức vĩ mô ngắn gọn, súc tích (dưới 15 từ) bằng Tiếng Việt.")
    summary: str = Field(description="Nội dung phân tích & tóm tắt vĩ mô chuyên sâu bằng Tiếng Việt, chia thành các bullet points rõ ràng (KHÔNG chèn timestamp hay mốc thời gian), nêu rõ số liệu, luận điểm chính và tác động thị trường.")
    importance: int = Field(default=3, ge=1, le=5, description="Mức độ quan trọng của tin tức đối với thị trường tài chính từ 1 đến 5 sao.")
    key_points: List[str] = Field(default_factory=list, description="3-5 điểm nhấn cốt lõi nhất.")


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract YouTube 11-character video ID from multiple URL formats."""
    if not url:
        return None
    url = url.strip()
    
    # Check if raw 11-char ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
        
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/live\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
            
    # Try query param v
    try:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if 'v' in params and len(params['v']) > 0:
            return params['v'][0]
    except Exception:
        pass
        
    return None


def fetch_youtube_metadata(video_id: str, original_url: str) -> Dict[str, Any]:
    """Fetch video metadata using YouTube oEmbed API."""
    metadata = {
        "video_id": video_id,
        "video_title": f"YouTube Video ({video_id})",
        "video_author": "YouTube",
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    }
    try:
        target_url = f"https://www.youtube.com/watch?v={video_id}"
        oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(target_url)}&format=json"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                metadata["video_title"] = data.get("title", metadata["video_title"])
                metadata["video_author"] = data.get("author_name", metadata["video_author"])
                if data.get("thumbnail_url"):
                    metadata["thumbnail_url"] = data.get("thumbnail_url")
    except Exception as e:
        logger.warning(f"Could not fetch oEmbed metadata for {video_id}: {e}")
        
    return metadata


def format_timestamp(seconds: float) -> str:
    """Format seconds into [MM:SS] or [HH:MM:SS]."""
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"
    return f"[{minutes:02d}:{secs:02d}]"


def get_video_transcript(video_id: str) -> str:
    """Retrieve full video transcript with formatted timestamps, supporting all youtube_transcript_api versions."""
    try:
        transcript_list = None
        # 1. Try listing transcripts using available API method
        try:
            if hasattr(YouTubeTranscriptApi, 'list_transcripts'):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except Exception:
            pass
            
        if transcript_list is None:
            try:
                api = YouTubeTranscriptApi()
                if hasattr(api, 'list'):
                    transcript_list = api.list(video_id)
                elif hasattr(api, 'list_transcripts'):
                    transcript_list = api.list_transcripts(video_id)
            except Exception:
                pass
        
        transcript = None
        if transcript_list:
            # Try Vietnamese
            for t in transcript_list:
                lang = getattr(t, 'language_code', '')
                if lang.startswith('vi'):
                    transcript = t
                    break
            # Try English
            if not transcript:
                for t in transcript_list:
                    lang = getattr(t, 'language_code', '')
                    if lang.startswith('en'):
                        transcript = t
                        break
            # Fallback to any transcript available
            if not transcript:
                for t in transcript_list:
                    transcript = t
                    break

        data = None
        if transcript:
            data = transcript.fetch()
        else:
            # Fallback to direct fetch
            api = YouTubeTranscriptApi()
            if hasattr(api, 'fetch'):
                try:
                    data = api.fetch(video_id, languages=['vi', 'en'])
                except Exception:
                    data = api.fetch(video_id)
            elif hasattr(YouTubeTranscriptApi, 'get_transcript'):
                data = YouTubeTranscriptApi.get_transcript(video_id, languages=['vi', 'en'])
                
        if not data:
            raise NoTranscriptFound(video_id, ['vi', 'en'], None)
        
        # Format transcript segments with interval timestamps
        formatted_lines = []
        last_time = -1
        chunk_texts = []
        
        for item in data:
            start = getattr(item, 'start', None) if not isinstance(item, dict) else item.get('start')
            text = getattr(item, 'text', None) if not isinstance(item, dict) else item.get('text')
            if start is None:
                start = 0.0
            if not text:
                continue
            text = str(text).strip().replace('\n', ' ')
            
            if last_time < 0 or (start - last_time) >= 25 or len(' '.join(chunk_texts)) > 250:
                if chunk_texts:
                    formatted_lines.append(f"{format_timestamp(last_time)} {' '.join(chunk_texts)}")
                    chunk_texts = []
                last_time = start
                
            chunk_texts.append(text)
            
        if chunk_texts:
            formatted_lines.append(f"{format_timestamp(last_time)} {' '.join(chunk_texts)}")
            
        return "\n".join(formatted_lines)
        
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        logger.error(f"Transcript unavailable for {video_id}: {e}")
        raise RuntimeError("Video YouTube này không có phụ đề (Captions/Transcript) hoặc đã bị tắt phụ đề.")
    except Exception as e:
        logger.error(f"Error fetching transcript for {video_id}: {e}")
        raise RuntimeError(f"Không thể lấy transcript của video: {str(e)}")


def summarize_youtube_video(url: str) -> Dict[str, Any]:
    """Complete pipeline: Validate URL -> Metadata -> Transcript -> AI Macro Analysis."""
    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise ValueError("URL YouTube không hợp lệ. Vui lòng nhập link video YouTube đúng định dạng.")
        
    metadata = fetch_youtube_metadata(video_id, url)
    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # 1. Fetch transcript with timestamps
    transcript_text = get_video_transcript(video_id)
    if not transcript_text or len(transcript_text.strip()) < 50:
        raise RuntimeError("Transcript video quá ngắn hoặc không có nội dung để phân tích.")
        
    # 2. Limit transcript if excessively long (keep max ~30,000 characters)
    if len(transcript_text) > 30000:
        transcript_text = transcript_text[:30000] + "\n...[Nội dung video tiếp tục nhưng đã được cắt giảm để tối ưu token]..."
        
    # 3. Build Prompt for LLM
    prompt = f"""Giả sử bạn là một Nhà phân tích Tài chính và Kinh tế Vĩ mô chuyên nghiệp (Senior Financial & Macroeconomic Analyst).
Hãy phân tích toàn diện nội dung sau từ video YouTube và trả về một bản tóm tắt phân tích chuyên sâu, sắc bén:

- Tiêu đề video: {metadata['video_title']}
- Kênh / Tác giả: {metadata['video_author']}
- Nguồn video: {canonical_url}

=== NỘI DUNG PHỤ ĐỀ VIDEO (TRANSCRIPT) ===
{transcript_text}
=== HẾT PHỤ ĐỀ ===

YÊU CẦU PHÂN TÍCH VÀ ĐỊNH DẠNG ĐẦU RA:
1. TIÊU ĐỀ (title):
   - Đặt một tiêu đề mang tính phân tích chuyên nghiệp, súc tích (dưới 15 từ Tiếng Việt), phản ánh đúng thông điệp hoặc bước ngoặt thị trường cốt lõi.

2. BẢN TÓM TẮT PHÂN TÍCH (summary):
   - Trình bày dạng các Bullet points rõ ràng, lập luận chặt chẽ, mạch lạc bằng Tiếng Việt.
   - Bóc tách các sự kiện, phát biểu chính sách (FED, Ngân hàng Nhà nước SBV, Lạm phát, Lãi suất, Tỷ giá USD/VND, DXY, Trái phiếu, Giá Vàng, Năng lượng, v.v.).
   - Đưa ra góc nhìn phân tích tác động cụ thể tới thị trường tài chính và các lớp tài sản: Chứng khoán (VN-Index, Chứng khoán Mỹ), Vàng, Tiền tệ/Forex, Crypto, Bất động sản.
   - Nhận định rủi ro và hàm ý cho nhà đầu tư.
   - TUYỆT ĐỐI KHÔNG chèn mốc thời gian, timestamps hay các thẻ [MM:SS] vào nội dung tóm tắt.

3. MỨC ĐỘ QUAN TRỌNG (importance):
   - Đánh giá từ 1 đến 5 sao theo mức độ tác động tới thị trường (1: Tin thường nhật/tham khảo $\rightarrow$ 5: Sự kiện vĩ mô mang tính bước ngoặt).

4. ĐIỂM NHẤN CỐT LÕI (key_points):
   - 3-5 gạch đầu dòng ngắn gọn những kết luận quan trọng nhất.
"""

    logger.info(f"Generating AI Macro Summary for YouTube video: {video_id} ({metadata['video_title']})")
    ai_result = global_gemini_client.generate_structured_data(prompt, YouTubeSummaryOutput)
    
    if isinstance(ai_result, dict):
        title = ai_result.get("title") or metadata["video_title"]
        summary = ai_result.get("summary") or ""
        importance = ai_result.get("importance", 3)
        key_points = ai_result.get("key_points", [])
    else:
        title = getattr(ai_result, "title", None) or metadata["video_title"]
        summary = getattr(ai_result, "summary", "")
        importance = getattr(ai_result, "importance", 3)
        key_points = getattr(ai_result, "key_points", [])

    try:
        importance = int(importance)
    except Exception:
        importance = 3
        
    return {
        "status": "success",
        "video_id": video_id,
        "video_title": metadata["video_title"],
        "video_author": metadata["video_author"],
        "thumbnail_url": metadata["thumbnail_url"],
        "source_url": canonical_url,
        "title": title,
        "summary": summary,
        "importance": importance,
        "key_points": key_points
    }
