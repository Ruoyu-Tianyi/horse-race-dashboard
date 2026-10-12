"""Meaningful model-integrity and user-flow checks; run with `uv run python verify.py`."""
import json
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from racing_model import ROOT, FEATURES, load_sources, prepare_features, evaluate

predictions = pd.read_csv(ROOT / 'artifacts/predictions.csv', parse_dates=['race_date'])
report = json.loads((ROOT / 'artifacts/model_report.json').read_text(encoding='utf-8'))
assert predictions.groupby('race_id').won.sum().eq(1).all()
assert np.allclose(predictions.groupby('race_id').model_probability.sum(), 1, atol=1e-7)
assert np.allclose(predictions.groupby('race_id').market_probability.sum(), 1, atol=1e-7)
assert predictions.model_probability.between(0,1).all()
assert predictions.race_date.min() > pd.Timestamp(report['calibration_period'][1])
observed = evaluate(predictions, 'model_probability')
for key, value in observed.items():
    assert np.isclose(value, report['metrics']['Form model'][key])
assert not set(FEATURES) & {'won','win_odds','finish_time','finishing_position','finish_rank','running_position_1'}

# Changing all outcomes on/after a date must never alter features on/before that date.
horses, races = load_sources()
before = prepare_features(horses, races)
boundary = pd.Timestamp('2017-03-05')
perturbed = horses.copy()
future_race_ids = races.loc[races.race_date.ge(boundary), 'race_id']
change = perturbed.race_id.isin(future_race_ids) & perturbed.finishing_position.str.match(r'^\d+')
perturbed.loc[change, 'finishing_position'] = '7'
after = prepare_features(perturbed, races)
keys = ['race_id','horse_id']
a = before.loc[before.race_date.le(boundary)].set_index(keys)[FEATURES].sort_index()
b = after.loc[after.race_date.le(boundary)].set_index(keys)[FEATURES].sort_index()
pd.testing.assert_frame_equal(a,b)
print('PASS: probabilities, report reconciliation, chronological splits, same-day/future outcome leakage')

app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=40)
assert not app.exception
assert len(app.metric) == 3
assert '真实名次' not in app.dataframe[0].value.columns
assert len(app.get('plotly_chart')) == 2
app.sidebar.selectbox[0].select('Happy Valley').run(timeout=40)
assert not app.exception
assert app.sidebar.selectbox[0].value == 'Happy Valley'
selected_race = app.sidebar.selectbox[2].value
selected_field = predictions.loc[predictions.race_id.eq(selected_race)].sort_values('model_rank')
assert len(app.dataframe[0].value) == len(selected_field)
assert app.metric[0].value == f'{selected_field.iloc[0].model_probability:.1%}'
app.sidebar.toggle[0].set_value(True).run(timeout=40)
assert '真实名次' in app.dataframe[0].value.columns
assert not app.exception
app.button[0].click().run(timeout=40)
assert len(app.session_state['watchlist']) == 1
print('PASS: page load, three KPIs, two charts, race/course filters, result reveal, watchlist')
