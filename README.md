# CDSS-AB: synthetic reproducibility demo

Run a small, fully synthetic CDSS-AB analysis in a browser using Binder. The
example contains four arithmetic questions, three fictional participants,
12 responses and three answer revisions. It demonstrates the software's
analysis and verification workflow. It does not reproduce clinical pilot results.

## Run in Binder

[**Launch the verified example in Binder**](https://mybinder.org/v2/gh/VincentXing23/CDSS-AB-binder/44bd860f7774ae440e859f1ac0feae7036120d13?urlpath=lab/tree/demo.ipynb)

Wait until the bottom status bar shows **Python 3 (ipykernel) | Idle**. Open
`demo.ipynb` and choose **Run → Run All Cells**. The notebook runs the
analysis twice, checks the results, displays the condition totals and offers a
ZIP download. Expected results are **12 responses, 8 correct answers and
3 answer revisions**: T0 = 2/4, T1 = 4/4, T2 = 2/4.

Binder provides temporary sessions. Download the ZIP before leaving; session
files are not permanent storage. The initial image build can take several
minutes. This demo needs no API key, model download or GPU.

The launch URL is pinned to commit
`44bd860f7774ae440e859f1ac0feae7036120d13`. It was successfully built and run on
Binder on 2026-11-03 (UTC), with Python 3.12.12, NumPy 2.2.6 and SQLite 3.50.4
on Linux x86_64. Both 22-file runs passed verification; the downloaded ZIP
contained both runs plus their log (45 files), with matching expected totals.
The pinned revision's README predates this online validation note; the analysis
code, references, notebook and Binder configuration have not changed.

## Run locally

Use Python 3.12 and install the locked analysis dependency:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python cdss-ab/scripts/run_binder_demo.py --output-dir demo-results/run-001
```

Choose a new output directory for every run. On Windows, use
`.venv\Scripts\python` in place of `.venv/bin/python`.

## What is verified

The Binder entry point uses a committed, reviewed reference. It never generates
or replaces a reference at runtime.

- The input snapshot is unchanged and matches the original reference.
- Two independent runs produce the same complete set of 22 files, with identical
  SHA-256 hashes within the current environment.
- Twenty platform-independent files also match the original reference hashes.
- SQLite schema and all database content match a committed semantic reference;
  database integrity, foreign keys and expected synthetic results are checked.
- The manifest accounts for every output file with its actual hash and size,
  and its provenance fields and analysis script identity are verified.

This is **cross-platform content verification**, not a claim that a Linux SQLite
file has the same binary representation as the original macOS database.
`reproduce.sh` retains the original strict verification of all 22 reference
hashes for the documented reference environment.

The original reference was verified with CPython 3.12.14, NumPy 2.2.6 and
SQLite 3.53.1 on macOS arm64. Binder selects Python 3.12 and pins NumPy 2.2.6.
The Python patch version, SQLite build, Jupyter software and base operating
system are supplied by Binder; the verification log records the actual runtime.
The environment configuration is not a complete container image lock.

## Source and contents

The three original analysis/verification scripts and synthetic inputs are copied
unchanged from SAIRI-CDSS commit
`149f7ad4e33f71ae3f5a6e95719b6430511664fd`. File hashes are recorded in
`SOURCE-PROVENANCE.json`. This standalone package adds a Binder environment,
notebook, portable verification entry point, reviewed semantic reference and
failure-path tests.

Only the synthetic analysis example is included. The package contains no real
participant responses, MedQA materials, credentials, collection server, paper
drafts or upstream Git history. The software retains its MIT license.

## 中文使用说明

打开 `demo.ipynb`，点击 **Run → Run All Cells**，即可运行两轮合成数据分析并校验、
查看分组结果、下载结果压缩包。预期为 12 条作答、8 条正确、3 次改答。
进入后请等底部 Python 内核状态显示 Idle，再运行全部单元。
Binder 会话是临时的，离开前请下载结果。该示例验证软件复现流程，不复现真实临床试点。

## Platform documentation

- [Binder session limits](https://mybinder.readthedocs.io/en/latest/user-guidelines.html)
- [Binder configuration location](https://repo2docker.readthedocs.io/en/latest/use/repository/)
- [Opening a notebook directly](https://mybinder.readthedocs.io/en/latest/howto/user_interface.html)
