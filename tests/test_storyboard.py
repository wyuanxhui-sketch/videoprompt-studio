import unittest
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest

from generator import export_csv, export_excel
from storyboard import COLUMNS, RuleBackend, generate_storyboard

SAMPLE = "第一幕是少女的背影看着佛光寺大殿、应县木塔、永宁门的立面依次出现又消失，这些画面都由银色的线条和光点组成，然后所有化作银色光点慢慢消散。"


class StoryboardTests(unittest.TestCase):
    def test_acceptance_events(self):
        frame = generate_storyboard(SAMPLE, "通用", 7)
        self.assertGreaterEqual(len(frame), 5)
        self.assertEqual(list(frame.columns), COLUMNS)
        self.assertEqual(frame["画面内容"].nunique(), len(frame))
        self.assertTrue(all(SAMPLE != s for s in frame["画面内容"]))
        self.assertEqual(frame.iloc[0]["镜头号"], "01")
        for subject in ("少女", "佛光寺大殿", "应县木塔", "永宁门", "银色光点"):
            self.assertTrue(frame["画面内容"].str.contains(subject).any())
        buildings = frame[frame["画面内容"].str.contains("立面")]
        self.assertTrue(buildings["画面内容"].str.contains("银色的线条和光点").all())
        self.assertTrue((frame["地点"] == "未明确").all())

    def test_multiple_acts_context_reset(self):
        events = RuleBackend().split("第一幕：少女转身，然后走向大殿。第二幕：应县木塔出现，然后消失。第三幕：永宁门出现。")
        self.assertEqual([e.act for e in events], ["第一幕", "第一幕", "第二幕", "第二幕", "第三幕"])
        self.assertEqual(events[3].subject, "应县木塔")

    def test_action_states(self):
        frame = generate_storyboard("第一幕：少女转身并走向大殿。然后镜头推进。", "电影写实", 5)
        self.assertEqual(len(frame), 3)
        self.assertEqual(frame.iloc[-1]["运镜"], "推进")

    def test_dialogue_not_split(self):
        frame = generate_storyboard('第一幕：少女说：“然后转身，再离开。”', "通用", 10)
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["对话"], "然后转身，再离开。")

    def test_empty_and_invalid(self):
        self.assertTrue(generate_storyboard("", "通用", 5).empty)
        with self.assertRaises(ValueError):
            generate_storyboard(SAMPLE, "未知", 5)

    def test_prompt_and_excel(self):
        frame = generate_storyboard(SAMPLE, "动画", 7)
        for label in ("主体", "场景", "动作", "景别", "机位", "运镜", "光线", "视觉风格", "连续性约束", "音效", "转场", "画面约束"):
            self.assertIn(label, frame.iloc[0]["备注"])
        frame.loc[0, "备注"] = "=用户编辑"
        sheet = load_workbook(BytesIO(export_excel(frame))).active
        self.assertEqual([c.value for c in sheet[1]], COLUMNS)
        self.assertEqual(sheet["A2"].value, "01")
        self.assertEqual(sheet["I2"].value, "=用户编辑")
        self.assertEqual(sheet["I2"].data_type, "s")
        self.assertTrue(export_csv(frame).startswith(b"\xef\xbb\xbf"))

    def test_web_acceptance(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
        app.text_area[0].set_value(SAMPLE).run()
        app.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(list(app.dataframe[0].value.columns), COLUMNS)
        self.assertGreaterEqual(len(app.dataframe[0].value), 5)


if __name__ == "__main__":
    unittest.main()
