from pathlib import Path
from html import escape
import base64
import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='馬場風雲 · Team 11 | RACE EDGE', page_icon='🏇', layout='wide')
display_font = base64.b64encode((ROOT / 'assets/fonts/Teko.ttf').read_bytes()).decode('ascii')
font_css = "@font-face{font-family:'Race Display';src:url(data:font/ttf;base64," + display_font + ") format('truetype');font-weight:300 700;font-display:swap;}"
st.markdown('<style>' + font_css + (ROOT / 'assets/style.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)


@st.cache_data
def load_data():
    predictions = pd.read_csv(ROOT / 'artifacts/predictions.csv', parse_dates=['race_date'])
    history = pd.read_csv(ROOT / 'artifacts/horse_history.csv', parse_dates=['race_date'])
    report = json.loads((ROOT / 'artifacts/model_report.json').read_text(encoding='utf-8'))
    return predictions, history, report


@st.cache_data
def hero_art():
    """Embed committed artwork so Cloud needs no external image service."""
    return base64.b64encode((ROOT / 'assets/hong-kong-hero.png').read_bytes()).decode('ascii')


def chart_theme(figure, height=360):
    figure.update_layout(
        height=height, margin=dict(l=0, r=24, t=12, b=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(75,0,13,0.5)',
        font=dict(family='Segoe UI, sans-serif', color='#ffe9b7', size=12),
        legend=dict(orientation='h', y=1.14, x=0, font=dict(size=11)),
        hoverlabel=dict(bgcolor='#4b0711', font_size=13),
    )
    figure.update_xaxes(gridcolor='rgba(255,212,59,0.19)', zeroline=False, tickfont=dict(family='Race Display, sans-serif', size=21, color='#ffe672'))
    figure.update_yaxes(gridcolor='rgba(255,212,59,0.13)', zeroline=False)
    return figure


def comparison_chart(field):
    ordered = field.sort_values('model_probability', ascending=True)
    labels = ordered.apply(lambda row: f"{int(row.horse_number):02d}  {row.horse_name}", axis=1)
    figure = go.Figure()
    figure.add_trace(go.Bar(
        y=labels, x=ordered.model_probability * 100, name='模型胜率', orientation='h',
        marker=dict(color=['#ffd43b' if rank == 1 else '#ffad24' for rank in ordered.model_rank], line=dict(color='#fff1a0', width=1.2), cornerradius=0), width=.62,
        text=[f'{value:.1%}' for value in ordered.model_probability], textposition='outside',
        textfont=dict(family='Race Display, sans-serif', color='#fff1c5', size=21),
        hovertemplate='%{y}<br>模型胜率 %{x:.1f}%<extra></extra>',
    ))
    figure.add_trace(go.Scatter(
        y=labels, x=ordered.market_probability * 100, name='赔率归一化概率',
        mode='markers', marker=dict(color='#ff779d', size=10, symbol='diamond', line=dict(color='#fff0dc', width=1)),
        hovertemplate='%{y}<br>赔率归一化概率 %{x:.1f}%<extra></extra>',
    ))
    figure.update_layout(bargap=.25)
    figure.update_xaxes(ticksuffix='%', range=[0, max(field.model_probability.max(), field.market_probability.max()) * 125])
    return chart_theme(figure, max(340, len(field) * 29 + 60))


data, history, report = load_data()
course_names = {'Sha Tin': '沙田 · SHA TIN', 'Happy Valley': '跑马地 · HAPPY VALLEY'}
st.session_state.setdefault('watchlist', [])
with st.sidebar:
    st.markdown('<div class="side-emblem" aria-hidden="true">馬</div><div class="brand">馬場<span>風雲</span></div><div class="side-tag">RACE EDGE · HONG KONG EDITION</div><div class="side-couplet">鑼鼓響 · 睇好馬 · 論勝負</div>', unsafe_allow_html=True)
    st.caption('赛事导航 / RACE SELECTOR')
    course = st.selectbox('赛场', list(course_names), format_func=lambda value: course_names[value])
    course_data = data.loc[data.race_course.eq(course)]
    dates = sorted(course_data.race_date.dt.date.unique(), reverse=True)
    date = st.selectbox('比赛日期', dates, format_func=lambda value: value.strftime('%Y.%m.%d'))
    race_rows = course_data.loc[course_data.race_date.dt.date.eq(date)].drop_duplicates('race_id').sort_values('race_number')
    race_id = st.selectbox('场次', race_rows.race_id.tolist(), index=len(race_rows)-1,
        format_func=lambda value: f"R{int(race_rows.loc[race_rows.race_id.eq(value), 'race_number'].iloc[0]):02d}  ·  {int(race_rows.loc[race_rows.race_id.eq(value), 'race_distance'].iloc[0])}m")
    reveal = st.toggle('揭晓历史赛果', value=False)
    st.markdown('<div class="side-note"><b>HISTORICAL REPLAY</b><br>原始数据：2014.09—2017.07<br>可回放预测：2017.01—2017.07<br><br>生产设想：赛后更新历史；<br>赛前赔率每 60 秒刷新。<br>当前 CSV 为固定快照。</div>', unsafe_allow_html=True)
    with st.expander(f"观察清单 · {len(st.session_state.watchlist)}"):
        if not st.session_state.watchlist:
            st.caption('在马匹详情中加入观察对象。')
        for item in st.session_state.watchlist:
            st.caption(item)
        if st.session_state.watchlist and st.button('清空观察清单'):
            st.session_state.watchlist = []
            st.rerun()

field = data.loc[data.race_id.eq(race_id)].sort_values('model_rank').copy()
race = field.iloc[0]
leader = field.iloc[0]
st.markdown('<div class="masthead"><span class="status"><i></i> 2017 歷史賽事回放</span><span class="edition">港式霓虹版 / HONG KONG NIGHTS</span></div>', unsafe_allow_html=True)
st.title('Team 11 · 馬場風雲')
st.caption('面向赛前投注研究者：比较马匹胜率与市场定价，筛选值得进一步研究的候选马匹。')
st.markdown(f'''<div class="race-hero"><img class="hero-art" src="data:image/png;base64,{hero_art()}" alt="成年女骑师与赛马，红金港式霓虹海报插画"><div class="hero-shade"></div><div class="hero-content"><div class="race-kicker">RACE EDGE 呈獻 / {escape(race.race_course.upper())}</div><div class="hero-seal">賽馬<br>研究社</div>
<div class="race-heading">馬場風雲<br><em>今場，睇真啲。</em></div><div class="hero-subtitle">一場好戲，一眼看清勝率與賠率。</div>
<div class="race-meta"><span>第 {int(race.race_number):02d} 場</span><span>{int(race.race_distance):,} 米</span><span>{len(field)} 匹出賽</span><span>{escape(str(race.race_class))}</span></div><div class="hero-footnote">{date.strftime('%Y.%m.%d')} · {escape(str(race.surface).upper())} · {escape(str(race.track_condition))} · 歷史數據回放</div></div><div class="poster-stamp">香 港<br><b>賽 馬</b></div></div><div class="ticker-strip" aria-label="本页功能"><span>✦ 全場勝率</span><span>✦ 賠率對照</span><span>✦ 馬匹近況</span><span>✦ 歷史驗證</span></div>''', unsafe_allow_html=True)
st.caption('数据：2014-09-14—2017-07-16，Kaggle 历史快照 · 生产刷新设想：赛后更新历史，赛前赔率每 60 秒刷新。')

prediction_tab, validation_tab = st.tabs(['壹 /  赛前情报', '贰 /  历史检验'])
with prediction_tab:
    st.markdown(f'<div class="race-callout"><span class="callout-tag">本場焦點</span><span>模型首选 <b>#{int(leader.horse_number):02d} {escape(leader.horse_name)}</b></span><span class="callout-end">賽前情報局 / MODEL PICK</span></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1.container(key='kpi-win'):
        st.metric('首选马匹 · 模型胜率', f'{leader.model_probability:.1%}', help='同场预测概率之和为 100%；这是模型估计，不是命中承诺。')
    with c2.container(key='kpi-odds'):
        st.metric('历史独赢赔率 · 参考', f'{leader.win_odds:.1f}', help='数据中的历史 win_odds；记录时点未知，不代表当时可成交报价。')
    with c3.container(key='kpi-gap'):
        st.metric('模型 − 市场概率', f'{leader.probability_gap * 100:+.1f} pp', help='模型胜率 − 归一化的 1/赔率。正值仅表示模型看法高于赔率基准，不等于预期盈利。')
    st.caption('市场概率 = (1 / 本马历史赔率) ÷ 同场所有马匹的 (1 / 历史赔率) 之和；pp 表示百分点。')
    left, right = st.columns([2.1, 1], gap='large')
    with left:
        st.markdown('<div class="section-head">胜率与市场定价<span>FULL FIELD / 全场对照</span></div>', unsafe_allow_html=True)
        st.plotly_chart(comparison_chart(field), width='stretch', config={'displayModeBar': False})
    with right:
        st.markdown('<div class="section-head">金榜三甲<span>模型前三顺位</span></div>', unsafe_allow_html=True)
        for index, (_, runner) in enumerate(field.head(3).iterrows()):
            st.markdown(f'''<div class="pick-card {'first' if index == 0 else ''}"><div class="pick-ribbon">第{['壹','貳','叁'][index]}順位 <span>MODEL RANK {index + 1:02d}</span></div><div class="pick-top"><div class="silk">{int(runner.horse_number):02d}</div><div class="pick-name">{escape(runner.horse_name)}</div><div class="pick-prob">{runner.model_probability:.1%}</div></div><div class="pick-bottom"><span>{escape(runner.jockey)}</span><span>赔率 <b>{runner.win_odds:.1f}</b> · 档位 <b>{int(runner.draw)}</b></span></div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="micro">模型依据历史表现独立排序。金色柱为模型胜率，粉色菱形为赔率基准；差距是进一步研究的线索。</div>', unsafe_allow_html=True)
        if reveal:
            winner = field.loc[field.won.eq(1)].iloc[0]
            st.success(f"历史冠军：#{int(winner.horse_number)} {winner.horse_name}")
    st.markdown('<div class="section-head">参赛马匹<span>RUNNER INTELLIGENCE</span></div>', unsafe_allow_html=True)
    labels = {'horse_number':'马号','horse_name':'马名','model_probability':'模型胜率','market_probability':'市场概率',
              'probability_gap':'概率差 pp','win_odds':'历史赔率','draw':'档位','jockey':'骑师','trainer':'练马师','finishing_position':'真实名次'}
    columns = ['horse_number','horse_name','model_probability','market_probability','probability_gap','win_odds','draw','jockey','trainer']
    if reveal:
        columns.append('finishing_position')
    display = field[columns].copy()
    display['probability_gap'] *= 100
    display['model_probability'] *= 100
    display['market_probability'] *= 100
    display = display.rename(columns=labels)
    table_style = display.style.set_properties(**{'background-color':'#700b1a', 'color':'#fff1d0'}).set_properties(subset=['马号','模型胜率','历史赔率'], **{'color':'#ffdf4c', 'font-weight':'bold'})
    st.dataframe(table_style, hide_index=True, width='stretch', height=325,
        column_config={
            '模型胜率': st.column_config.ProgressColumn(format='%.1f%%', min_value=0, max_value=100),
            '市场概率': st.column_config.NumberColumn(format='%.1f%%'),
            '概率差 pp': st.column_config.NumberColumn(format='%+.1f'),
            '历史赔率': st.column_config.NumberColumn(format='%.1f'),
        })
    # Export respects result reveal and the selected race, matching visible data scope.
    st.download_button('下载本场分析 CSV', display.to_csv(index=False).encode('utf-8-sig'), file_name=f'race-edge-{race_id}.csv', mime='text/csv')
    selected_id = st.selectbox('查看马匹近况', field.horse_id.tolist(), format_func=lambda value: field.loc[field.horse_id.eq(value), 'horse_name'].iloc[0])
    selected = field.loc[field.horse_id.eq(selected_id)].iloc[0]
    past = history.loc[history.horse_id.eq(selected_id) & history.race_date.lt(pd.Timestamp(date))].sort_values('race_date').tail(5)
    st.markdown(f'<div class="runner-detail"><h3>#{int(selected.horse_number):02d} {escape(selected.horse_name)}</h3><div class="micro">{escape(selected.trainer)} · {escape(selected.jockey)} · {int(selected.horse_prior_starts)} 次历史出赛</div></div>', unsafe_allow_html=True)
    if len(past):
        chips = ''.join(f'<span class="form-chip {"good" if pd.notna(row.finish_rank) and row.finish_rank <= 3 else ""}" title="{row.race_date.date()} · {escape(row.race_course)} · {int(row.race_distance)}m">{escape(str(row.finishing_position))}</span>' for row in past.itertuples())
        st.markdown('<div class="form-strip"><span class="micro">最近五次 · 旧 → 新</span>' + chips + '</div>', unsafe_allow_html=True)
        st.caption(f'距离上次出赛 {int(selected.days_since_last)} 天；数据仅来自本场比赛日期之前。')
    else:
        st.caption('快照内没有此前出赛记录；模型使用保守先验。')
    watch_label = f'{date} · R{int(race.race_number)} · {selected.horse_name}'
    if st.button('＋ 加入观察清单', disabled=watch_label in st.session_state.watchlist):
        st.session_state.watchlist.append(watch_label)
        st.rerun()

with validation_tab:
    st.markdown('<div class="section-head">把预测交给历史检验<span>OUT-OF-TIME / 2017</span></div>', unsafe_allow_html=True)
    st.caption('固定模型与参数后，按时间回放 2017 年比赛；基准使用每场历史赔率最低的马匹。此页统计全部检验赛事，不随左侧单场筛选变化。')
    form = report['metrics']['Form model']
    market = report['metrics']['Closing market']
    difference = (form['top1_accuracy'] - market['top1_accuracy']) * 100
    message = '模型首选命中率高于赔率基准。' if difference > 0 else '模型首选命中率低于赔率基准；当前结果不支持模型优于市场的说法。'
    st.markdown(f'<div class="validation-banner">{message} 检验覆盖 {form["races"]} 场，差异 {difference:+.1f} 个百分点。历史赔率记录时点未知，比较结果不能解释为可实现的盈利。</div>', unsafe_allow_html=True)
    summary = pd.DataFrame([{
        '方法': label, '检验场数': values['races'], '首选命中场数': values['top1_hits'],
        '首选命中率': values['top1_accuracy'], '前三顺位覆盖冠军': values['top3_coverage'],
        '对数损失 ↓': values['log_loss'],
    } for label, values in report['metrics'].items() if label != 'Uniform'])
    summary['方法'] = summary['方法'].map({'Form model':'历史表现模型','Closing market':'历史赔率基准'})
    st.dataframe(summary, hide_index=True, width='stretch', column_config={
        '首选命中率':st.column_config.NumberColumn(format='percent'),
        '前三顺位覆盖冠军':st.column_config.NumberColumn(format='percent'),
        '对数损失 ↓':st.column_config.NumberColumn(format='%.3f'),
    })
    monthly = pd.DataFrame(report['monthly'])
    figure = go.Figure()
    for label, color, name in [('Form model','#ffd43b','历史表现模型'),('Closing market','#ff779d','历史赔率基准')]:
        group = monthly.loc[monthly.model.eq(label)]
        figure.add_trace(go.Scatter(x=group.month, y=group.top1_accuracy * 100, mode='lines+markers', name=name,
            line=dict(color=color,width=2.5), marker=dict(size=7),customdata=group[['races','top1_hits']],
            hovertemplate='%{x}<br>命中率 %{y:.1f}%<br>场数 %{customdata[0]} · 命中 %{customdata[1]}<extra></extra>'))
    figure.update_yaxes(ticksuffix='%', rangemode='tozero')
    st.markdown('<div class="section-head">首选命中率 · 月度变化<span>MONTHLY HIT RATE</span></div>', unsafe_allow_html=True)
    st.plotly_chart(chart_theme(figure, 330), width='stretch', config={'displayModeBar': False})
    st.caption('命中率 = 首选马匹实际获胜场数 / 当月可检验场数。前三顺位覆盖冠军 = 模型排序前三包含实际冠军的场次比例。对数损失越低越好，用于检验概率预测。')
    with st.expander('模型、数据与检验口径'):
        st.markdown(f'''- **训练期**：{report['train_period'][0]}—{report['train_period'][1]}，{report['train_races']} 场。
- **概率校准期**：{report['calibration_period'][0]}—{report['calibration_period'][1]}，{report['calibration_races']} 场。
- **独立检验期**：{report['test_period'][0]}—{report['test_period'][1]}，{report['test_races']} 场。
- 马匹、骑师、练马师历史统计均截在比赛日之前；模型不使用本场赔率、赛果、途中名次或完赛时间。
- 同场概率归一化为 100%；温度参数只在校准期选取，未使用检验期调参。
- 排除退赛、未参赛、未知参赛状态和并列第一场次；未完成比赛的有效参赛马匹保留为未获胜。
- 不展示收益率：数据缺少可成交的赛前赔率、完整派彩和费用，无法核算真实收益。
- [Kaggle 原始数据集](https://www.kaggle.com/datasets/lantanacamara/hong-kong-horse-racing)''')

with st.expander('数据来源与刷新计划'):
    st.markdown('本应用使用用户提供的两份 Kaggle CSV，经 `race_id` 合并；原始记录为 30,189 条马匹记录和 2,367 场比赛。当前数据为固定历史快照，只有 2017 年独立检验期开放预测回放。')
    st.markdown('生产设想：官方赛果确认后更新历史；赛前赔率每 60 秒刷新，用户在挑选赛事时查看，并在决策前复核报价。赔率源超过 120 秒未更新时应暂停显示概率差。当前页面未接入实时赔率。')
    st.markdown('[原始数据集](https://www.kaggle.com/datasets/lantanacamara/hong-kong-horse-racing) · [项目仓库](https://github.com/Ruoyu-Tianyi/horse-race-dashboard)')
st.markdown('<div class="footline">TEAM 11 · Zhou Tianyi / Xu Yiming / Zhang Zai / Xu Mohan<br>RACE EDGE / COURSE PROJECT · 历史研究与模拟预测 · 数据截止 2017-07-16 · 概率差表示模型与赔率基准的分歧。</div>', unsafe_allow_html=True)
