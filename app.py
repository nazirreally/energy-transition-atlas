"""Energy Transition Atlas: multi-source observed energy and development intelligence."""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import streamlit as st
from src.data import OWID, build_panel, coverage, fetch_grapher, fetch_world_bank, latest_observed
from src.momentum import adjacent_year_changes, transition_quadrants

st.set_page_config(page_title='Energy Transition Atlas',page_icon='⚡',layout='wide',initial_sidebar_state='expanded')
COLORS=['#45e2c0','#7da8ff','#efc789','#b8a0f8','#8de0ff','#8bd0c6']
LABELS={'renewables_share':'Renewables share of electricity (%)','fossil_share':'Fossil-fuel share of electricity (%)',
        'electricity_demand':'Electricity demand (TWh)','co2_per_capita':'CO₂ emissions per capita (t)',
        'gdp_per_capita':'GDP per capita (current USD)'}
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;700;800&display=swap');
:root{--mint:#45e2c0;--ink:#081421;--panel:#112538}
.stApp{background:radial-gradient(ellipse at 70% -10%,#173e4b 0%,transparent 55%),#081421;color:#edf7ff;font-family:'DM Sans',sans-serif}
[data-testid="stSidebar"]{background:#0c1b2d;border-right:1px solid #29445a}
.block-container{max-width:1560px;padding-top:1.2rem}
h1,h2,h3{font-family:'Manrope',sans-serif!important;letter-spacing:-.045em!important}
.hero{padding:35px 38px;border-radius:23px;border:1px solid #346477;background:linear-gradient(115deg,#163849,#0f2035 75%);margin-bottom:19px}
.hero h1{font-size:clamp(2.1rem,3.5vw,3.4rem);margin:4px 0 12px;color:#f0fcff}
.hero p{max-width:780px;color:#bfd6e8;font-size:14px;line-height:1.7}
.eyebrow{color:#61f1d5;font-size:11px;font-weight:800;letter-spacing:.2em}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:15px 0 22px}
.kpi{background:#11283a;border:1px solid #345468;border-radius:16px;padding:18px;min-height:115px}
.kpi span{display:block;font-size:11px;color:#bed3e5;font-weight:700;text-transform:uppercase;letter-spacing:.08em}
.kpi b{display:block;font-size:clamp(19px,2vw,29px);margin:11px 0 0;color:#f2fcff}
[data-testid="stPlotlyChart"]{background:#0c2032;border:1px solid #29465b;border-radius:17px;padding:9px}
.stTabs [data-baseweb="tab-list"]{background:#10253a;border:1px solid #34536b;border-radius:13px;padding:5px;gap:7px}
.stTabs [data-baseweb="tab"]{color:#d0e0ed!important;border-radius:9px;font-weight:700}
.stTabs [aria-selected="true"]{background:#1c4c50!important;color:#8af9e0!important}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
.stApp [data-baseweb="tag"]{background:#175453!important;color:#dcfff6!important;border-radius:7px}
.stApp [data-baseweb="tag"] *{color:#dcfff6!important}
.stApp [data-baseweb="select"]>div{background:#173148!important;color:#effaff!important;border-color:#40647b!important}
.stApp [data-testid="stWidgetLabel"] p{color:#d2e4f2!important}
.stApp [data-baseweb="slider"] [role="slider"]{background:#45e2c0!important}
.stApp [data-testid="stRadio"] input,.stApp [data-testid="stCheckbox"] input{accent-color:#45e2c0!important}
@media(max-width:800px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.hero{padding:23px}}
</style>''',unsafe_allow_html=True)

@st.cache_data(ttl=86400,show_spinner='Downloading observed public energy and development data…')
def load():
    return build_panel({k:fetch_grapher(k) for k in OWID},fetch_world_bank())

def figstyle(fig,height=420):
    fig.update_layout(height=height,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(color='#e9f5ff',family='DM Sans',size=12),margin=dict(l=10,r=10,t=22,b=25),
                      hoverlabel=dict(bgcolor='#173247',bordercolor='#45e2c0',font=dict(color='#f5ffff',size=13),align='left'),
                      legend=dict(orientation='h',y=1.08,bgcolor='rgba(0,0,0,0)'))
    fig.update_xaxes(gridcolor='rgba(160,193,218,.12)',zeroline=False)
    fig.update_yaxes(gridcolor='rgba(160,193,218,.12)',zeroline=False)
    return fig

def show(fig,height=420):
    st.plotly_chart(figstyle(fig,height),use_container_width=True,theme=None,config={'displaylogo':False,'responsive':True})

st.markdown('''<div class="hero"><div class="eyebrow">◈ GLOBAL ENERGY INTELLIGENCE / RESEARCH STUDIO</div>
<h1>Mapping the energy transition.</h1><p>Explore observed electricity mixes, demand, carbon emissions and economic development across countries and decades. Five independently published series, joined transparently by country and year.</p></div>''',unsafe_allow_html=True)
try:
    data=load()
except Exception as exc:
    st.error(f'Published data retrieval or validation failed: {exc}')
    st.info('No sample or simulated observations will be substituted. Verify source URLs and try again.')
    st.stop()
with st.sidebar:
    st.markdown('### ⚡ ATLAS CONTROLS')
    metric=st.selectbox('Energy or development indicator',list(LABELS),format_func=lambda x:LABELS[x])
    years=sorted(data.loc[data[metric].notna(),'year'].unique().tolist())
    if not years:
        st.error('No observed years for selected indicator');st.stop()
    year=st.select_slider('Reporting year',options=years,value=years[-1])
    countries=sorted(data.country.dropna().unique())
    default=[c for c in ['Pakistan','India','China','United States','Germany','Brazil'] if c in countries]
    selected=st.multiselect('Compare countries',countries,default=default)
    show_missing=st.checkbox('Show countries without observations in table',value=False)
    st.caption('Data: Our World in Data Grapher + World Bank Indicators API. No fabricated values.')
current=latest_observed(data,metric,year)
if current.empty:
    st.warning('No observed values for this indicator and year. Select another year.');st.stop()
median=current[metric].median()
latest=int(data.loc[data[metric].notna(),'year'].max())
format_num=lambda v: f'{v:,.1f}' if pd.notna(v) else '—'
st.markdown(f'''<div class="kpis"><div class="kpi"><span>Countries reporting</span><b>{current.iso3.nunique():,}</b></div>
<div class="kpi"><span>Country-year observations</span><b>{data[metric].notna().sum():,}</b></div>
<div class="kpi"><span>Observed median · {year}</span><b>{format_num(median)}</b></div>
<div class="kpi"><span>Latest observed year</span><b>{latest}</b></div></div>''',unsafe_allow_html=True)
world,compare,relationships,momentum,quality=st.tabs(['◉ World explorer','⌁ Country trajectories','◇ Transition relationships','↗ Transition momentum','▦ Source & coverage lab'])
with world:
    st.subheader('The geography of energy')
    a,b=st.columns(2)
    with a: projection=st.selectbox('Projection',['natural earth','orthographic','equirectangular'])
    with b: map_mode=st.radio('Map representation',['Choropleth','Proportional bubbles'],horizontal=True)
    if map_mode=='Choropleth':
        fig=px.choropleth(current,locations='iso3',color=metric,hover_name='country',
                          custom_data=['year'],projection=projection,
                          color_continuous_scale=['#193b57','#218b99','#4be2c1','#c8ffe9'],labels={metric:LABELS[metric]})
    else:
        positive=current[current[metric].gt(0)]
        if positive.empty:
            st.info('This metric has no strictly positive observations for proportional circles.')
            fig=None
        else:
            fig=px.scatter_geo(positive,locations='iso3',size=metric,color=metric,hover_name='country',
                               custom_data=['year'],projection=projection,size_max=34,
                               color_continuous_scale=['#193b57','#218b99','#4be2c1','#c8ffe9'],labels={metric:LABELS[metric]})
    if fig is not None:
        fig.update_traces(hovertemplate='<b>%{hovertext}</b><br>'+LABELS[metric]+': %{z:,.2f}<br>Year: %{customdata[0]}<extra></extra>' if map_mode=='Choropleth' else '<b>%{hovertext}</b><br>'+LABELS[metric]+': %{marker.color:,.2f}<br>Year: %{customdata[0]}<extra></extra>')
        fig.update_geos(showframe=False,showcoastlines=True,coastlinecolor='#385267',showland=True,landcolor='#162b3e',showocean=True,oceancolor='#081421',bgcolor='rgba(0,0,0,0)')
        show(fig,520)
    c1,c2=st.columns([1.15,1])
    with c1:
        st.subheader('Country leaderboard')
        direction=st.radio('Ranking direction',['Highest','Lowest'],horizontal=True)
        n=st.slider('Countries in ranking',5,30,15)
        ranked=(current.nlargest(n,metric) if direction=='Highest' else current.nsmallest(n,metric)).sort_values(metric)
        fig=px.bar(ranked,x=metric,y='country',orientation='h',color=metric,color_continuous_scale='Tealgrn',labels={metric:LABELS[metric],'country':''})
        fig.update_layout(coloraxis_showscale=False)
        show(fig,450)
    with c2:
        st.subheader('Distribution of observed values')
        fig=px.histogram(current,x=metric,nbins=32,color_discrete_sequence=['#45e2c0'],labels={metric:LABELS[metric]})
        show(fig,450)
with compare:
    st.subheader('Historical country trajectories')
    a,b=st.columns(2)
    with a: start=st.select_slider('Start year',options=years,value=years[max(0,len(years)-26)])
    with b: indexed=st.checkbox('Index to first observed year in selected range (100)',value=False)
    trend=data[data.country.isin(selected)&data.year.ge(start)&data[metric].notna()].copy()
    if trend.empty:
        st.info('Select countries with observations to compare historical trends.')
    else:
        value=metric
        if indexed:
            trend=trend.sort_values(['country','year'])
            baseline=trend.groupby('country')[metric].transform('first')
            trend=trend[baseline.ne(0)].copy()
            trend['index']=100*trend[metric]/baseline[baseline.ne(0)]
            value='index'
            st.caption('Each country is indexed to its first observed year in the selected range. Baseline years may differ across countries.')
        if not trend.empty:
            fig=px.line(trend,x='year',y=value,color='country',markers=True,color_discrete_sequence=COLORS,labels={value:'Index (100)' if indexed else LABELS[metric],'year':'Year'})
            show(fig,520)
            st.subheader('Reporting gaps and latest values')
            st.dataframe(trend.sort_values('year').groupby('country').tail(1)[['country','year',metric]].sort_values(metric,ascending=False),hide_index=True,use_container_width=True)
with relationships:
    st.subheader('Explore multi-indicator relationships')
    a,b,c=st.columns(3)
    with a: x=st.selectbox('Horizontal metric',list(LABELS),index=0,format_func=lambda x:LABELS[x],key='x')
    with b: y=st.selectbox('Vertical metric',list(LABELS),index=3,format_func=lambda x:LABELS[x],key='y')
    with c: logx=st.checkbox('Logarithmic X-axis',value=False)
    points=data[data.year.eq(year)].dropna(subset=[x,y]).copy()
    if x==y: st.info('Choose two distinct metrics.')
    elif len(points)<3: st.info('Fewer than three matched country-year observations. Try another year.')
    else:
        if logx: points=points[points[x].gt(0)]
        if len(points)<3: st.info('Insufficient strictly positive values for logarithmic X-axis.')
        else:
            corr=points[[x,y]].corr().iloc[0,1]
            st.caption(f'{len(points):,} matched countries · Pearson r = {corr:.3f} · Descriptive association, not causation')
            fig=px.scatter(points,x=x,y=y,hover_name='country',color_discrete_sequence=['#45e2c0'],
                           log_x=logx,labels={x:LABELS[x],y:LABELS[y]},opacity=.8)
            fig.update_traces(marker=dict(size=11,line=dict(width=1,color='#0c2032')))
            show(fig,520)
with momentum:
    st.subheader('Observed annual electricity-mix momentum')
    st.caption('Year-over-year percentage-point changes require observations in BOTH consecutive calendar years. No missing years are filled. CO₂ changes are in tonnes per person, not percentage points.')
    changes=adjacent_year_changes(data)
    paired=transition_quadrants(changes)
    annual=paired[paired.year.eq(year)].copy()
    if annual.empty:
        st.info('No countries have both renewable and fossil electricity shares reported in adjacent years for this year.')
    else:
        st.caption(f'{len(annual):,} countries with both observed adjacent-year share changes in {year}')
        scatter=px.scatter(annual,x='renewables_share_delta',y='fossil_share_delta',
                           color='transition_pattern',hover_name='country',
                           color_discrete_map={'Renewables up · fossil down':'#45e2c0',
                                               'Renewables down · fossil up':'#efc789',
                                               'Both shares up':'#8de0ff',
                                               'Both shares down':'#b8a0f8',
                                               'Mixed / unchanged':'#b9cddd'},
                           labels={'renewables_share_delta':'Renewables change (percentage points)',
                                   'fossil_share_delta':'Fossil change (percentage points)',
                                   'transition_pattern':'Observed pattern'},
                           custom_data=['year','co2_per_capita_delta'])
        scatter.add_hline(y=0,line_dash='dot',line_color='#8199ae')
        scatter.add_vline(x=0,line_dash='dot',line_color='#8199ae')
        scatter.update_traces(marker=dict(size=11,line=dict(width=1,color='#0c2032')))
        show(scatter,510)
        st.subheader('Observed transition patterns')
        pattern_counts=annual.groupby('transition_pattern',as_index=False).size().rename(columns={'size':'countries'})
        show(px.bar(pattern_counts,x='transition_pattern',y='countries',
                    color_discrete_sequence=['#45e2c0'],
                    labels={'transition_pattern':'Pattern','countries':'Countries'}),310)
        st.dataframe(annual[['country','iso3','year','renewables_share_delta',
                             'fossil_share_delta','co2_per_capita_delta','transition_pattern']]
                     .sort_values('renewables_share_delta',ascending=False),
                     use_container_width=True,hide_index=True)
        st.download_button('Download observed transition changes (CSV)',
                           annual.to_csv(index=False).encode(),
                           file_name=f'energy_transition_changes_{year}.csv',mime='text/csv')
    st.caption('Interpretation: changes in electricity generation shares are not changes in absolute generation; the non-fossil remainder includes nuclear and other sources. CO₂ per capita covers broader emissions and is not attributable to electricity alone.')

with quality:
    st.subheader('Data lineage & completeness')
    st.caption('Outer joins retain actual observed country-years. Missing values are not imputed or interpolated.')
    st.dataframe(coverage(data).rename(columns={'metric':'Indicator','country_years':'Reported country-years','countries':'Countries','first_year':'First year','last_year':'Last year'}),hide_index=True,use_container_width=True)
    st.subheader('Reporting coverage over time')
    byyear=data.groupby('year')[metric].count().reset_index(name='reporting_countries')
    fig=px.area(byyear,x='year',y='reporting_countries',color_discrete_sequence=['#45e2c0'],labels={'reporting_countries':'Reporting countries','year':'Year'})
    show(fig,290)
    st.subheader('Observed records and reproducible export')
    rows=data[data.year.eq(year)] if show_missing else current
    st.dataframe(rows[['country','iso3','year']+list(LABELS)],hide_index=True,use_container_width=True,height=350)
    st.download_button('Download selected-year observations (CSV)',rows.to_csv(index=False).encode(),file_name=f'energy_atlas_{year}.csv',mime='text/csv')
    st.caption('Sources: Our World in Data Grapher CSV (four series), World Bank GDP per-capita API. Coverage and row counts are computed from actual retrieved observations at runtime.')
