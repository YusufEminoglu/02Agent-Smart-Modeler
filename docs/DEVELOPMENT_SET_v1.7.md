# 02Agent Smart Modeler — Development Set for v1.7.0

**Goal: more people install it, and a first-time user gets a working
workflow in the first two minutes.** Written 2026-10-26 from measured
evidence. Items that do not remove a real adoption barrier are listed in §4,
not built.

## 0. Baseline (measured 2026-10-26)

| Signal | Value | Source |
|---|---|---|
| Hub downloads | **2,350** in 73 days (since 2026-08-14) | `plugins.xml?qgis=3.44` |
| Sibling plugin, same family, same age | 02Agent OSM Downloader **13,597** | same |
| Hub version | 1.6.0 = local | `pf status --hub` |
| Minimum QGIS | **3.44** (`qgisMinimumVersion`) | `metadata.txt` |
| Code | 32 k lines (Python, excl. tests); 59 test files | `git ls-files` |
| Starter workflows | 15, in a small list under the node palette | `resources/micro_packages.json` |

A plugin of this depth at one sixth of its sibling's downloads is a
discovery-and-first-run problem, not a capability problem.

## 1. Adoption barriers found by reading the plugin

1. **The Hub page sells architecture, not outcomes.** Description: "typed
   graphs, validated AI planning, smart proposals, and native model
   interchange". A user searching the Hub types *model designer*, *workflow*,
   *batch*, *automation*, *no code*; only *modeler* and *graphical-modeler*
   are tags. The README's first screen is a security model; its version badge
   still says **1.5.28**.
2. **The first screen is an empty canvas.** The fifteen ready workflows live in
   a short list under the algorithm tree, discoverable only by scrolling the
   palette. Nothing on the canvas says "start here".
3. **Existing QGIS users cannot bring their models in one click.** Open asks
   for a file path; the user's own models sit in the profile's
   `processing/models` folder, which they rarely know the path to.
4. **No "do this to every layer".** The single most common reason people
   build a model is to repeat it; the Studio runs one configuration at a time.
5. **Five of the fifteen starters are everyday GIS; ten are PlanX showcases**
   that are hidden when PlanX is not installed — so a user without PlanX sees
   five starters, none of them the classic tasks people search for (clip to a
   boundary, dissolve, count points in polygons, nearest hub, zonal stats).
6. **No recent files.** Reopening yesterday's workflow means a file dialog.

## 2. The set

### S1 — Start page on an empty canvas — *highest value*
- When the graph is empty, the canvas shows a start panel: **Starter
  workflows** as cards (name, one-line description, node count, grouped
  *Everyday GIS* / *Urban analytics showcases*, unavailable ones listed as
  "needs …" instead of silently missing), and actions **Blank workflow**,
  **Open file…**, **Open a QGIS model** (S2), **Recent** (S3). It disappears
  as soon as the graph has a node and returns when it is cleared.
- Acceptance: smoke builds the Studio with an empty graph → panel visible
  with ≥ 1 card per available starter; triggering a card loads that graph and
  hides the panel; `clear` brings it back.

### S2 — Open models from the QGIS Models folder
- Lists every `.model3` in the Processing models folder(s) (the profile's
  `processing/models` plus the `MODELS_FOLDER` setting's extra paths) with
  name and group read from the file; one click imports through the existing
  `Model3Serializer.import_from_model3`.
- Acceptance: smoke writes a `.model3` (exported from a starter) into a
  temporary models folder → it appears in the list → importing it yields a
  graph with the same nodes and connections.

### S3 — Recent workflows
- The last 8 opened/saved paths (QgsSettings), shown on the start page and in
  an **Open recent** toolbar menu; missing files are dropped on display.
- Acceptance: pure list-maintenance test (dedupe, cap, order); smoke saves
  and reopens through the menu.

### S4 — Run for each layer (batch)
- Enabled when the workflow has exactly one unbound vector *or* raster
  input. **Run for each layer…** lists the compatible project layers; the
  workflow runs once per checked layer, sequentially in the background, each
  run's outputs suffixed with the input layer's name and grouped under one
  layer-tree group. Cancel stops after the current run; the final report
  lists per-layer success or the failing step.
- Acceptance: smoke runs the *Proximity buffer* starter over two fixture
  layers → two result layers, correctly named, one group; a cancel after the
  first run leaves exactly one.

### S5 — Six everyday starter workflows (native algorithms only)
- *Clip a layer to a boundary*, *Dissolve by attribute*, *Count points in
  polygons*, *Distance to the nearest hub*, *Zonal statistics of a raster*,
  *Repair and reproject*. Built only from `native:`/`qgis:` algorithms so they
  are always available, schema-validated like the existing fifteen.
- Acceptance: the existing catalogue validation covers them; smoke
  instantiates every starter on both runtimes and runs the new six on fixture
  data.

### S6 — Hub copy and README that say what it does for you
- `description` task-first ("Build and run QGIS Processing workflows on a
  visual canvas — start from ready-made workflows, run them on every layer,
  open your existing models, and export to Model Designer or Python"), `about`
  rewritten in the same order a user meets the features, tags extended (model
  designer, workflow, automation, batch, no-code, model3, processing modeler),
  README first screen = what it is + 4-step quick start; stale badge fixed.
  Security/agent depth stays in the manual, linked, not deleted.
- Acceptance: gate green; no literal `%`; no self-praise wording.

## 3. Release discipline
One release, **v1.7.0**, after `pf verify zero2smartmodeler` passes on QGIS
3.44 LTR and 4.2: version bump, CHANGELOG, tag, push to both remotes, GitHub +
GitLab releases with the zip, Hub upload.

## 4. Considered and left out — and why
- **Lowering `qgisMinimumVersion` below 3.44.** It would widen the audience
  more than any single feature, but this machine has no QGIS 3.40 runtime to
  prove the 32 k lines and their Processing signatures still hold there;
  shipping an untested minimum version is how a plugin collects one-star
  reviews. Recorded as the next lever once a 3.40 runtime is available.
- **More AI providers / agent tools.** Seven providers are already supported;
  the adoption barrier is the first two minutes, not the agent.
- **A web/cloud runner.** Out of the plugin's local-first scope.
