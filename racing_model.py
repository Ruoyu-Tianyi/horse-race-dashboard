"""Chronological, race-normalized predictions. Current-race odds are NOT features."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent
TRAIN_END = pd.Timestamp('2016-07-31')
CALIBRATION_END = pd.Timestamp('2016-12-31')
NUMERIC = [
    'draw_fraction', 'actual_weight', 'relative_weight', 'declared_horse_weight',
    'race_distance', 'field_size', 'horse_prior_starts', 'horse_prior_win_rate',
    'horse_prior_top3_rate', 'recent_form', 'last_form', 'days_since_last',
    'trainer_prior_win_rate', 'jockey_prior_win_rate', 'course_distance_rate',
    'weight_change', 'distance_change',
]
CATEGORICAL = ['race_course', 'race_class', 'track_condition', 'surface']
FEATURES = NUMERIC + CATEGORICAL


def load_sources():
    horses = pd.read_csv(ROOT / 'data/race-result-horse.csv', keep_default_na=False)
    races = pd.read_csv(ROOT / 'data/race-result-race.csv', keep_default_na=False)
    assert races.race_id.is_unique, 'Race IDs must be unique.'
    assert not horses.duplicated(['race_id', 'horse_id']).any()
    races['race_date'] = pd.to_datetime(races.race_date)
    races['race_distance'] = pd.to_numeric(races.race_distance)
    return horses, races


def prior_stats(frame, keys, prefix, strength=24):
    """Freeze all entity statistics before the race DAY, including jockey/trainer stats."""
    group_keys = keys + ['race_date']
    daily = frame.groupby(group_keys, sort=True, observed=True).agg(
        starts=('won', 'size'), wins=('won', 'sum'), top3=('top3', 'sum')
    ).reset_index().sort_values('race_date', kind='stable')
    grouping = daily.groupby(keys, sort=False, observed=True)
    for column in ['starts', 'wins', 'top3']:
        daily['prior_' + column] = grouping[column].cumsum() - daily[column]
    daily[prefix + '_prior_starts'] = daily.prior_starts
    daily[prefix + '_prior_win_rate'] = (daily.prior_wins + strength / 12) / (daily.prior_starts + strength)
    daily[prefix + '_prior_top3_rate'] = (daily.prior_top3 + strength / 4) / (daily.prior_starts + strength)
    columns = group_keys + [prefix + '_prior_starts', prefix + '_prior_win_rate', prefix + '_prior_top3_rate']
    return frame.merge(daily[columns], on=group_keys, how='left', validate='many_to_one')


def prepare_features(horses=None, races=None):
    if horses is None:
        horses, races = load_sources()
    frame = horses.merge(races.drop(columns=['incident_report', 'sectional_time', 'src']),
                         on='race_id', how='left', validate='many_to_one')
    assert frame.race_date.notna().all()
    frame['finish_rank'] = pd.to_numeric(frame.finishing_position.str.extract(r'^(\d+)')[0], errors='coerce')
    for column in ['win_odds', 'draw', 'actual_weight', 'declared_horse_weight', 'horse_number']:
        frame[column] = pd.to_numeric(frame[column], errors='coerce')
    # Retain starters that failed to finish as losses. Exclude withdrawals / no-part records.
    started = frame.finish_rank.notna() | frame.finishing_position.isin(['PU', 'UR', 'FE', 'DNF', 'DISQ'])
    frame = frame.loc[started & frame.win_odds.gt(0) & frame.draw.gt(0)].copy()
    frame['won'] = frame.finish_rank.eq(1).astype(int)
    frame['top3'] = frame.finish_rank.le(3).astype(int)
    frame['field_size'] = frame.groupby('race_id').horse_id.transform('size')
    frame['form_score'] = ((frame.finish_rank - 1) / (frame.field_size - 1)).clip(0, 1).fillna(1)
    frame['surface'] = np.where(frame.track.str.contains('ALL WEATHER', case=False), 'All weather', 'Turf')
    frame['draw_fraction'] = frame.draw / frame.field_size
    frame['relative_weight'] = frame.actual_weight - frame.groupby('race_id').actual_weight.transform('mean')
    frame = prior_stats(frame, ['horse_id'], 'horse')
    frame = prior_stats(frame, ['trainer'], 'trainer', strength=60)
    frame = prior_stats(frame, ['jockey'], 'jockey', strength=60)
    frame = prior_stats(frame, ['horse_id', 'race_course', 'race_distance'], 'course_distance')
    frame['course_distance_rate'] = frame.course_distance_prior_win_rate
    frame = frame.sort_values(['race_date', 'race_number', 'horse_id'], kind='stable').reset_index(drop=True)
    assert not frame.duplicated(['horse_id', 'race_date']).any(), 'Horse history requires one start per day.'
    horse_groups = frame.groupby('horse_id', sort=False)
    frame['last_form'] = horse_groups.form_score.shift(1)
    frame['recent_form'] = horse_groups.form_score.transform(lambda values: values.shift(1).rolling(5, min_periods=1).mean())
    frame['days_since_last'] = horse_groups.race_date.diff().dt.days
    frame['weight_change'] = horse_groups.declared_horse_weight.diff()
    frame['distance_change'] = horse_groups.race_distance.diff()
    # History may contain dead heats; model/evaluation only uses unambiguous single-winner races.
    winner_count = frame.groupby('race_id').won.transform('sum')
    frame['eligible'] = winner_count.eq(1) & frame.field_size.ge(4)
    return frame


def normalized_probability(scores, race_ids, temperature=1.0):
    series = pd.Series(np.clip(np.asarray(scores), 1e-9, 1) ** (1 / temperature), index=race_ids.index)
    return series / series.groupby(race_ids).transform('sum')


def evaluate(frame, probability_column):
    ordered = frame.sort_values([probability_column, 'horse_id'], ascending=[False, True], kind='stable')
    picks = ordered.groupby('race_id', sort=False).head(1)
    winners = frame.loc[frame.won.eq(1)]
    return {
        'races': int(frame.race_id.nunique()),
        'top1_hits': int(picks.won.sum()),
        'top1_accuracy': float(picks.won.mean()),
        'top3_coverage': float(ordered.groupby('race_id').head(3).won.sum() / frame.race_id.nunique()),
        'log_loss': float(-np.log(winners[probability_column].clip(1e-9)).mean()),
        'brier': float(((frame[probability_column] - frame.won) ** 2).mean()),
    }


def build_artifacts():
    horses, races = load_sources()
    frame = prepare_features(horses, races)
    eligible = frame.loc[frame.eligible].copy()
    train = eligible.loc[eligible.race_date.le(TRAIN_END)]
    calibration = eligible.loc[eligible.race_date.gt(TRAIN_END) & eligible.race_date.le(CALIBRATION_END)]
    test = eligible.loc[eligible.race_date.gt(CALIBRATION_END)].copy()
    processor = ColumnTransformer([
        ('numeric', SimpleImputer(strategy='median', add_indicator=True), NUMERIC),
        ('category', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL),
    ])
    # No random internal validation split; all fitted rows precede calibration/test dates.
    model = make_pipeline(processor, HistGradientBoostingClassifier(
        max_iter=140, max_leaf_nodes=9, min_samples_leaf=65,
        learning_rate=0.055, l2_regularization=8, early_stopping=False, random_state=7,
    ))
    model.fit(train[FEATURES], train.won)
    calibration_raw = model.predict_proba(calibration[FEATURES])[:, 1]
    candidates = np.linspace(0.7, 2.3, 65)
    losses = []
    for temperature in candidates:
        probability = normalized_probability(calibration_raw, calibration.race_id, temperature)
        losses.append(float(-np.log(probability.loc[calibration.won.eq(1)]).mean()))
    temperature = float(candidates[int(np.argmin(losses))])
    test['model_probability'] = normalized_probability(model.predict_proba(test[FEATURES])[:, 1], test.race_id, temperature)
    market_score = 1 / test.win_odds
    test['market_probability'] = market_score / market_score.groupby(test.race_id).transform('sum')
    test['uniform_probability'] = 1 / test.field_size
    test['probability_gap'] = test.model_probability - test.market_probability
    test['model_rank'] = test.groupby('race_id').model_probability.rank(method='first', ascending=False).astype(int)
    test['market_rank'] = test.groupby('race_id').market_probability.rank(method='first', ascending=False).astype(int)
    selected_columns = [
        'race_id', 'race_date', 'race_course', 'race_number', 'race_class', 'race_distance',
        'track_condition', 'surface', 'race_name', 'horse_id', 'horse_name', 'horse_number',
        'jockey', 'trainer', 'draw', 'actual_weight', 'declared_horse_weight',
        'finishing_position', 'finish_rank', 'won', 'field_size', 'win_odds',
        'model_probability', 'market_probability', 'probability_gap', 'model_rank',
        'market_rank', 'horse_prior_starts', 'horse_prior_win_rate', 'recent_form',
        'days_since_last', 'jockey_prior_win_rate', 'trainer_prior_win_rate',
    ]
    artifact_dir = ROOT / 'artifacts'
    artifact_dir.mkdir(exist_ok=True)
    test[selected_columns].to_csv(artifact_dir / 'predictions.csv', index=False, float_format='%.9f')
    history_columns = ['race_date', 'race_id', 'horse_id', 'race_course', 'race_distance',
                       'finishing_position', 'finish_rank', 'jockey', 'trainer', 'field_size']
    frame[history_columns].to_csv(artifact_dir / 'horse_history.csv', index=False)
    models = {
        'Form model': evaluate(test, 'model_probability'),
        'Closing market': evaluate(test, 'market_probability'),
        'Uniform': evaluate(test, 'uniform_probability'),
    }
    monthly = []
    for month, group in test.groupby(test.race_date.dt.to_period('M')):
        for label, column in [('Form model', 'model_probability'), ('Closing market', 'market_probability')]:
            monthly.append({'month': str(month), 'model': label, **evaluate(group, column)})
    exclusions = horses.finishing_position.value_counts().to_dict()
    metadata = {
        'data_source': 'https://www.kaggle.com/datasets/lantanacamara/hong-kong-horse-racing',
        'source_rows': {'horse': len(horses), 'race': len(races)},
        'source_period': [races.race_date.min().strftime('%Y-%m-%d'), races.race_date.max().strftime('%Y-%m-%d')],
        'train_period': [train.race_date.min().strftime('%Y-%m-%d'), train.race_date.max().strftime('%Y-%m-%d')],
        'calibration_period': [calibration.race_date.min().strftime('%Y-%m-%d'), calibration.race_date.max().strftime('%Y-%m-%d')],
        'test_period': [test.race_date.min().strftime('%Y-%m-%d'), test.race_date.max().strftime('%Y-%m-%d')],
        'train_races': int(train.race_id.nunique()), 'calibration_races': int(calibration.race_id.nunique()),
        'test_races': int(test.race_id.nunique()), 'temperature': temperature,
        'eligible_races': int(eligible.race_id.nunique()),
        'excluded_races': int(races.race_id.nunique() - eligible.race_id.nunique()),
        'eligible_starts': len(eligible), 'position_codes': exclusions,
        'features': FEATURES, 'metrics': models, 'monthly': monthly,
        'source_hashes': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (ROOT / 'data').glob('*.csv')},
        'caveats': [
            'Historical replay only; no current entries or live odds are connected.',
            'Current-race odds, finish times, running positions and results are excluded from model features.',
            'Entity statistics are frozen before each race day; earlier test-day results can inform later days, never earlier predictions.',
            'The model is frozen after July 2016; temperature is chosen only on September–December 2016.',
            'Market probabilities normalize reciprocal historical win_odds within each race. Odds timestamp is unavailable.',
            'Probability gap is a model–market disagreement, not expected profit or a calibrated return forecast.',
            'Withdrawals/no-part/unknown starters are removed. Known non-finishers remain losses. First-place dead-heat races are excluded.',
            'No dividends, fees or executable pre-bet odds: no bankroll, ROI or profit claims are calculated.',
        ],
    }
    (artifact_dir / 'model_report.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'metrics': models, 'temperature': temperature, 'splits': [metadata['train_races'], metadata['calibration_races'], metadata['test_races']]}, indent=2))
    return test, metadata


if __name__ == '__main__':
    build_artifacts()
