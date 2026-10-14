"""Local, conservative storyboard rules. No model or network calls."""
import re
from io import BytesIO

import pandas as pd

STYLES = {
    "建筑纪录片": "建筑纪录片风格，客观记录，保持建筑形态与比例真实",
    "电影写实": "电影写实风格，自然质感，保持场景与主体一致",
    "国风古建筑": "国风古建筑影像风格，克制表达，保持原有建筑形态",
    "动画": "动画影像风格，造型统一，保持主体一致",
    "通用": "清晰自然的影像风格，保持主体与场景一致",
}
COLUMNS = ["镜头编号", "时长", "画面内容", "主体动作", "运镜方式", "光线氛围", "完整中文视频提示词", "负面约束"]
NEGATIVE = "不添加文案未提及的人物、物体、建筑构件或历史细节；不改变主体结构；避免画面变形、闪烁、额外文字与水印"
EXAMPLE = "山西五台山的佛光寺，是本片关注的建筑。\n镜头保持稳定，观察佛光寺东大殿的整体外观。\n通过建筑影像，感受这座古建筑的历史气息。"


def split_scenes(text: str) -> list[str]:
    """Split only at paragraph / complete sentence boundaries; keep punctuation."""
    scenes = []
    for paragraph in re.split(r"[\r\n]+", text.strip()):
        scenes.extend(s.strip() for s in re.findall(r'.+?(?:[。！？!?]+[”’\"\']*|\.(?=\s|$)|$)', paragraph) if s.strip())
    return scenes


def generate(text: str, style: str, duration: int) -> pd.DataFrame:
    if style not in STYLES or duration not in (5, 7, 10):
        raise ValueError("请选择支持的风格和时长")
    rows = []
    for number, scene in enumerate(split_scenes(text), 1):
        action = "保持文案所述主体状态；未明确的动作不额外添加"
        camera = "固定机位，稳定观察"
        light = "自然、均匀的光线；未指定时段与天气"
        prompt = f"{STYLES[style]}。画面依据：{scene} 主体动作：{action}。运镜：{camera}。光线氛围：{light}。建议时长：{duration}秒。仅表现可核实、文案明确提供的内容。"
        rows.append([number, duration, scene, action, camera, light, prompt, NEGATIVE])
    return pd.DataFrame(rows, columns=COLUMNS)


def export_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")


def export_excel(frame: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    # Treat user text as literal text, including strings starting with '='.
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="分镜")
        sheet = writer.sheets["分镜"]
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    cell.data_type = "s"
    return buffer.getvalue()


def copy_text(frame: pd.DataFrame) -> str:
    if "镜头号" in frame.columns:
        return "\n\n".join(f"镜头 {int(row['镜头号']) if str(row['镜头号']).isdigit() else row['镜头号']}（{row['镜头号']}）｜{row['时长（秒）']}秒\n{row['备注']}" for _, row in frame.iterrows())
    return "\n\n".join(f"镜头 {row['镜头编号']}｜{row['时长']}秒\n{row['完整中文视频提示词']}\n负面约束：{row['负面约束']}" for _, row in frame.iterrows())
