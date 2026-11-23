"""Observed adjacent-year energy transition diagnostics, without interpolation."""
from __future__ import annotations
import pandas as pd

FIELDS = ('renewables_share', 'fossil_share', 'co2_per_capita')


def adjacent_year_changes(panel: pd.DataFrame) -> pd.DataFrame:
    """Calculate exact adjacent-year changes, preserving missing values."""
    required = {'iso3', 'country', 'year', *FIELDS}
    if not required.issubset(panel.columns):
        raise ValueError(f'Missing columns: {sorted(required - set(panel.columns))}')
    if panel.duplicated(['iso3', 'year']).any():
        raise ValueError('Duplicate ISO3-year keys')
    if panel['year'].isna().any() or not pd.api.types.is_integer_dtype(panel['year']):
        raise ValueError('Year must be a non-null integer')
    for field in FIELDS:
        values = pd.to_numeric(panel[field], errors='coerce')
        if values.notna().any() and not values.dropna().map(
            lambda v: float('-inf') < v < float('inf')
        ).all():
            raise ValueError(f'Nonfinite observations in {field}')
    data = panel.sort_values(['iso3', 'year']).copy()
    prev_year = data.groupby('iso3', sort=False)['year'].shift()
    adjacent = data['year'].sub(prev_year).eq(1)
    for field in FIELDS:
        previous = data.groupby('iso3', sort=False)[field].shift()
        data[field + '_delta'] = (data[field] - previous).where(
            adjacent & data[field].notna() & previous.notna()
        )
    cols = ['iso3', 'country', 'year'] + [f + '_delta' for f in FIELDS]
    return data[cols].reset_index(drop=True)


def transition_quadrants(changes: pd.DataFrame) -> pd.DataFrame:
    """Classify paired observed electricity-share shifts; ties remain mixed."""
    fields = ['renewables_share_delta', 'fossil_share_delta']
    if not set(fields).issubset(changes):
        raise ValueError('Missing share change columns')
    result = changes.dropna(subset=fields).copy()
    r, f = result[fields[0]], result[fields[1]]
    result['transition_pattern'] = 'Mixed / unchanged'
    result.loc[r.gt(0) & f.lt(0), 'transition_pattern'] = 'Renewables up · fossil down'
    result.loc[r.lt(0) & f.gt(0), 'transition_pattern'] = 'Renewables down · fossil up'
    result.loc[r.gt(0) & f.gt(0), 'transition_pattern'] = 'Both shares up'
    result.loc[r.lt(0) & f.lt(0), 'transition_pattern'] = 'Both shares down'
    return result
