import os
import time
import json
import html
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

try:
    import akshare as ak
except Exception as exc:
    ak = None
    AK_IMPORT_ERROR = exc

st.set_page_config(page_title="AlphaMind (阿尔法智脑)", layout="wide")

APP_DIR = Path(__file__).resolve().parent
STOCK_CACHE_PATH = APP_DIR / "stock_universe_cache.csv"
STOCK_CACHE_MAX_AGE_HOURS = 24
STOCK_CACHE_RETRY_MINUTES = 30
OPENCLAW_HOME = Path.home() / ".openclaw"
OPENCLAW_CONFIG_PATH = OPENCLAW_HOME / "openclaw.json"
WOLF_AGENT_CONFIG_PATH = OPENCLAW_HOME / "workspace" / "agents" / "wall-street-wolf" / "agent.json"

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&family=Space+Grotesk:wght@400;600;700&display=swap');
      :root {
        --bg: #f7f9fc;
        --bg-soft: #eef2f7;
        --card: #ffffff;
        --card-2: #f3f6fb;
        --text: #101828;
        --muted: #4b5565;
        --primary: #2563eb;
        --primary-2: #3b82f6;
        --accent: #0ea5e9;
        --radius: 18px;
      }
      html, body, [class*="stApp"] {
        background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 35%);
        color: var(--text);
        font-family: "Space Grotesk", "Segoe UI", sans-serif;
      }
      .block-container {padding-top: 5.75rem;}

      .topbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 64px;
        background: rgba(255, 255, 255, 0.98);
        border-bottom: 1px solid rgba(15, 23, 42, 0.12);
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 2.5rem;
        z-index: 10000;
        backdrop-filter: blur(12px);
      }
      .brand-title {
        font-weight: 700;
        font-size: 1rem;
        color: #0f172a;
        text-shadow: 0 1px 0 rgba(255,255,255,0.6);
      }
      .brand-sub {
        color: #22304a;
        font-size: 0.82rem;
      }
      .logo-text {
        font-family: "ZCOOL KuaiLe", "Space Grotesk", sans-serif;
        font-size: 1.1rem;
        color: #1e3a8a;
        letter-spacing: 0.12em;
        font-weight: 700;
      }

      .hero-wrap {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 0.5rem;
      }
      .hero-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.45rem 0.85rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.1);
        color: #1e40af;
        font-size: 0.95rem;
        font-weight: 600;
        border: 1px solid rgba(37, 99, 235, 0.25);
      }
      .hero-title {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        color: var(--text);
      }
      .hero-logo {
        font-family: "ZCOOL KuaiLe", "Space Grotesk", sans-serif;
        font-size: 0.95rem;
        color: #1d4ed8;
        letter-spacing: 0.14em;
        background: #e8eefc;
        padding: 0.35rem 0.7rem;
        border-radius: 12px;
        border: 1px solid rgba(29, 78, 216, 0.15);
      }

      section[data-testid="stSidebar"] {
        background: var(--bg-soft);
        border-right: 1px solid rgba(15, 23, 42, 0.12);
        z-index: 9999;
      }
      section[data-testid="stSidebar"] * {
        color: #0f172a !important;
      }

      .stButton > button {
        background: linear-gradient(120deg, var(--primary), var(--primary-2));
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        border-radius: 14px;
        font-weight: 600;
      }
      .stTextInput input, .stSelectbox select, .stSlider {
        background-color: var(--card);
        color: var(--text) !important;
        border-radius: 12px !important;
      }
      label, p, span, div {
        color: var(--text);
      }
      .stMetric {
        background: var(--card);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: var(--radius);
        padding: 0.6rem 0.85rem;
      }
      div[data-testid="stMetricValue"] {
        color: var(--text);
      }
      div[data-testid="stMetricDelta"] {
        color: var(--accent);
      }
      .section-title {
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
        color: var(--text);
      }
      .card-block {
        background: var(--card-2);
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: var(--radius);
        padding: 1rem;
        color: var(--text);
      }
      .panel-title {
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: var(--text);
      }
      .muted {color: var(--muted) !important;}

      .slider-wrap {
        background: #ffffff;
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: var(--radius);
        padding: 0.85rem 0.85rem 0.45rem;
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.05);
        margin-bottom: 0.6rem;
      }
      .slider-title {
        font-size: 0.85rem;
        color: #111827;
        font-weight: 600;
        margin-bottom: 0.25rem;
      }
      .slider-hint {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.3rem;
      }

      .stPlotlyChart, .stDataFrame {
        border-radius: var(--radius);
        overflow: hidden;
      }

      .news-item {
        padding: 0.6rem 0.2rem;
        border-bottom: 1px dashed rgba(15, 23, 42, 0.08);
      }
      .news-item:last-child {
        border-bottom: none;
      }
      .news-title {
        font-weight: 600;
        font-size: 0.9rem;
      }
      .news-meta {
        color: var(--muted);
        font-size: 0.75rem;
      }

      @media (max-width: 900px) {
        .hero-title {font-size: 1.35rem;}
        .topbar {padding: 0 1.25rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="topbar">
      <div class="brand">
        <div class="brand-title">AlphaMind 投研台</div>
        <div class="brand-sub">多 Agent · 数据驱动 · 专业分析</div>
      </div>
      <div class="logo-text">MADE BY WQ</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-wrap">
      <div class="hero-pill">AlphaMind · 阿尔法智脑</div>
      <div class="hero-title">智能投研快速分析台</div>
      <div class="hero-logo">MADE BY WQ</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("仅供研究与教学演示，不构成任何投资建议")

if "rate_limit" not in st.session_state:
    st.session_state.rate_limit = {}


def rate_limit_ok(source: str, window_sec: int) -> bool:
    last = st.session_state.rate_limit.get(source, 0)
    now = time.time()
    if now - last < window_sec:
        return False
    st.session_state.rate_limit[source] = now
    return True


@st.cache_data(ttl=600)
def fetch_news_serpapi(query: str, api_key: str):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_news",
        "q": query,
        "hl": "zh-cn",
        "gl": "cn",
        "api_key": api_key,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("news_results", [])


@st.cache_data(ttl=600)
def fetch_news_newsapi(query: str, api_key: str):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "zh",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": api_key,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("articles", [])


def analyze_sentiment(headlines):
    positive = ["利好", "上涨", "增长", "超预期", "回暖", "创新高", "盈利", "突破"]
    negative = ["利空", "下跌", "下滑", "亏损", "警告", "暴跌", "裁员", "减持"]
    pos = neg = 0
    for title in headlines:
        for k in positive:
            if k in title:
                pos += 1
                break
        for k in negative:
            if k in title:
                neg += 1
                break
    score = pos - neg
    return pos, neg, score


def normalize_news(items, source_name: str):
    normalized = []
    for item in items:
        title = item.get("title") or ""
        if not title:
            continue
        link = item.get("link") or item.get("url") or ""
        source = item.get("source") if isinstance(item.get("source"), str) else (item.get("source") or {}).get("name")
        published = item.get("date") or item.get("publishedAt") or ""
        normalized.append(
            {
                "title": title,
                "source": source or source_name,
                "link": link,
                "published": published,
            }
        )
    return normalized


def merge_dedupe(items, limit: int):
    seen = set()
    merged = []
    for item in items:
        key = item["title"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= limit:
            break
    return merged


def fetch_news_bundle(
    query: str,
    serp_key: str,
    news_key: str,
    prefer_free: bool,
    news_max: int,
    rate_window: int,
    bypass_rate_limit: bool = False,
):
    sources = ["newsapi", "serpapi"] if prefer_free else ["serpapi", "newsapi"]
    collected = []
    for source in sources:
        if source == "serpapi" and serp_key:
            if bypass_rate_limit or rate_limit_ok("serpapi", rate_window):
                try:
                    raw_items = fetch_news_serpapi(query, serp_key)
                    collected.extend(normalize_news(raw_items, "SerpAPI"))
                except Exception:
                    pass

        if source == "newsapi" and news_key:
            if bypass_rate_limit or rate_limit_ok("newsapi", rate_window):
                try:
                    raw_items = fetch_news_newsapi(query, news_key)
                    collected.extend(normalize_news(raw_items, "NewsAPI"))
                except Exception:
                    pass
    return merge_dedupe(collected, news_max)


def looks_mojibake(text: str) -> bool:
    return any(token in text for token in ["鍗", "浣", "銆", "€", "", "�"])


def default_wolf_agent() -> dict:
    return {
        "name": "华尔街之狼",
        "description": "顶级金融投资专家，擅长股票分析、市场预测和投资策略建议。",
        "model": "deepseek/deepseek-chat",
        "systemPrompt": (
            "你是名为“华尔街之狼”的顶级金融投资专家。你擅长股票市场分析、技术分析和基本面分析。"
            "你的风格专业、自信、果断，但表达清晰易懂，始终基于数据和事实。"
            "请结合技术面、市场情绪和风险控制，给出明确的买入/持有/卖出倾向，并说明理由、风险点和观察重点。"
            "请始终使用中文回答，不要夸大收益，也不要给出绝对承诺。"
        ),
    }


def load_wall_street_wolf_agent() -> dict:
    agent = default_wolf_agent()
    if not WOLF_AGENT_CONFIG_PATH.exists():
        return agent
    try:
        raw = json.loads(WOLF_AGENT_CONFIG_PATH.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return agent
    for key in ["name", "description", "model", "systemPrompt"]:
        value = raw.get(key)
        if isinstance(value, str) and value.strip() and not looks_mojibake(value):
            agent[key] = value.strip()
    return agent


def load_openclaw_model_config() -> dict:
    config = {"base_url": "https://api.deepseek.com/v1", "api_key": "", "model": "deepseek-chat"}
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if OPENCLAW_CONFIG_PATH.exists():
        try:
            raw = json.loads(OPENCLAW_CONFIG_PATH.read_text(encoding="utf-8", errors="ignore"))
            env_key = (raw.get("env") or {}).get("DEEPSEEK_API_KEY")
            provider = ((raw.get("models") or {}).get("providers") or {}).get("deepseek") or {}
            if env_key:
                api_key = env_key
            if provider.get("baseUrl"):
                config["base_url"] = provider["baseUrl"]
        except Exception:
            pass
    config["api_key"] = api_key
    return config


def build_wolf_stock_context(
    stock_name: str,
    symbol: str,
    latest_close: float,
    change_pct: float,
    ma5: float,
    ma20: float,
    rsi14: float | None,
    days: int,
    summary_text: str,
    news_titles: tuple[str, ...],
) -> str:
    news_text = "；".join(news_titles[:5]) if news_titles else "暂无有效新闻标题"
    rsi_text = f"{rsi14:.1f}" if rsi14 is not None and not pd.isna(rsi14) else "暂无"
    return f"""
当前分析标的如下：
股票名称：{stock_name}
股票代码：{symbol}
市场：A股
最新收盘价：{latest_close:.2f}
当日涨跌幅：{change_pct:.2f}%
MA5：{ma5:.2f}
MA20：{ma20:.2f}
RSI14：{rsi_text}
观察周期：近 {days} 天
系统摘要：{summary_text}
相关新闻标题：{news_text}
""".strip()


def request_wolf_completion(messages: list[dict]) -> dict:
    agent = load_wall_street_wolf_agent()
    model_config = load_openclaw_model_config()
    if not model_config["api_key"]:
        return {"ok": False, "message": "未找到 OpenClaw 的 DeepSeek 配置，暂时无法生成华尔街之狼建议。"}

    session = make_direct_session()
    endpoint = model_config["base_url"].rstrip("/") + "/chat/completions"
    model_name = agent.get("model", "deepseek/deepseek-chat").split("/")[-1]
    payload = {
        "model": model_name,
        "messages": [{"role": "system", "content": agent["systemPrompt"]}] + messages,
        "temperature": 0.7,
        "max_tokens": 400,
    }
    headers = {
        "Authorization": f"Bearer {model_config['api_key']}",
        "Content-Type": "application/json",
    }
    try:
        resp = session.post(endpoint, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        if not content:
            return {"ok": False, "message": "华尔街之狼暂时没有给出有效建议。"}
        return {"ok": True, "title": agent["name"], "content": content}
    except Exception:
        return {"ok": False, "message": "华尔街之狼建议生成失败，请稍后重试。"}


@st.cache_data(ttl=900)
def fetch_wall_street_wolf_commentary(
    stock_name: str,
    symbol: str,
    latest_close: float,
    change_pct: float,
    ma5: float,
    ma20: float,
    rsi14: float | None,
    days: int,
    summary_text: str,
    news_titles: tuple[str, ...],
):
    context_text = build_wolf_stock_context(
        stock_name=stock_name,
        symbol=symbol,
        latest_close=latest_close,
        change_pct=change_pct,
        ma5=ma5,
        ma20=ma20,
        rsi14=rsi14,
        days=days,
        summary_text=summary_text,
        news_titles=news_titles,
    )
    user_prompt = f"""
请站在“华尔街之狼”的视角，对下面这只股票给出一段专业建议。

{context_text}

输出要求：
1. 先给一句总体判断：买入 / 观察持有 / 谨慎减仓 三选一
2. 再给 2 到 4 句理由，兼顾技术面和情绪面
3. 最后补一句风险提示
4. 全文控制在 120 到 220 字
5. 语言保持专业、自信、像资深投研人，但不要夸张
""".strip()
    return request_wolf_completion([{"role": "user", "content": user_prompt}])


def ensure_news_cache(query: str, serp_key: str, news_key: str, prefer_free: bool, news_max: int) -> None:
    if not query or not (serp_key or news_key):
        return
    if not bootstrap_once("news_auto_refresh_done"):
        return
    news_items = fetch_news_bundle(
        query=query,
        serp_key=serp_key,
        news_key=news_key,
        prefer_free=prefer_free,
        news_max=news_max,
        rate_window=0,
        bypass_rate_limit=True,
    )
    if news_items:
        st.session_state["news_cache_status"] = f"本次启动已自动更新新闻缓存，共 {len(news_items)} 条"
    else:
        st.session_state["news_cache_status"] = "本次启动未获取到新闻缓存，查询时会继续尝试"


def read_stock_cache() -> pd.DataFrame:
    if not STOCK_CACHE_PATH.exists():
        return pd.DataFrame(columns=["代码", "名称"])
    df = pd.read_csv(STOCK_CACHE_PATH, dtype=str).fillna("")
    return df[["代码", "名称"]]


def write_stock_cache(df: pd.DataFrame) -> None:
    df[["代码", "名称"]].dropna().to_csv(STOCK_CACHE_PATH, index=False, encoding="utf-8-sig")


def stock_cache_age_hours() -> float | None:
    if not STOCK_CACHE_PATH.exists():
        return None
    modified_at = datetime.fromtimestamp(STOCK_CACHE_PATH.stat().st_mtime)
    return (datetime.now() - modified_at).total_seconds() / 3600


def should_refresh_stock_cache() -> bool:
    age_hours = stock_cache_age_hours()
    if age_hours is None:
        return True
    if age_hours < STOCK_CACHE_MAX_AGE_HOURS:
        return False
    last_attempt = st.session_state.get("stock_cache_refresh_attempt")
    if not last_attempt:
        return True
    return (time.time() - last_attempt) >= STOCK_CACHE_RETRY_MINUTES * 60


def bootstrap_once(key: str) -> bool:
    if st.session_state.get(key):
        return False
    st.session_state[key] = True
    return True


@st.cache_data(ttl=3600)
def fetch_ashare_universe_remote() -> pd.DataFrame:
    df = ak.stock_info_a_code_name().rename(columns={"code": "代码", "name": "名称"})
    return df.drop_duplicates(subset=["代码"])


def fetch_ashare_universe(force_refresh: bool = False) -> pd.DataFrame:
    cached = read_stock_cache()
    if not force_refresh and not cached.empty:
        return cached
    fresh = fetch_ashare_universe_remote()
    if not fresh.empty:
        write_stock_cache(fresh)
        return fresh
    return cached


def ensure_stock_cache() -> None:
    if not bootstrap_once("stock_cache_auto_refresh_done"):
        return
    st.session_state["stock_cache_refresh_attempt"] = time.time()
    cached = read_stock_cache()
    try:
        fresh = fetch_ashare_universe_remote()
        if not fresh.empty:
            write_stock_cache(fresh)
            st.session_state["stock_cache_status"] = "本次启动已自动刷新股票列表"
            return
    except Exception:
        pass
    if not cached.empty:
        st.session_state["stock_cache_status"] = "本次启动刷新股票列表失败，当前继续使用本地缓存"
        return
    st.session_state["stock_cache_status"] = "本次启动未能建立股票列表缓存"


@st.cache_data(ttl=300)
def fetch_symbol_matches(query: str, limit: int = 10) -> pd.DataFrame:
    encoded_query = requests.utils.quote(query)
    url = f"https://searchapi.eastmoney.com/api/suggest/get?input={encoded_query}&type=14&count={limit}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    rows = ((payload.get("QuotationCodeTable") or {}).get("Data")) or []
    df = pd.DataFrame(
        [{"代码": row.get("Code"), "名称": row.get("Name")} for row in rows if row.get("Code") and row.get("Name")]
    )
    if df.empty:
        return pd.DataFrame(columns=["代码", "名称"])
    df["代码"] = df["代码"].astype(str).str.zfill(6)
    return df[df["代码"].str.len() == 6].drop_duplicates(subset=["代码"])


def resolve_symbol(query: str):
    q = (query or "").strip()
    if not q:
        return None, None, "请输入 A 股代码或关键词。"
    if q.isdigit() and len(q) == 6:
        return q, None, ""
    try:
        matched = fetch_symbol_matches(q, limit=20)
        if matched.empty:
            universe = fetch_ashare_universe()
            matched = universe[universe["名称"].str.contains(q, na=False, regex=False)]
    except Exception as exc:
        try:
            universe = fetch_ashare_universe()
            matched = universe[universe["名称"].str.contains(q, na=False, regex=False)]
        except Exception:
            return None, None, f"股票列表加载失败：{exc}"
    if matched.empty:
        return None, None, f"未找到匹配“{q}”的股票，请更换关键词或直接输入代码。"
    return None, matched, ""


def suggest_symbols(query: str, limit: int = 10):
    q = (query or "").strip()
    if not q or (q.isdigit() and len(q) == 6):
        return []
    try:
        merged = fetch_symbol_matches(q, limit=limit)
    except Exception:
        universe = fetch_ashare_universe()
        starts = universe[universe["名称"].str.startswith(q, na=False)]
        contains = universe[universe["名称"].str.contains(q, na=False, regex=False)]
        merged = pd.concat([starts, contains]).drop_duplicates(subset=["代码"])
    suggestions = [f"{row['名称']} ({row['代码']})" for _, row in merged.iterrows()]
    return suggestions[:limit]


def get_stock_cache_text() -> str:
    if not STOCK_CACHE_PATH.exists():
        return f"股票列表缓存未生成，系统会自动尝试刷新（每 {STOCK_CACHE_MAX_AGE_HOURS} 小时一次）"
    updated_at = datetime.fromtimestamp(STOCK_CACHE_PATH.stat().st_mtime).strftime("%m-%d %H:%M")
    return (
        f"股票列表缓存已生成，更新时间 {updated_at}；"
        f"系统会在缓存超过 {STOCK_CACHE_MAX_AGE_HOURS} 小时后自动刷新"
    )


def clear_selected_symbol() -> None:
    st.session_state["selected_symbol"] = ""
    st.session_state["selected_name"] = ""


def apply_suggestion_choice() -> None:
    picked = st.session_state.get("suggest_choice", "")
    if not picked:
        return
    picked_name = picked.split("(")[0].strip()
    picked_symbol = picked.split("(")[-1].replace(")", "").strip()
    st.session_state["query_input"] = picked_name
    st.session_state["selected_symbol"] = picked_symbol
    st.session_state["selected_name"] = picked_name
    st.session_state["auto_run"] = True


def save_analysis_context(query_text: str, symbol: str, display_name: str, days: int, adjust_label: str) -> None:
    st.session_state["analysis_context"] = {
        "query_text": query_text,
        "symbol": symbol,
        "display_name": display_name,
        "days": days,
        "adjust_label": adjust_label,
    }


def sync_wolf_chat_state(symbol: str, display_name: str, opening_message: str) -> None:
    current_symbol = st.session_state.get("wolf_chat_symbol")
    if current_symbol != symbol:
        st.session_state["wolf_chat_symbol"] = symbol
        st.session_state["wolf_chat_display_name"] = display_name
        st.session_state["wolf_chat_messages"] = [{"role": "assistant", "content": opening_message}]


def make_direct_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def resolve_secid(symbol: str) -> str:
    if symbol.startswith(("5", "6", "9")):
        return f"1.{symbol}"
    return f"0.{symbol}"


def adjust_to_fqt(adjust: str) -> str:
    mapping = {"qfq": "1", "hfq": "2", "": "0"}
    return mapping.get(adjust, "1")


def to_ak_daily_symbol(symbol: str) -> str:
    if symbol.startswith(("5", "6", "9")):
        return f"sh{symbol}"
    return f"sz{symbol}"


with st.sidebar:
    st.header("查询设置")
    query_input = st.text_input(
        "A 股代码 / 关键词",
        value="600519",
        help="支持 6 位股票代码或公司关键词",
        key="query_input",
    )
    selected_name = st.session_state.get("selected_name", "")
    if selected_name and query_input.strip() != selected_name:
        clear_selected_symbol()

    st.markdown("<div class='slider-wrap'>", unsafe_allow_html=True)
    st.markdown("<div class='slider-title'>回溯天数</div>", unsafe_allow_html=True)
    days = st.slider("", min_value=30, max_value=365, value=180, step=10, label_visibility="collapsed")
    st.markdown("<div class='slider-hint'>建议 90~180 天用于观察趋势</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    ensure_stock_cache()
    auto_suggest_on = st.checkbox("开启公司简称自动联想", value=True)
    if auto_suggest_on:
        st.caption(get_stock_cache_text())
        cache_status = st.session_state.get("stock_cache_status", "")
        if cache_status:
            st.caption(cache_status)
        current_query = st.session_state.query_input.strip()
        if current_query and not (current_query.isdigit() and len(current_query) == 6):
            if len(current_query) < 2:
                st.caption("继续输入至少 2 个字后，会自动显示候选。")
                st.session_state["suggest_choice"] = ""
            else:
                try:
                    suggestions = suggest_symbols(current_query, limit=10)
                except Exception as exc:
                    suggestions = []
                    st.warning(f"候选加载失败：{exc}")
                if suggestions:
                    st.caption(f"已找到 {len(suggestions)} 条候选")
                    options = [""] + suggestions
                    selected = st.session_state.get("suggest_choice", "")
                    default_index = options.index(selected) if selected in options else 0
                    st.selectbox(
                        "公司简称自动联想",
                        options=options,
                        index=default_index,
                        key="suggest_choice",
                        on_change=apply_suggestion_choice,
                    )
                else:
                    st.caption("暂时没有匹配到候选，可以继续输入更完整的公司名称。")
                    st.session_state["suggest_choice"] = ""
        else:
            st.session_state["suggest_choice"] = ""

    adjust_map = {
        "前复权（推荐）": "qfq",
        "后复权": "hfq",
        "不复权": "",
    }
    adjust_label = st.selectbox("复权方式", options=list(adjust_map.keys()), index=0)

    st.markdown("---")
    st.subheader("新闻接口配置")
    st.markdown(
        """
        <div class="card-block" style="margin-bottom: 0.65rem;">
          <div class="panel-title">提示</div>
          <div class="muted">优先使用系统环境变量（推荐），也可以在这里临时输入。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    serp_key = os.getenv("SERPAPI_API_KEY") or ""
    news_key = os.getenv("NEWSAPI_KEY") or ""
    prefer_free = st.checkbox("优先使用免费额度（NewsAPI 优先）", value=True)
    news_max = st.slider("新闻条数（最多）", min_value=3, max_value=12, value=6, step=1)
    rate_window = st.slider("接口请求间隔（秒）", min_value=6, max_value=30, value=12, step=2)
    serp_input = st.text_input("SerpAPI Key（可选）", value="" if serp_key else "", type="password")
    news_input = st.text_input("NewsAPI Key（可选）", value="" if news_key else "", type="password")
    serp_key_final = serp_input or serp_key
    news_key_final = news_input or news_key
    ensure_news_cache(query_input.strip(), serp_key_final, news_key_final, prefer_free, news_max)
    news_cache_status = st.session_state.get("news_cache_status", "")
    if news_cache_status:
        st.caption(news_cache_status)
    run = st.button("开始生成报告")

if ak is None:
    st.error(f"AkShare 导入失败：{AK_IMPORT_ERROR}")
    st.stop()

@st.cache_data(ttl=300)
def fetch_ashare(symbol: str, start_date: str, end_date: str, adjust: str) -> pd.DataFrame:
    try:
        daily_df = ak.stock_zh_a_daily(symbol=to_ak_daily_symbol(symbol), adjust=adjust)
        if daily_df is not None and not daily_df.empty:
            df = daily_df.copy().reset_index()
            if "date" not in df.columns:
                df = df.rename(columns={df.columns[0]: "date"})
            df["date"] = pd.to_datetime(df["date"])
            start_dt = pd.to_datetime(start_date, format="%Y%m%d")
            end_dt = pd.to_datetime(end_date, format="%Y%m%d")
            df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)].copy()
            df["prev_close"] = df["close"].shift(1)
            df["涨跌额"] = (df["close"] - df["prev_close"]).fillna(0)
            df["涨跌幅"] = ((df["close"] / df["prev_close"] - 1) * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
            df["振幅"] = ((df["high"] - df["low"]) / df["prev_close"] * 100).replace([np.inf, -np.inf], np.nan).fillna(0)
            renamed = df.rename(
                columns={
                    "date": "日期",
                    "open": "开盘",
                    "close": "收盘",
                    "high": "最高",
                    "low": "最低",
                    "volume": "成交量",
                    "amount": "成交额",
                    "turnover": "换手率",
                }
            )
            return renamed[["日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]]
    except Exception:
        pass

    session = make_direct_session()
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": "101",
        "fqt": adjust_to_fqt(adjust),
        "secid": resolve_secid(symbol),
        "beg": start_date,
        "end": end_date,
    }
    resp = session.get(url, params=params, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("data") or {}
    klines = data.get("klines") or []
    if not klines:
        return pd.DataFrame()
    rows = []
    for item in klines:
        parts = item.split(",")
        if len(parts) < 11:
            continue
        rows.append(
            {
                "日期": parts[0],
                "开盘": float(parts[1]),
                "收盘": float(parts[2]),
                "最高": float(parts[3]),
                "最低": float(parts[4]),
                "成交量": float(parts[5]),
                "成交额": float(parts[6]),
                "振幅": float(parts[7]),
                "涨跌幅": float(parts[8]),
                "涨跌额": float(parts[9]),
                "换手率": float(parts[10]),
            }
        )
    return pd.DataFrame(rows)

@st.cache_data
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI14"] = 100 - (100 / (1 + rs))
    return df

auto_run = st.session_state.pop("auto_run", False) if "auto_run" in st.session_state else False
should_run = run or auto_run
analysis_context = st.session_state.get("analysis_context")
should_render_analysis = should_run or bool(analysis_context)

if should_render_analysis:
    active_query_text = query_input
    active_days = days
    active_adjust_label = adjust_label
    selected_symbol = st.session_state.get("selected_symbol", "")
    selected_name = st.session_state.get("selected_name", "")
    if should_run:
        if selected_symbol and query_input.strip() == selected_name:
            symbol = selected_symbol
            matches = None
            resolve_msg = ""
            display_name = selected_name
        else:
            symbol, matches, resolve_msg = resolve_symbol(query_input)
            display_name = query_input
        if resolve_msg:
            st.warning(resolve_msg)
        if matches is not None:
            options = [f"{row['名称']} ({row['代码']})" for _, row in matches.iterrows()][:20]
            if not options:
                st.stop()
            pick = st.selectbox("匹配到多条结果，请选择", options=options, index=0)
            symbol = pick.split("(")[-1].replace(")", "").strip()
            display_name = pick.split("(")[0].strip()
            st.session_state["selected_symbol"] = symbol
            st.session_state["selected_name"] = display_name
        if not symbol:
            st.stop()
        save_analysis_context(active_query_text, symbol, display_name, active_days, active_adjust_label)
    else:
        active_query_text = analysis_context.get("query_text", query_input)
        symbol = analysis_context.get("symbol", "")
        display_name = analysis_context.get("display_name", active_query_text)
        active_days = analysis_context.get("days", days)
        active_adjust_label = analysis_context.get("adjust_label", adjust_label)
        if not symbol:
            st.stop()

    end = datetime.now()
    start = end - timedelta(days=active_days)
    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")

    with st.spinner("正在拉取行情数据..."):
        try:
            raw = fetch_ashare(symbol, start_str, end_str, adjust_map[active_adjust_label])
        except Exception as exc:
            st.error(f"行情拉取失败：{exc}")
            st.stop()

    if raw is None or raw.empty:
        st.warning("未获取到数据，请检查股票代码是否正确。")
        st.stop()

    df = raw.rename(
        columns={
            "日期": "Date",
            "开盘": "Open",
            "收盘": "Close",
            "最高": "High",
            "最低": "Low",
            "成交量": "Volume",
            "成交额": "Amount",
            "振幅": "Amplitude",
            "涨跌幅": "PctChange",
            "涨跌额": "Change",
            "换手率": "Turnover",
        }
    )
    df["Date"] = pd.to_datetime(df["Date"])
    df = add_indicators(df)

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    change_pct = (latest["Close"] / prev["Close"] - 1) * 100 if prev["Close"] else 0

    st.markdown("<div class='section-title'>关键指标概览</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最新收盘价", f"{latest['Close']:.2f}")
    c2.metric("当日涨跌幅", f"{change_pct:.2f}%")
    c3.metric("成交量", f"{latest['Volume'] / 1e6:.2f} 百万")
    c4.metric("RSI(14)", f"{latest['RSI14']:.1f}" if pd.notna(latest["RSI14"]) else "-")

    left, right = st.columns([2.1, 1])
    news_titles = []

    with left:
        st.markdown("<div class='section-title'>技术面走势</div>", unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=df["Date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="K 线",
            )
        )
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MA5"], name="均线 MA5"))
        fig.add_trace(go.Scatter(x=df["Date"], y=df["MA20"], name="均线 MA20"))
        fig.update_layout(height=520, margin=dict(l=10, r=10, t=30, b=10), template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("<div class='section-title'>情绪面观察</div>", unsafe_allow_html=True)

        news_items = fetch_news_bundle(
            query=active_query_text,
            serp_key=serp_key_final,
            news_key=news_key_final,
            prefer_free=prefer_free,
            news_max=news_max,
            rate_window=rate_window,
        )

        if news_items:
            titles = []
            for item in news_items:
                title = item.get("title") or ""
                if not title:
                    continue
                titles.append(title)
                link = item.get("link") or ""
                source = item.get("source") or "来源未知"
                published = item.get("published") or ""
                title_html = f"<a href='{link}' target='_blank'>{title}</a>" if link else title
                meta = f"{source} {published}".strip()
                st.markdown(
                    f"""
                    <div class="news-item">
                      <div class="news-title">{title_html}</div>
                      <div class="news-meta">{meta}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            news_titles = titles
            pos, neg, score = analyze_sentiment(titles)
            st.markdown(
                f"""
                <div class="card-block" style="margin-top: 12px;">
                  <div class="panel-title">情绪评分（规则法）</div>
                  <div>利好新闻数：{pos}</div>
                  <div>负面新闻数：{neg}</div>
                  <div>情绪评分：{score}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="card-block">
                  <div class="panel-title">市场情绪（占位）</div>
                  <div class="muted">未获取到新闻数据，可能是接口额度或网络限制。</div>
                  <div style="margin-top: 12px;">
                    <div>利好新闻数：--</div>
                    <div>负面新闻数：--</div>
                    <div>情绪评分：--</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div class='section-title'>分析摘要</div>", unsafe_allow_html=True)
        summary = (
            f"当前 {display_name} 最新收盘价为 {latest['Close']:.2f}，近 {active_days} 天均线 MA5/MA20 "
            f"分别为 {latest['MA5']:.2f} / {latest['MA20']:.2f}。"
        )
        st.markdown(f"<div class='card-block'>{summary}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>华尔街之狼观点</div>", unsafe_allow_html=True)
    with st.spinner("华尔街之狼正在研判这只股票..."):
        wolf_result = fetch_wall_street_wolf_commentary(
            stock_name=display_name,
            symbol=symbol,
            latest_close=float(latest["Close"]),
            change_pct=float(change_pct),
            ma5=float(latest["MA5"]) if pd.notna(latest["MA5"]) else float(latest["Close"]),
            ma20=float(latest["MA20"]) if pd.notna(latest["MA20"]) else float(latest["Close"]),
            rsi14=float(latest["RSI14"]) if pd.notna(latest["RSI14"]) else None,
            days=active_days,
            summary_text=summary,
            news_titles=tuple(news_titles),
        )

    if wolf_result.get("ok"):
        wolf_title = wolf_result.get("title") or "华尔街之狼"
        sync_wolf_chat_state(symbol, display_name, wolf_result["content"])
        wolf_context = build_wolf_stock_context(
            stock_name=display_name,
            symbol=symbol,
            latest_close=float(latest["Close"]),
            change_pct=float(change_pct),
            ma5=float(latest["MA5"]) if pd.notna(latest["MA5"]) else float(latest["Close"]),
            ma20=float(latest["MA20"]) if pd.notna(latest["MA20"]) else float(latest["Close"]),
            rsi14=float(latest["RSI14"]) if pd.notna(latest["RSI14"]) else None,
            days=active_days,
            summary_text=summary,
            news_titles=tuple(news_titles),
        )
        st.markdown(
            f"""
            <div class="card-block">
              <div class="panel-title">{html.escape(wolf_title)} 对话框</div>
              <div class="muted">你可以继续追问这只股票的短线判断、风险点、买卖节奏和仓位建议。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        chat_messages = st.session_state.get("wolf_chat_messages", [])
        for message in chat_messages:
            with st.chat_message("assistant" if message["role"] == "assistant" else "user"):
                st.markdown(message["content"])

        prompt = st.chat_input(f"继续向{wolf_title}追问 {display_name}...")
        if prompt:
            chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner(f"{wolf_title} 正在回答..."):
                    reply = request_wolf_completion(
                        [
                            {"role": "system", "content": wolf_context},
                            *chat_messages,
                        ]
                    )
                    if reply.get("ok"):
                        st.markdown(reply["content"])
                        chat_messages.append({"role": "assistant", "content": reply["content"]})
                    else:
                        st.markdown(reply.get("message", "暂时无法回答这个问题。"))
                        chat_messages.append(
                            {"role": "assistant", "content": reply.get("message", "暂时无法回答这个问题。")}
                        )
            st.session_state["wolf_chat_messages"] = chat_messages
    else:
        st.markdown(
            f"""
            <div class="card-block">
              <div class="panel-title">华尔街之狼</div>
              <div class="muted">{html.escape(wolf_result.get("message", "暂时无法生成建议。"))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption("免责声明：本系统仅做数据展示与分析演示，不构成任何投资建议。")
else:
    st.info("在左侧输入 A 股代码或公司关键词即可开始；选中联想候选后会自动生成报告。")
