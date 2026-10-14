"""Event splitting and rendering boundary for future generation backends."""
import re
from dataclasses import dataclass
from typing import Protocol

import pandas as pd

from generator import NEGATIVE, STYLES, split_scenes

COLUMNS = ["镜头号", "地点", "画面内容", "景别", "机位", "运镜", "时长（秒）", "对话", "备注", "配图"]
ACTS = re.compile(r"第[一二三四五六七八九十百零\d]+幕")
SUBJECTS = re.compile(r"佛光寺(?:东大殿|大殿)?|应县木塔|永宁门|少女|少年|男子|女子|老人|小孩|人物")
CAMERAS = ("固定", "推进", "拉远", "横移", "摇镜", "航拍")


@dataclass
class Event:
    act: str
    content: str
    subject: str = "文案所述主体"
    location: str = "未明确"
    texture: str = ""
    dialogue: str = "无"
    light: str = "未明确，建议均匀中性光，不指定时段天气"
    sound: str = "未指定，不额外添加"


class StoryboardBackend(Protocol):
    def split(self, text: str) -> list[Event]: ...


def split_acts(text: str) -> list[tuple[str, str]]:
    parts = re.split(f"({ACTS.pattern})", text)
    result = [("未标幕次", parts[0])] if parts[0].strip() else []
    result.extend((parts[i], parts[i + 1].lstrip("是：: \n")) for i in range(1, len(parts), 2))
    return result


class RuleBackend:
    """Conservative patterns; unknown clauses retain supplied information."""

    def split(self, text: str) -> list[Event]:
        events = []
        for act, body in split_acts(text):
            act_start = len(events)
            texture_match = re.search(r"(?:由|以)([^，。；]+)(?:组成|构成)", body)
            texture = texture_match.group(1) if texture_match else ""
            location = "未明确"
            previous_subject = "文案所述主体"
            # Protect dialogue punctuation so spoken actions are not visual events.
            quotes = []
            def protect(match):
                quotes.append(match.group(0))
                return f"§{len(quotes) - 1}§"
            protected = re.sub(r"[“\"]([^”\"]*)[”\"]", protect, body)
            for sentence in split_scenes(protected):
                clauses = re.split(
                    r"[；;]|[，,](?=这些画面|所有|少女|少年|男子|女子|老人|小孩|佛光寺|应县木塔|永宁门|镜头(?:推进|拉远|横移|摇镜)|画面(?:切换|变为))|(?:然后|随后|接着|最后)|(?=切换到|转场到)",
                    sentence,
                )
                for clause in clauses:
                    clause = clause.strip(" 。！？!?")
                    if not clause:
                        continue
                    if re.search(r"这些画面.*(?:组成|构成)", clause):
                        continue
                    dialogue = "无"
                    for index, quote in enumerate(quotes):
                        if f"§{index}§" in clause:
                            dialogue = quote.strip('“”"')
                            clause = clause.replace(f"§{index}§", "说话")
                    names = SUBJECTS.findall(clause)
                    # Enumerated subjects sharing appearance state become separate events.
                    if len(names) > 1 and re.search(r"依次|分别", clause):
                        person = next((n for n in names if n in ("少女", "少年", "男子", "女子", "老人", "小孩", "人物")), None)
                        if person:
                            events.append(Event(act, f"{person}以背影入画，观看前方画面" if "背影" in clause else f"{person}观看前方画面", person, location, dialogue=dialogue))
                        objects = [n for n in names if n != person]
                        for name in objects:
                            facade = "立面" if "立面" in clause else "形象"
                            events.append(Event(act, f"{name}的{facade}出现", name, location, texture))
                            if "消失" in clause:
                                events.append(Event(act, f"{name}的{facade}消失", name, location, texture))
                        previous_subject = "前述画面"
                        continue
                    # Explicit places are accepted; a viewed projection isn't a location.
                    place = re.search(r"(?:地点[:：]|位于|来到)([^，。；]+)", clause)
                    if place:
                        location = place.group(1)
                    subject = names[0] if names else previous_subject
                    # Split successive actions only at meaningful connectors.
                    pieces = re.split(r"(?:并且|并|又|再)(?=出现|消失|转身|走向|走进|抬头|离开|消散|推进|拉远|横移|摇镜)", clause)
                    if "化作" in clause and "消散" in clause:
                        cut = clause.index("化作")
                        material = re.search(r"化作(.+?)(?:慢慢|缓缓)?消散", clause)
                        target = material.group(1).rstrip("慢缓") if material else "光点"
                        pieces = [f"{clause[:cut] or subject}化作{target}", f"{target}慢慢消散"]
                    for piece in pieces:
                        if not SUBJECTS.search(piece) and piece != clause:
                            piece = f"{subject}：{piece}" if "消散" not in piece else piece
                        event_subject = piece.split("慢慢消散")[0] if "慢慢消散" in piece else subject
                        events.append(Event(act, piece, event_subject, location, texture, dialogue))
                    previous_subject = subject
            light = re.search(r"光线[:：]([^，。；\n]+)", body)
            sound = re.search(r"(?:音效|声音)[:：]([^，。；\n]+)", body)
            for event in events[act_start:]:
                if light:
                    event.light = light.group(1)
                if sound:
                    event.sound = sound.group(1)
        return events


def prompt_for(event: Event, style: str, size: str, angle: str, camera: str, duration: int) -> str:
    return (f"AI视频生成提示词：主体：{event.subject}；场景：{event.location}；动作与画面：{event.content}；"
            f"景别：{size}；机位：{angle}；运镜：{camera}；光线：{event.light}；视觉风格：{STYLES[style]}；"
            f"表现材质：{event.texture or '依据参考素材，不额外推断'}；建议时长：{duration}秒；"
            "连续性约束：同幕保持人物外观、建筑轮廓和表现材质一致，仅执行当前事件。"
            f"\n音效：{event.sound}。转场：按镜头顺序衔接；原文中的转场依画面描述执行。"
            f"\n画面约束：{NEGATIVE}。幕次：{event.act}。"
            "\n后期制作：复杂运动、场景渐变或服装变化建议分段制作，以动作匹配和后期拼接保持连续；建筑表达依据实拍与可靠资料核对。")


def generate_storyboard(text: str, style: str, duration: int, backend: StoryboardBackend | None = None) -> pd.DataFrame:
    if style not in STYLES or duration not in (5, 7, 10):
        raise ValueError("请选择支持的风格和时长")
    rows = []
    for i, event in enumerate((backend or RuleBackend()).split(text), 1):
        size = next((s for s in ("远景", "全景", "中景", "近景", "特写") if s in event.content), "全景")
        angle = next((s for s in ("平视", "俯视", "仰视") if s in event.content), "平视")
        camera = next((s for s in CAMERAS if s in event.content), "固定")
        content = event.content + (f"；以{event.texture}呈现" if event.texture else "")
        rows.append([f"{i:02d}", event.location, content, size, angle, camera, duration, event.dialogue,
                     prompt_for(event, style, size, angle, camera, duration), ""])
    return pd.DataFrame(rows, columns=COLUMNS)
