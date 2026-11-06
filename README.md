# CDSS-AB: interactive doctor demo

[**Open the doctor interface in Binder**](https://mybinder.org/v2/gh/VincentXing23/CDSS-AB-binder/main?urlpath=cdss-demo/)

After Binder starts, the link opens the CDSS-AB interface directly. No notebook
commands, API key, model download or GPU are needed.

## Try the complete workflow

1. Sign in with **doctor / demo** and select **Start**.
2. Answer three short questions based on a fictional anaemia vignette. They
   illustrate no advice, correct advice and deliberately incorrect advice.
3. Revisit a question and change an answer, then finish the exercise.
4. Sign out and sign in with **admin / demo**. Inspect completion, accuracy
   and individual responses, then export results including revision counts.

The login page also shows the demonstration credentials. This exercise uses
synthetic cases and temporary responses. It is intended to demonstrate the
software, not to assess clinical competence or establish a training effect.
Each Binder session has its own files and accounts. Do not enter real patient
information. Download exports before the temporary session ends.

The first image build can take several minutes. If a public Binder provider
cannot start a session, use the local command below.

## Run the interface locally

Python 3.12 is sufficient for the interactive interface:

```sh
python cdss-ab/scripts/serve_interactive_demo.py --port 8765
```

Open `http://127.0.0.1:8765/` and use the same demo accounts. The launcher creates
its runtime files in a temporary directory. It binds to localhost; it does not
create a public tunnel.

## Supplementary analysis notebook

[Open the analysis notebook](https://mybinder.org/v2/gh/VincentXing23/CDSS-AB-binder/main?urlpath=lab/tree/demo.ipynb)

The original `demo.ipynb` remains available. Choose **Run → Run All Cells** to run
two analyses of a separate, fixed synthetic snapshot. Expected results are
**12 responses, 8 correct answers and 3 answer revisions**: T0 = 2/4, T1 = 4/4,
T2 = 2/4. Download the ZIP at the end.

This fixed snapshot is separate from responses entered in the interactive
exercise. Its four arithmetic questions and three fictional participants support
automated reproduction checks, not clinical pilot results.

For command-line analysis, install the pinned dependency and run:

```sh
python -m pip install -r requirements.lock
python cdss-ab/scripts/run_binder_demo.py --output-dir demo-results/run-001
```

Use a new output directory for every run.

## Analysis verification

The verifier checks both runs' complete set of 22 output files, 20 fixed
platform-independent hashes, SQLite schema/content, expected totals and output
manifest. SQLite content is compared across platforms; binary equality with the
original macOS database is not assumed. The committed references are never
regenerated during a demonstration.

Binder selects Python 3.12 and pins NumPy 2.2.6 and jupyter-server-proxy 4.6.0.
Other Jupyter and operating-system components come from the Binder image.

## Source and scope

The software is derived from SAIRI-CDSS commit
`149f7ad4e33f71ae3f5a6e95719b6430511664fd`. Original analysis scripts and synthetic
snapshot files are preserved. The doctor interface and server are reused with
small adaptations for a temporary demo: relative proxy paths, visible demo
credentials and a synthetic clinical exercise. See `SOURCE-PROVENANCE.json` for
original and adapted file hashes.

This repository includes no real participant responses, MedQA case bank,
private account configuration, manuscript drafts or upstream Git history.
The software retains its MIT license. The example advice is prepared in advance;
the demo does not call an AI model.

## Platform documentation

- [Binder user guidance](https://mybinder.readthedocs.io/en/latest/user-guidelines.html)
- [Starting and proxying applications](https://jupyter-server-proxy.readthedocs.io/en/latest/server-process.html)
- [Opening Binder interfaces directly](https://mybinder.readthedocs.io/en/latest/howto/user_interface.html)
