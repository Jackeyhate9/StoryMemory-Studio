import os
from pathlib import Path

import streamlit as st

from app.llm.validation import validate_llm_connection
from app.ui.components.result_panel import result_panel
from app.ui.services import (
    ENV_PATH,
    health_snapshot,
    migrate_data_storage,
    save_env,
    suggested_data_dirs,
)

st.title("模型与数据设置")
st.caption(f"配置文件：{ENV_PATH}")

health = health_snapshot()

st.subheader("本地数据位置")
st.caption("章节、记忆库、文风画像和生成日志优先保存在本机。C 盘空间紧张时，建议迁移到 D/E 盘。")

col_a, col_b, col_c = st.columns(3)
col_a.metric("当前数据库", "已初始化" if health["database_exists"] else "未创建")
col_b.metric("数据库大小", f"{health['database_size_mb']} MB")
col_c.metric("位置提示", "可能在系统盘" if health["on_system_drive"] else "非系统盘或自定义路径")

st.code(health["database_path"], language="text")

suggestions = suggested_data_dirs()
selected_suggestion = st.selectbox("常用数据目录", suggestions, index=0)
new_data_dir = st.text_input("数据目录", value=selected_suggestion, help="会在该目录下保存本地数据库。可以填写 D:\\长篇记忆小说 之类的路径。")
copy_existing = st.checkbox("迁移时复制当前数据库", value=True)

data_cols = st.columns(2)
with data_cols[0]:
    if st.button("应用数据目录", type="primary"):
        try:
            target_db = migrate_data_storage(new_data_dir, copy_existing=copy_existing)
            st.success(f"数据目录已更新：{target_db}")
            st.info("如果页面仍显示旧路径，请刷新或重启应用。")
        except Exception as exc:
            st.error(str(exc))
with data_cols[1]:
    if st.button("只初始化当前数据库"):
        try:
            target_db = migrate_data_storage(str(Path(health["database_path"]).parent), copy_existing=True)
            st.success(f"数据库已确认可用：{target_db}")
        except Exception as exc:
            st.error(str(exc))

st.divider()
st.subheader("模型接入")
st.caption("文风学习、记忆抽取、章节生成都会优先使用这里的默认模型；页面中选择“自动识别”时，会按 DeepSeek、OpenAI 兼容服务、OpenAI、Ollama 的可用情况自动选择。")

provider_options = ["deepseek", "openai_compatible", "openai", "ollama"]
current_provider = os.getenv("STORYMEMORY_LLM_PROVIDER", "deepseek")
provider = st.selectbox(
    "默认模型提供方",
    provider_options,
    index=provider_options.index(current_provider) if current_provider in provider_options else 0,
)

with st.expander("DeepSeek", expanded=provider == "deepseek"):
    deepseek_key = st.text_input("DeepSeek 密钥", value=os.getenv("DEEPSEEK_API_KEY", ""), type="password")
    deepseek_base = st.text_input("DeepSeek 服务地址", value=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    deepseek_model = st.text_input("DeepSeek 模型名称", value=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"))

with st.expander("OpenAI 兼容服务", expanded=provider == "openai_compatible"):
    compatible_key = st.text_input("OpenAI 兼容服务密钥", value=os.getenv("OPENAI_COMPATIBLE_API_KEY", ""), type="password")
    compatible_base = st.text_input("OpenAI 兼容服务地址", value=os.getenv("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1"))
    compatible_model = st.text_input("OpenAI 兼容模型名称", value=os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-4o-mini"))

with st.expander("OpenAI", expanded=provider == "openai"):
    openai_key = st.text_input("OpenAI 密钥", value=os.getenv("OPENAI_API_KEY", ""), type="password")
    openai_base = st.text_input("OpenAI 服务地址", value=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    openai_model = st.text_input("OpenAI 模型名称", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

with st.expander("Ollama 本地模型", expanded=provider == "ollama"):
    ollama_base = st.text_input("Ollama 地址", value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model = st.text_input("Ollama 模型名称", value=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
    st.caption("如果模型不存在，请先执行：ollama pull 模型名。使用 Ollama 时，章节和样章不会发送到外部接口。")

settings_payload = {
    "STORYMEMORY_LLM_PROVIDER": provider,
    "DEEPSEEK_API_KEY": deepseek_key,
    "DEEPSEEK_BASE_URL": deepseek_base,
    "DEEPSEEK_MODEL": deepseek_model,
    "OPENAI_API_KEY": openai_key,
    "OPENAI_BASE_URL": openai_base,
    "OPENAI_MODEL": openai_model,
    "OPENAI_COMPATIBLE_API_KEY": compatible_key,
    "OPENAI_COMPATIBLE_BASE_URL": compatible_base,
    "OPENAI_COMPATIBLE_MODEL": compatible_model,
    "OLLAMA_BASE_URL": ollama_base,
    "OLLAMA_MODEL": ollama_model,
    "STORYMEMORY_DB_PATH": health["database_path"],
}

col1, col2 = st.columns(2)
with col1:
    if st.button("保存模型设置", type="primary"):
        save_env(settings_payload)
        st.success("模型设置已保存。")
with col2:
    if st.button("测试默认模型连接"):
        save_env(settings_payload)
        result = validate_llm_connection(provider)
        if result["ok"]:
            st.success(result["message"])
        else:
            st.error(result["message"])
        result_panel("连接校验结果", result)

with st.expander("数据安全说明", expanded=False):
    st.markdown(
        f"""
        - 当前数据库：`{health["database_path"]}`
        - 配置文件保存接口密钥，请只在本机使用，不要上传到代码仓库。
        - 文风学习默认不保存完整样章，只保存哈希、短摘录和抽象风格画像。
        - 使用 DeepSeek / OpenAI / OpenAI 兼容服务时，只有你主动调用模型，相关上下文才会发送到对应服务。
        - 使用 Ollama 时，模型调用走本地地址：`{os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")}`。
        """
    )
