# Team 11 · 馬場風雲 / RACE EDGE

**Horse-racing predictions and odds comparison, designed as a historical research terminal.**

Team members: **Zhou Tianyi; Xu Yiming; Zhang Zai; Xu Mohan**.

Repository: [Ruoyu-Tianyi/horse-race-dashboard](https://github.com/Ruoyu-Tianyi/horse-race-dashboard).

The app compares an independent historical-form model with recorded market prices. This **Hong Kong Neon** design branch uses traditional Chinese sign lettering, lacquer red, bright gold, neon glow, coin-shaped runner numbers and an illustrated adult equestrian host with a racehorse. Gold bars show model probabilities; pink diamonds show the historical market benchmark. All predictions shown are out-of-time **historical replay**, not current betting advice or live prices.

**Branch:** `design/hong-kong-neon`. The original design remains on `main`. The visual redesign preserves the three headline metrics, two supporting charts, race filters, model validation and team attribution required by the assignment. On narrow screens, the hero copy moves below the portrait; the interface uses no flashing animation. The artwork is bundled in the repository and needs no external image service or API key at runtime. See [artwork and design notes](assets/DESIGN.md) for provenance and the generation prompt.

The red-and-gold theme extends across the full dashboard, including illuminated KPI panels, ranking ribbons, charts, tables, filters and action buttons. Heavy condensed **Teko** numerals are bundled locally with their open-font licence, with slanted and embossed styling for prominent values.

## Step 1 — Dataset and decision-maker

**Dataset:** [Hong Kong Horse Racing Results 2014–17 Seasons, Lantana Camara, Kaggle](https://www.kaggle.com/datasets/lantanacamara/hong-kong-horse-racing).

The dataset page credits data scraped from **The Hong Kong Jockey Club (HKJC)**; these are real historical race observations rather than a teaching or synthetic dataset. The supplied files match its filenames, size and sample records. The page's older description mentions 2014–16 and 1,561 races, while its latest title covers 2014–17; the actual supplied snapshot extends to **2017-07-16** and is the controlling source for this project's coverage. The page lists its licence as **Unknown** and its update frequency as **Not specified**. The collection process has not been independently audited. Source hashes are in `artifacts/model_report.json`.

| File | Grain | Rows | Columns |
|---|---|---:|---:|
| `race-result-horse.csv` | One horse's entry/result in one race; includes withdrawals | 30,189 | 19 |
| `race-result-race.csv` | One race | 2,367 | 12 |

Period: **14 September 2014–16 July 2017**. Courses: Sha Tin and Happy Valley. Join key: `race_id`, with a many-to-one validation. All horse records match a race; no duplicate horse–race keys or duplicate race IDs were found.

The raw CSVs total approximately **8.4 MiB**, each below 25 MB. The application reads **one compact derived CSV**, `artifacts/predictions.csv`, rather than joining the long incident narratives into every row. Raw files remain in `data/` for reproducibility; no rows were randomly sampled. Only the independent 2017 evaluation period is exposed for prediction replay. `horse_history.csv` supports optional runner detail.

**One decision-maker:** an adult race-betting researcher comparing runners before each race. This role repeatedly decides which horses merit further research and which races to pass over. A watchlist records research candidates; it does not execute wagers.

## Step 2 — Why this dashboard?

1. **Who and how often?** The same researcher opens it when evaluating each race, revisiting the current field and shortlisted runners before making a decision. Historical validation is reviewed weekly and after model changes.
2. **Decision sentence:** “If the researcher sees a meaningful disagreement between model probability and the historical market baseline, they will inspect the runner's prior form and field context, then either add it to a research watchlist or pass on the race.” A positive gap alone never triggers a wager or a profit claim.
3. **Without it:** the researcher must move between result tables, horse histories and prices, manually match runners and compare inconsistent figures. This duplicates work and increases the chance of mixing race dates, using a stale price, or overlooking weak historical coverage. These are a proposed workflow and plausible costs; this dataset does not measure minutes or money saved.
4. **Why a dashboard instead of an email/report/alert?** Each race has a different field. Course/date/race filters and runner inspection let the same user answer the same questions for many races. A weekly email cannot support that selection workflow; a one-off report is appropriate for model review but not repeated runner lookup. A stale-price alert would complement the dashboard in production, rather than replace the comparison view.

## Step 3 — EDA, selection and page order

The executed [EDA notebook](notebooks/01_eda_and_validation.ipynb) uses **Pandas and Matplotlib** to inspect shape, data types, placeholder missingness, join integrity, result-code distributions, distance and monthly coverage, odds relationships, and independent validation.

### Exactly three headline metrics

All three refer to the **model's top-ranked horse in the selected race**:

| KPI | Definition | Why shown |
|---|---|---|
| Model win probability | Model score normalized across all starters after temperature calibration | Shows the model's strongest candidate and how uncertain it remains |
| Recorded historical win odds | The supplied `win_odds` for that candidate | Gives pricing context; timestamp and executability are unavailable |
| Model–market gap, percentage points | Model probability minus `(1/odds) / sum(1/odds)` within the race | Locates disagreement for further investigation; **not** expected return |

**Supporting charts:** one chart on the prediction tab compares all runners' model probabilities (bars) with normalized market probabilities (diamonds). One chart on the validation tab compares monthly top-pick hit rates for the fixed model and historical market favourite. There are **two supporting charts in total**. Validation summary is a small table, not another KPI row.

**Filters:** course, actual race date, and race number. These identify the race the researcher is investigating. A result-reveal toggle supports honest historical replay. A runner selector opens prior form. Global validation is explicitly labelled as all held-out races, so the single-race filters do not silently redefine its denominator.

### What we deliberately excluded

1. **Raw finish-time leaderboards:** race distances, surfaces and conditions differ. A pooled ranking would confuse race context with ability and does not support the repeated decision.
2. **Profit, ROI, expected payout and bankroll projections:** executable pre-race prices, full dividends, fees and timing are unavailable. Such panels would create unsupported financial precision.
3. **Full incident narratives and every sectional position:** long text and structurally absent later sections would crowd out the comparison. These can be investigated in the source, but are not headline information.

### Misleading-data risks and handling

- Result codes are strings, including withdrawals, no-part, non-finishers and dead heats. Numeric ranks are parsed without deleting known non-finisher losses. Withdrawals/no-part/unknown starters are excluded; **six first-place dead-heat races** are excluded from modelling and evaluation. Dead heats in lower places are retained as tied numerical ranks.
- `NA`, `-`, `---` and blank strings require explicit conversion. Late running-position columns are often structurally absent in shorter races and are excluded from prediction.
- Training history begins in September 2014, so earlier career form is unknown. New horses use smoothed historical priors rather than a fabricated complete career record.
- August has no observations; partial first/last months and seasonal gaps must not be interpreted as zero performance. The notebook shows coverage gaps explicitly.
- Popular horses are not equally likely to win. Historical market odds form a strong baseline and are compared with the model rather than hidden.
- Outcomes in the selected race are hidden by default. Features use dates strictly before the race day, including trainer/jockey statistics. The result-reveal toggle and matching CSV export make hindsight visible.
- The data ends in 2017. The title-area caption and sidebar identify historical replay and distinguish proposed refresh cadence from an actual live feed.
- Probabilities are estimates; no calibrated uncertainty interval is available. The screen does not turn probability gaps into a certainty rating or guaranteed-return claim.

### Sketch and hierarchy

The pre-implementation layout is saved in [assets/wireframe.svg](assets/wireframe.svg).

1. **Top:** team title, one-line audience/decision caption, selected race context, data period/refresh line, then the three immediate headline values.
2. **Middle:** a whole-field probability comparison alongside a three-runner shortlist. Both explain the headline candidate in the context of competitors.
3. **Bottom:** runner records, scoped CSV export, prior form and an optional watchlist action. Details are for users who actually need to investigate.
4. **Secondary tab:** independent model validation and a single trend chart. This keeps model assessment available without displacing race-by-race research.

If an element does not help identify the field, compare estimates, assess evidence or inspect a runner, it is excluded.

## Step 4 — Refresh and action policy

The current CSV is a **frozen snapshot**, and the app does **not** automatically refresh or connect to a betting feed.

Proposed production design, subject to a licensed feed and its limits:

- **Results/history:** ingest after official result confirmation. Update historical features before the next race day. Model retraining is a separate weekly process requiring fresh chronological validation before replacing the model.
- **Entries:** ingest confirmed racecards when published, then process official scratching changes before using field-normalized probabilities.
- **Prices:** poll pre-race odds every **60 seconds**. Prices can change during the decision window, so a monthly or daily snapshot would be too stale for price comparison. Faster updates have cost and feed constraints; this is a design choice, not a measured optimum.
- **Human review:** inspect during race selection and recheck immediately before a decision. Review weekly held-out performance separately. Data refresh and human review need not occur at the same frequency.
- **One action trigger:** track **price age**. If the latest quote is more than **120 seconds old**, suspend the probability-gap comparison and flag a data-quality problem. The two-minute limit is a proposed service threshold of two missed refreshes, not an empirically optimized betting signal. It does not imply that newer prices guarantee availability.
- **Cost of stale data:** stale odds may reverse an apparent comparison; missing scratches change the field denominator; unconfirmed results contaminate future historical features. A day of stale prices makes a race-specific price comparison unusable. A week of stale historical results misses recent form and weakens the comparison.

The dashboard displays both the **actual data period** and the **intended production refresh cadence**, as required.

## Model and independent validation

The model is a small gradient-boosted classifier. Features include prior horse form, smoothed prior trainer/jockey rates, course/distance history, draw, carried weight, horse weight and entry context. Current-race odds, outcomes, finish times and sectional positions are never model inputs.

- Training: **2014-09-14–2016-07-10**, 1,557 eligible races.
- Calibration: **2016-09-03–2016-12-27**, 295 eligible races. Only this window selects a probability-temperature parameter.
- Independent evaluation: **2017-01-01–2017-07-16**, 509 eligible races.
- A fixed model is replayed chronologically. Historical features may incorporate completed earlier evaluation days, which is available information at each later day; they never use current-day or future outcomes.

| Method | Top-pick wins | Top-pick hit rate | Top-three coverage | Race-level log loss ↓ |
|---|---:|---:|---:|---:|
| Historical-form model | 128 / 509 | 25.1% | 55.0% | 2.202 |
| Historical market favourite | 148 / 509 | 29.1% | 63.3% | 1.991 |

These results **do not support claiming that the model beats the market**. “Top-three coverage” means the actual winner is among the three highest-ranked runners, not a PLACE-bet success rate. Ties in top-pick probabilities/odds use `horse_id` as a deterministic tie-break. No profit is calculated.

## Step 5 — Run and deploy

This project was initialized with **`uv init`** and is verified under **Python 3.14**. The app consumes committed prediction artifacts, so Cloud startup does not retrain a model.

```powershell
uv sync --group dev
uv run streamlit run app.py
```

Reproduce the model, notebook and meaningful checks:

```powershell
uv run python racing_model.py
uv run python create_notebook.py
uv run python verify.py
```

The notebook generator uses a project-local Jupyter kernel and saves executed outputs. `uv.lock` records the resolved environment. `requirements.txt` supports a minimal application installation.

**Streamlit Community Cloud deployment settings:**

- Repository: `Ruoyu-Tianyi/horse-race-dashboard`
- Branch: `design/hong-kong-neon` (use `main` for the original design)
- Main file path: `app.py`
- Advanced settings → Python version: **3.14**
- Deploy from [Streamlit Community Cloud](https://share.streamlit.io/), following the [official deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Submission

The assignment requires **everyone to submit individually** on Canvas, with their **own deployed app, repository and README**, even when the dataset and group discussion are shared. This repository belongs to its account owner; other members should create and adapt their own repositories and deployments.

Submit the verified deployed application URL and your own GitHub repository URL. The local development URL is not a deployed submission URL.
