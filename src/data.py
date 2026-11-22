"""Observed-only, source-explicit multi-publisher energy integration."""
from __future__ import annotations
import io
import pandas as pd
import requests
import pycountry

# Public Grapher CSVs; no bundled or synthetic analytical data.
OWID = {
    'renewables_share': 'https://ourworldindata.org/grapher/electricity-mix.csv?v=1&csvType=full&useColumnShortNames=false&frequency=annual&metric=share_of_generation&source=renewables',
    'fossil_share': 'https://ourworldindata.org/grapher/electricity-mix.csv?v=1&csvType=full&useColumnShortNames=false&frequency=annual&metric=share_of_generation&source=fossil',
    'electricity_demand': 'https://ourworldindata.org/grapher/electricity-mix.csv?v=1&csvType=full&useColumnShortNames=false&frequency=annual&metric=demand&source=total',
    'co2_per_capita': 'https://ourworldindata.org/grapher/co-emissions-per-capita.csv',
}
WB = 'https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.CD'


def fetch_grapher(metric: str, session=requests) -> pd.DataFrame:
    if metric not in OWID:
        raise ValueError('Unknown published indicator')
    response = session.get(OWID[metric], timeout=75)
    response.raise_for_status()
    df = pd.read_csv(io.BytesIO(response.content))
    required = {'Entity', 'Code', 'Year'}
    if not required.issubset(df.columns):
        raise ValueError(f'Unexpected Grapher schema: {metric}')
    values = [c for c in df if c not in required]
    if len(values) != 1:
        raise ValueError(f'Ambiguous Grapher value field: {metric}')
    df = df.rename(columns={'Entity':'country','Code':'iso3','Year':'year',values[0]:metric})
    df = df[['iso3','country','year',metric]].copy()
    df = df[df.iso3.astype('string').str.fullmatch('[A-Z]{3}',na=False)].copy()
    # OWID regional aggregates can have 3-letter codes: accept only ISO 3166 countries.
    valid = {country.alpha_3 for country in pycountry.countries}
    df = df[df.iso3.isin(valid)].copy()
    df['year'] = pd.to_numeric(df.year, errors='coerce')
    df[metric] = pd.to_numeric(df[metric], errors='coerce')
    df = df.dropna(subset=['year',metric])
    df['year'] = df.year.astype(int)
    if df.empty or df.duplicated(['iso3','year']).any():
        raise ValueError(f'Empty or duplicate observed series: {metric}')
    return df


def fetch_world_bank(session=requests) -> pd.DataFrame:
    records = []
    page = 1
    while True:
        response = session.get(WB, params={'format':'json','per_page':20000,'page':page,'date':'1990:2026'}, timeout=75)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload,list) or len(payload)!=2 or not isinstance(payload[0],dict):
            raise ValueError('Unexpected World Bank JSON contract')
        records.extend(payload[1] or [])
        if page >= int(payload[0]['pages']):
            break
        page += 1
    df = pd.DataFrame([{'iso3':r.get('countryiso3code'),'year':r.get('date'),'gdp_per_capita':r.get('value')}
                       for r in records if r.get('value') is not None])
    if df.empty:
        raise ValueError('World Bank GDP observations unavailable')
    valid = {country.alpha_3 for country in pycountry.countries}
    df = df[df.iso3.isin(valid)].copy()
    df['year'] = pd.to_numeric(df.year,errors='coerce')
    df['gdp_per_capita'] = pd.to_numeric(df.gdp_per_capita,errors='coerce')
    df = df.dropna(subset=['year','gdp_per_capita'])
    df['year'] = df.year.astype(int)
    if df.empty or df.duplicated(['iso3','year']).any():
        raise ValueError('World Bank data has empty/duplicate keys')
    return df


def build_panel(series: dict[str,pd.DataFrame], wb: pd.DataFrame) -> pd.DataFrame:
    """Outer join retains real observations; missing publisher data stays missing."""
    if set(series) != set(OWID):
        raise ValueError('Missing required publisher series')
    merged = None
    for key in OWID:
        part = series[key]
        if part.duplicated(['iso3','year']).any():
            raise ValueError(f'Duplicate keys in {key}')
        if merged is None:
            merged = part.copy()
        else:
            merged = merged.merge(part[['iso3','year',key]],on=['iso3','year'],how='outer',validate='one_to_one')
    if wb.duplicated(['iso3','year']).any():
        raise ValueError('Duplicate World Bank keys')
    merged = merged.merge(wb,on=['iso3','year'],how='outer',validate='one_to_one')
    names = pd.concat([x[['iso3','country']] for x in series.values()]).drop_duplicates('iso3')
    merged = merged.drop(columns=['country']).merge(names,on='iso3',how='left',validate='many_to_one')
    return merged.sort_values(['country','year']).reset_index(drop=True)


def latest_observed(panel: pd.DataFrame, metric: str, year: int) -> pd.DataFrame:
    return panel.loc[panel.year.eq(year) & panel[metric].notna()].copy()


def coverage(panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([{'metric':k,'country_years':int(panel[k].notna().sum()),
                          'countries':int(panel.loc[panel[k].notna(),'iso3'].nunique()),
                          'first_year':int(panel.loc[panel[k].notna(),'year'].min()) if panel[k].notna().any() else None,
                          'last_year':int(panel.loc[panel[k].notna(),'year'].max()) if panel[k].notna().any() else None}
                         for k in list(OWID)+['gdp_per_capita']])
