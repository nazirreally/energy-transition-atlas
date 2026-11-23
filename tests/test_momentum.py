import pandas as pd
import pytest
from src.momentum import adjacent_year_changes, transition_quadrants


def sample():
    return pd.DataFrame([
        dict(iso3='PAK', country='Pakistan', year=2020, renewables_share=20., fossil_share=70., co2_per_capita=1.0),
        dict(iso3='PAK', country='Pakistan', year=2021, renewables_share=25., fossil_share=64., co2_per_capita=0.9),
        dict(iso3='PAK', country='Pakistan', year=2023, renewables_share=30., fossil_share=60., co2_per_capita=0.8),
        dict(iso3='DEU', country='Germany', year=2021, renewables_share=40., fossil_share=45., co2_per_capita=7.0),
        dict(iso3='DEU', country='Germany', year=2022, renewables_share=39., fossil_share=46., co2_per_capita=None),
    ])


def test_adjacent_changes_are_correct_and_no_gap_interpolation():
    result = adjacent_year_changes(sample())
    p = result[(result.iso3 == 'PAK') & (result.year == 2021)].iloc[0]
    assert p.renewables_share_delta == 5
    assert p.fossil_share_delta == -6
    assert p.co2_per_capita_delta == pytest.approx(-.1)
    assert result[(result.iso3 == 'PAK') & (result.year == 2023)].renewables_share_delta.isna().all()


def test_first_year_and_missing_values_stay_missing():
    result = adjacent_year_changes(sample())
    assert result[(result.iso3 == 'DEU') & (result.year == 2021)].fossil_share_delta.isna().all()
    assert result[(result.iso3 == 'DEU') & (result.year == 2022)].co2_per_capita_delta.isna().all()


def test_quadrants_classify_without_imputation():
    result = transition_quadrants(adjacent_year_changes(sample()))
    assert len(result) == 2
    assert result[result.iso3 == 'PAK'].transition_pattern.iloc[0] == 'Renewables up · fossil down'
    assert result[result.iso3 == 'DEU'].transition_pattern.iloc[0] == 'Renewables down · fossil up'


def test_duplicate_keys_rejected():
    frame = sample()
    with pytest.raises(ValueError, match='Duplicate'):
        adjacent_year_changes(pd.concat([frame, frame.iloc[[0]]]))


def test_invalid_year_and_missing_columns_rejected():
    with pytest.raises(ValueError, match='Year'):
        adjacent_year_changes(sample().assign(year=lambda x: x.year.astype(float)))
    with pytest.raises(ValueError, match='Missing'):
        adjacent_year_changes(sample().drop(columns='fossil_share'))


def test_nonfinite_measure_rejected():
    frame = sample()
    frame.loc[0, 'co2_per_capita'] = float('inf')
    with pytest.raises(ValueError, match='Nonfinite'):
        adjacent_year_changes(frame)
