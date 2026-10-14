import streamlit as st

from generator import EXAMPLE, STYLES, copy_text, export_csv, export_excel
from storyboard import generate_storyboard
from ai_storyboard import (AIError, AI_EXAMPLE, MODELS, MAX_INPUT, MAX_CONTINUITY,
                           MAX_SHOTS, build_payload, claim_request, generate_ai, resolve_api_key)

st.set_page_config(page_title="VideoPrompt Studio v0.3", page_icon="🎬", layout="wide")
st.title("🎬 VideoPrompt Studio v0.3 · 云端 AI 智能分镜版")
st.caption("中文视频分镜提示词工具 · 规则模式 / DeepSeek 智能分析 · 支持人工编辑与导出")
mode = st.radio("生成模式", ["规则模式", "AI智能模式"], horizontal=True)
if mode == "规则模式":
    st.info("规则模式无需 API Key。按幕次、主体切换和视觉事件拆镜头；无法识别时保留原文信息，请人工核对。景别、机位、运镜与时长是可修改的拍摄建议，不代表建筑史实。规则生成不调用 API。")
if st.button("载入佛光寺示例"):
    st.session_state["source"] = EXAMPLE
source = st.text_area("视频文案或分镜描述", key="source", height=180, max_chars=MAX_INPUT, placeholder="粘贴完整文案。可使用换行区分分镜。")
left, right = st.columns(2)
style = left.selectbox("视频风格", list(STYLES))
duration = right.selectbox("单镜头建议时长", [5, 7, 10], format_func=lambda n: f"{n}秒")
if mode == "规则模式":
    if st.button("生成分镜", type="primary"):
        if not source.strip():
            st.warning("请先输入文案，或载入示例。")
        else:
            st.session_state["scenes"] = generate_storyboard(source, style, duration)
            st.session_state["revision"] = st.session_state.get("revision", 0) + 1
            st.session_state["result_origin"] = "规则模式"
else:
    st.warning("AI 调用可能产生 API 费用，由您填写的密钥所属账户承担。文案将发送至 DeepSeek。仅点击“开始AI生成”才调用 API。")
    model = st.selectbox("DeepSeek 模型", list(MODELS), format_func=MODELS.get)
    st.text_input("您的 DeepSeek API Key", type="password", key="deepseek_key", max_chars=512,
                                help="仅用于当前会话的服务端请求，不写入文件或日志。刷新或离开后请重新填写。")
    target_input = st.number_input("目标总时长（秒，0 表示不指定）", min_value=0, max_value=600, value=0, step=1)
    continuity = st.text_area("人物与场景连续性要求（可选）", max_chars=MAX_CONTINUITY,
                              placeholder="例如同一少女、保持面部与发型一致、始终向画面右前方行走。")
    max_shots = st.number_input("最大镜头数", min_value=1, max_value=MAX_SHOTS, value=12, step=1)
    st.caption("限制：文案8000字、连续性1000字、最多24镜头、输出8192 Token；60秒网络超时；自动重试0次。目标时长为规划目标，请核对实际总时长。")
    st.expander("第四至第六幕验收文案").code(AI_EXAMPLE, language=None, wrap_lines=True)
    if st.button("开始AI生成", type="primary", disabled=st.session_state.get("ai_busy", False)):
        try:
            payload = build_payload(source, style, duration, model, target_input or None, continuity, max_shots)
            if not resolve_api_key(st.session_state.get("deepseek_key", "")):
                raise AIError("请填写自己的 DeepSeek API Key；也可以切换规则模式。")
            if not claim_request(st.session_state, payload):
                st.warning("本会话已提交相同参数或正在生成，已阻止重复调用。需要重新付费生成时，请先点击下方解除按钮。")
            else:
                st.session_state["ai_status"] = "生成中"
                st.session_state["ai_usage"] = {}
                try:
                    with st.spinner("DeepSeek 正在分析剧情并生成分镜…"):
                        frame, usage = generate_ai(payload, resolve_api_key(st.session_state["deepseek_key"]))
                    st.session_state["scenes"] = frame
                    st.session_state["revision"] = st.session_state.get("revision", 0) + 1
                    st.session_state["result_origin"] = f"AI智能模式 · {model}"
                    st.session_state["ai_status"] = "AI 生成成功（已通过 JSON 与十列字段校验）"
                    st.session_state["ai_usage"] = usage
                except AIError as error:
                    st.session_state["ai_status"] = f"AI 生成失败：{error} 原有表格保留，可继续编辑或使用规则模式。"
                    st.session_state["ai_usage"] = getattr(error, "usage", {})
                finally:
                    st.session_state["ai_busy"] = False
        except AIError as error:
            st.error(str(error))
    if st.session_state.get("ai_attempt"):
        if st.button("解除相同请求保护（下次开始AI生成可能再次计费）", disabled=st.session_state.get("ai_busy", False)):
            st.session_state.pop("ai_attempt", None)
            st.info("已解除保护；请再次点击“开始AI生成”提交新的调用。")
    if st.session_state.get("ai_status"):
        status = st.session_state["ai_status"]
        (st.error if "失败" in status else st.success)(status)
        usage = st.session_state.get("ai_usage", {})
        st.caption("Token 用量：" + (" / ".join(f"{label} {usage.get(key, '未提供')}" for key, label in
                   [("prompt_tokens", "输入"), ("completion_tokens", "输出"), ("total_tokens", "总计")]) if usage else "API 未提供，不能据此判断是否计费"))

if "scenes" in st.session_state:
    st.subheader("分镜表格")
    st.caption(f"当前表格来源：{st.session_state.get('result_origin', '规则模式')}")
    st.caption("可编辑、增删镜头；修改画面或镜头参数后请同步修改备注中的提示词。配图暂为空，可填写参考图路径或链接，后续可扩展上传；本版不加载或生成图片。")
    edited = st.data_editor(
        st.session_state["scenes"],
        num_rows="dynamic",
        hide_index=True,
        width="stretch",
        row_height=100,
        alt="可编辑的视频分镜提示词表格",
        key=f"editor_{st.session_state['revision']}",
        column_config={
            "时长（秒）": st.column_config.NumberColumn("时长（秒）", min_value=1, step=1),
            "镜头号": st.column_config.TextColumn("镜头号", pinned=True),
            "画面内容": st.column_config.TextColumn("画面内容", width="large"),
            "备注": st.column_config.TextColumn("备注", width="large"),
        },
    )
    st.caption(f"当前镜头数：{len(edited)} · 总时长：{edited['时长（秒）'].sum():g} 秒")
    a, b = st.columns(2)
    a.download_button("下载 Excel", export_excel(edited), "VideoPrompt_分镜.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    b.download_button("下载 CSV", export_csv(edited), "VideoPrompt_分镜.csv", "text/csv")
    with st.expander("逐镜头查看完整画面与备注"):
        for _, row in edited.iterrows():
            st.text(f"镜头 {row['镜头号']} · {row['地点']}\n画面：{row['画面内容']}\n对话：{row['对话']}\n{row['备注']}")
    st.subheader("逐镜头提示词")
    st.caption("点击代码框右上角复制按钮，即可复制全部镜头。")
    st.code(copy_text(edited), language=None, wrap_lines=True)
    st.caption("佛光寺示例只提供地点与东大殿名称，未指定年代、构件数量、尺寸、材质或修缮信息。规则工具不能核实事实，请使用可靠资料与实拍参考。")
