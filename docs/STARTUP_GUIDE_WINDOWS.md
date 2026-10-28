# Windows Startup Guide

This guide gets the Energy-Aware Routing Protocol simulator running on Windows and starts its interactive dashboard.

## Prerequisites

- Windows 10 or 11.
- Python 3.12 or later. During installation, enable the Python launcher (`py`) or add Python to `PATH`.
- The project folder on your computer.
- Internet access for the initial dependency installation.

## One-time setup

1. Open the project folder in File Explorer.
2. Open a terminal in that folder (right-click the folder and choose **Open in Terminal**).
3. Create a virtual environment:

   ```powershell
   py -3.12 -m venv .venv
   ```

   If `py -3.12` is unavailable but `python` points to Python 3.12 or newer, use:

   ```powershell
   python -m venv .venv
   ```

4. Install the project dependencies into the virtual environment:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m pip install -e .
   ```

   This installs Streamlit and the simulation libraries, then registers the project so its CLI and dashboard can import the code. You do not need to activate the environment to use the launcher.

   If the launcher says `.venv` exists but Python cannot start, that environment
   was likely copied from a different computer or Python installation. Recreate
   it from this project folder, then reinstall dependencies:

   ```powershell
   Remove-Item -Recurse -Force .venv
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m pip install -e .
   ```

## Start the dashboard

Double-click **`start_dashboard.bat`** in the project folder. A console window starts the dashboard and Streamlit opens it in your browser. If it does not open automatically, visit [http://localhost:8501](http://localhost:8501).

Keep the console window open while using the dashboard. To stop the project, focus that window and press **Ctrl+C**.

You can also start it from a terminal in the project folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src/energy_routing/dashboard.py
```

Or use the project CLI:

```powershell
.\.venv\Scripts\python.exe -m energy_routing.main gui
```

## First simulation

1. Open the **Run a Simulation** tab.
2. Set the number of sensor nodes, communication range, initial energy, round limit, seed, and routing algorithm.
3. Choose **Run Simulation** and wait for completion.
4. Review the lifetime and packet-delivery metrics and the charts below them.

The seed makes a run reproducible: use the same seed and configuration to recreate the same topology and traffic conditions.

## Compare routing algorithms

1. Open **Compare Algorithms**.
2. Choose the number of paired seeds, starting seed, network settings, round limit, and energy-aware distance weight.
3. Start the comparison. Both strategies run with matching topology and traffic conditions for each seed.
4. Review the per-seed outcomes, aggregate metrics, and comparison charts.

A larger seed count takes longer to run. Start with a small count to familiarize yourself with the workflow.

## Inspect saved results

Open **Saved Results** to browse JSON files under `results/` or upload a compatible JSON result file. Dashboard runs are saved under `results/dashboard/`. Existing files are not deleted by the dashboard.

## Run a simulation from the terminal

For a short smoke run, use the included quick configuration:

```powershell
.\.venv\Scripts\python.exe -m energy_routing.main run --config configs/test_quick.yaml
```

For the base configuration:

```powershell
.\.venv\Scripts\python.exe -m energy_routing.main run --config configs/base.yaml
```

The base configuration can take longer. CLI results and plots are written to the configured results directory.

## Troubleshooting

- **`py` or `python` is not recognized:** Install Python 3.12 or newer and enable the Python launcher or add Python to `PATH`, then reopen the terminal.
- **The launcher reports missing project dependencies:** Complete the one-time setup commands above. Make sure you install dependencies using `.venv\Scripts\python.exe` from the project folder.
- **The browser page does not load:** Keep the console open and check for an error message. Open `http://localhost:8501` manually. If port 8501 is already in use, stop the other dashboard or start this one from a terminal with `--server.port 8502`.
- **Configuration file not found:** Run commands from the project folder. The batch file automatically changes to that folder; terminal commands should be run there too.
- **To exit:** Press Ctrl+C in the dashboard console window.
