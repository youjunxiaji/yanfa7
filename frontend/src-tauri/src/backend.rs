//! Lifecycle of the bundled Python backend.
//!
//! Release builds start the sidecar that `backend/build_backend.py` builds with Nuitka (a onefile
//! program, bundled through `externalBin` in `tauri.windows.conf.json`) and stop it when the app
//! exits. It listens on 127.0.0.1:8000. Debug builds leave the backend alone: during development
//! it runs separately via `uv run main.py` on 8006, with hot reload.
//!
//! The backend's stdout / stderr go to `backend.log` in the app log directory
//! (`%LOCALAPPDATA%\com.rd7.yanfa7\logs\backend.log` on Windows), overwritten on every start.

use std::fs::{self, File};
use std::io::Write;
use std::sync::Mutex;

use tauri::async_runtime::Receiver;
use tauri::{AppHandle, Manager};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Tied to `externalBin` and to `SIDECAR_NAME` in `backend/build_backend.py`.
const SIDECAR: &str = "yanfa7-backend";

/// Directory the Pmax charts are written to (`TEMP_DIR` in `backend/app_pmax/module/chart.py`).
const PMAX_TEMP_DIR: &str = "yanfa7_pmax";

/// The running sidecar, taken out again on exit.
#[derive(Default)]
pub struct Backend(Mutex<Option<CommandChild>>);

/// Starts the sidecar. Does nothing in debug builds. Failures end up in `backend.log`; the
/// renderer notices on its own when the backend never answers.
pub fn spawn(app: &AppHandle) {
    if cfg!(debug_assertions) {
        return;
    }

    let mut log = open_log(app);
    match start(app) {
        Ok(rx) => {
            tauri::async_runtime::spawn(drain(rx, log));
        }
        Err(err) => {
            if let Some(file) = log.as_mut() {
                let _ = writeln!(file, "[外壳] {err}");
            }
        }
    }
}

/// Stops the sidecar and removes the Pmax temp directory; called when the app exits.
///
/// Killing the sidecar ends the onefile bootstrap. The child that actually runs Python checks its
/// parent once a second and exits when it is gone; it also exits as soon as its stdin closes
/// (`--sidecar`), which covers the shell crashing or being force-killed.
pub fn shutdown(app: &AppHandle) {
    let child = app
        .state::<Backend>()
        .0
        .lock()
        .ok()
        .and_then(|mut guard| guard.take());
    if let Some(child) = child {
        let _ = child.kill();
    }
    let _ = fs::remove_dir_all(std::env::temp_dir().join(PMAX_TEMP_DIR));
}

fn start(app: &AppHandle) -> Result<Receiver<CommandEvent>, String> {
    let (rx, child) = app
        .shell()
        .sidecar(SIDECAR)
        .map_err(|e| format!("找不到随包的后端程序：{e}"))?
        // Exit when stdin closes, see `backend/main.py`.
        .args(["--sidecar"])
        // Python writes pipes in the system code page (GBK on Chinese Windows); keep the log
        // UTF-8, and unbuffered so nothing is lost when the process is killed.
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONUNBUFFERED", "1")
        .spawn()
        .map_err(|e| format!("后端启动失败：{e}"))?;

    *app.state::<Backend>()
        .0
        .lock()
        .map_err(|_| "后端进程状态锁损坏".to_string())? = Some(child);
    Ok(rx)
}

/// Keeps reading the sidecar's output into the log. This must never stop while the process
/// runs: the shell plugin's channel holds a single event, so an unread pipe blocks the backend.
async fn drain(mut rx: Receiver<CommandEvent>, mut log: Option<File>) {
    while let Some(event) = rx.recv().await {
        let bytes = match event {
            CommandEvent::Stdout(line) | CommandEvent::Stderr(line) => line,
            CommandEvent::Terminated(payload) => {
                format!("[外壳] 后端进程已退出，退出码 {:?}\n", payload.code).into_bytes()
            }
            CommandEvent::Error(err) => format!("[外壳] {err}\n").into_bytes(),
            _ => continue,
        };
        if let Some(file) = log.as_mut() {
            let _ = file.write_all(&bytes);
        }
    }
}

fn open_log(app: &AppHandle) -> Option<File> {
    let dir = app.path().app_log_dir().ok()?;
    fs::create_dir_all(&dir).ok()?;
    File::create(dir.join("backend.log")).ok()
}
