import pandas as pd
import pytest
from src.data import OWID, build_panel, coverage, latest_observed


def observed_fixture():
    # Tiny deterministic fixture ONLY for unit tests, never used by dashboard or exports.
    keys=[('PAK','Pakistan',2020),('PAK','Pakistan',2021),('DEU','Germany',2021)]
    series={k:pd.DataFrame([{'iso3':iso,'country':country,'year':year,k:float(i+1)} for i,(iso,country,year) in enumerate(keys)]) for k in OWID}
    wb=pd.DataFrame([{'iso3':'PAK','year':2021,'gdp_per_capita':1500.}])
    return series,wb


def test_outer_join_preserves_observed_and_missing_values():
    series,wb=observed_fixture()
    panel=build_panel(series,wb)
    assert len(panel)==3
    assert panel.loc[panel.year.eq(2020),'gdp_per_capita'].isna().all()
    assert panel.loc[panel.iso3.eq('PAK')&panel.year.eq(2021),'gdp_per_capita'].iloc[0]==1500


def test_duplicate_country_year_rejected():
    series,wb=observed_fixture()
    series['renewables_share']=pd.concat([series['renewables_share'],series['renewables_share'].iloc[[0]]])
    with pytest.raises(ValueError,match='Duplicate'):
        build_panel(series,wb)


def test_missing_publisher_series_rejected():
    series,wb=observed_fixture()
    del series['fossil_share']
    with pytest.raises(ValueError,match='Missing'):
        build_panel(series,wb)


def test_coverage_reports_only_non_null_observations():
    series,wb=observed_fixture()
    result=coverage(build_panel(series,wb))
    assert result.loc[result.metric.eq('gdp_per_capita'),'country_years'].iloc[0]==1


def test_latest_year_filter_is_exact():
    series,wb=observed_fixture()
    result=latest_observed(build_panel(series,wb),'gdp_per_capita',2020)
    assert result.empty


def test_sources_are_https_and_distinct():
    assert len(set(OWID.values()))==4
    assert all(url.startswith('https://ourworldindata.org/grapher/') for url in OWID.values())
