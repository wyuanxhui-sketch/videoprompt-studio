import unittest
from io import BytesIO
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest

from generator import COLUMNS, EXAMPLE, copy_text, export_csv, export_excel, generate, split_scenes


class GeneratorTests(unittest.TestCase):
    def test_sentence_boundaries(self):
        self.assertEqual(split_scenes("山峦、寺庙，映入眼帘。镜头稳定！\n观察建筑？"), ["山峦、寺庙，映入眼帘。", "镜头稳定！", "观察建筑？"])

    def test_long_sentence_not_cut(self):
        text = "观察" + "建筑" * 200 + "。"
        self.assertEqual(split_scenes(text), [text])

    def test_blank_and_paragraph(self):
        self.assertEqual(split_scenes(" \n\n"), [])
        self.assertEqual(split_scenes("外观\n\n内部"), ["外观", "内部"])

    def test_quotes_and_decimal(self):
        self.assertEqual(split_scenes('他说：“保持稳定。”\n建议观察2.5米范围。'), ['他说：“保持稳定。”', '建议观察2.5米范围。'])

    def test_schema_and_settings(self):
        frame = generate(EXAMPLE, "建筑纪录片", 7)
        self.assertEqual(list(frame.columns), COLUMNS)
        self.assertEqual(frame["时长"].tolist(), [7, 7, 7])
        self.assertEqual(frame["镜头编号"].tolist(), [1, 2, 3])
        self.assertIn("固定机位", frame.iloc[0]["运镜方式"])

    def test_invalid_settings(self):
        with self.assertRaises(ValueError):
            generate("外观", "未知", 7)

    def test_exports_and_edits(self):
        frame = generate("观察建筑。", "通用", 5)
        frame.loc[0, "完整中文视频提示词"] = "=修改后的提示词"
        csv = export_csv(frame)
        self.assertTrue(csv.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(pd.read_csv(BytesIO(csv)).iloc[0]["完整中文视频提示词"], "=修改后的提示词")
        sheet = load_workbook(BytesIO(export_excel(frame))).active
        self.assertEqual(sheet["G2"].value, "=修改后的提示词")
        self.assertEqual(sheet["G2"].data_type, "s")
        self.assertIn("=修改后的提示词", copy_text(frame))

    def test_app_flow(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
        self.assertFalse(app.exception)
        app.button[0].click().run()
        self.assertEqual(app.text_area[0].value, EXAMPLE)
        app.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe[0].value), 3)
        self.assertIn("镜头 1", app.code[0].value)


if __name__ == "__main__":
    unittest.main()
