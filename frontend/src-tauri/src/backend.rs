//! Lifecycle of the bundled Python backend.
//!
//! Release builds start the sidecar that `backend/build_backend.py` builds with Nuitka (a onefile
//! program, bundled through `externalBin` in `tauri.windows.conf.json`) and stop it when the app
//! exits. It listens on 127.0.0.1:8000. Debug builds leave the backend alone: during development
//! it runs separately via `uv run main.py` on 8006, with hot reload.
//!
//! The backend's stdout / stderr go to one log file per run in the app log directory, named after
//! the start time (`%LOCALAPPDATA%\com.rd7.yanfa7\logs\backend-20261015-103152.log` on Windows).
//! Each start removes logs older than `LOG_KEEP`, so the run that went wrong is still there however
//! often the app was reopened since; a run's log stops growing at `LOG_MAX_BYTES`, so an error loop
//! cannot fill the disk.

use std::fs::{self, File};
use std::io::{ErrorKind, Write};
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::{Duration, SystemTime};

use chrono::Local;
use tauri::async_runtime::Receiver;
use tauri::{AppHandle, Manager};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Tied to `externalBin` and to `SIDECAR_NAME` in `backend/build_backend.py`.
const SIDECAR: &str = "yanfa7-backend";

/// Directory the Pmax charts are written to (`TEMP_DIR` in `backend/app_pmax/module/chart.py`).
const PMAX_TEMP_DIR: &str = "yanfa7_pmax";

/// How long run logs are kept.
const LOG_KEEP: Duration = Duration::from_secs(7 * 24 * 60 * 60);

/// Size at which a run's log stops growing.
const LOG_MAX_BYTES: u64 = 10 * 1024 * 1024;

/// The running sidecar, taken out again on exit, and this run's log file.
#[derive(Default)]
pub struct Backend {
    child: Mutex<Option<CommandChild>>,
    log_path: Mutex<Option<PathBuf>>,
}

impl Backend {
    /// This run's log file, for the log page's "open log folder". `None` in debug builds, which do
    /// not start the backend, or when the file could not be created.
    pub fn log_path(&self) -> Option<PathBuf> {
        self.log_path.lock().ok().and_then(|guard| guard.clone())
    }
}

/// Starts the sidecar. Does nothing in debug builds. Failures end up in this run's log; the
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
            if let Some(log) = log.as_mut() {
                log.write(format!("[外壳] {err}\n").as_bytes());
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
        .child
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
        .child
        .lock()
        .map_err(|_| "后端进程状态锁损坏".to_string())? = Some(child);
    Ok(rx)
}

/// Keeps reading the sidecar's output into the log. This must never stop while the process
/// runs: the shell plugin's channel holds a single event, so an unread pipe blocks the backend.
async fn drain(mut rx: Receiver<CommandEvent>, mut log: Option<RunLog>) {
    while let Some(event) = rx.recv().await {
        let bytes = match event {
            CommandEvent::Stdout(line) | CommandEvent::Stderr(line) => line,
            CommandEvent::Terminated(payload) => {
                format!("[外壳] 后端进程已退出，退出码 {:?}\n", payload.code).into_bytes()
            }
            CommandEvent::Error(err) => format!("[外壳] {err}\n").into_bytes(),
            _ => continue,
        };
        if let Some(log) = log.as_mut() {
            log.write(&bytes);
        }
    }
}

/// This run's log file, cut off at `LOG_MAX_BYTES`.
struct RunLog {
    file: File,
    written: u64,
}

impl RunLog {
    fn write(&mut self, bytes: &[u8]) {
        if self.written >= LOG_MAX_BYTES {
            return;
        }
        let _ = self.file.write_all(bytes);
        self.written += bytes.len() as u64;
        if self.written >= LOG_MAX_BYTES {
            let _ = writeln!(
                self.file,
                "[外壳] 日志已到 {} MB，后面的不再写入",
                LOG_MAX_BYTES / 1024 / 1024
            );
        }
    }
}

/// Removes old logs, then creates this run's and remembers its path in `Backend`.
fn open_log(app: &AppHandle) -> Option<RunLog> {
    let dir = app.path().app_log_dir().ok()?;
    fs::create_dir_all(&dir).ok()?;
    remove_old_logs(&dir);
    let (path, file) = create_run_log(&dir)?;
    if let Ok(mut guard) = app.state::<Backend>().log_path.lock() {
        *guard = Some(path);
    }
    Some(RunLog { file, written: 0 })
}

/// Names the file after the start time. Two instances started within the same second get a
/// suffix instead of truncating each other's log.
fn create_run_log(dir: &Path) -> Option<(PathBuf, File)> {
    let stamp = Local::now().format("%Y%m%d-%H%M%S");
    for n in 1..=9 {
        let name = if n == 1 {
            format!("backend-{stamp}.log")
        } else {
            format!("backend-{stamp}-{n}.log")
        };
        let path = dir.join(name);
        match File::options().write(true).create_new(true).open(&path) {
            Ok(file) => return Some((path, file)),
            Err(err) if err.kind() == ErrorKind::AlreadyExists => continue,
            Err(_) => return None,
        }
    }
    None
}

/// Removes the backend logs last written more than `LOG_KEEP` ago, including the single
/// `backend.log` that versions up to 2.2.1 wrote.
fn remove_old_logs(dir: &Path) {
    let Ok(entries) = fs::read_dir(dir) else {
        return;
    };
    let now = SystemTime::now();
    for entry in entries.flatten() {
        let name = entry.file_name();
        let name = name.to_string_lossy();
        if !(name.starts_with("backend") && name.ends_with(".log")) {
            continue;
        }
        let expired = entry
            .metadata()
            .and_then(|meta| meta.modified())
            .ok()
            .and_then(|modified| now.duration_since(modified).ok())
            .is_some_and(|age| age > LOG_KEEP);
        if expired {
            let _ = fs::remove_file(entry.path());
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::FileTimes;

    fn empty_dir(name: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!("yanfa7-{name}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    fn names_in(dir: &Path) -> Vec<String> {
        let mut names: Vec<String> = fs::read_dir(dir)
            .unwrap()
            .map(|entry| entry.unwrap().file_name().to_string_lossy().into_owned())
            .collect();
        names.sort();
        names
    }

    #[test]
    fn removes_only_backend_logs_older_than_a_week() {
        let dir = empty_dir("log-retention");
        let stale = SystemTime::now() - LOG_KEEP - Duration::from_secs(60);
        for name in ["backend-20261001-090000.log", "backend.log", "other.log"] {
            let file = File::create(dir.join(name)).unwrap();
            file.set_times(FileTimes::new().set_modified(stale))
                .unwrap();
        }
        File::create(dir.join("backend-20261015-103152.log")).unwrap();

        remove_old_logs(&dir);

        assert_eq!(names_in(&dir), ["backend-20261015-103152.log", "other.log"]);
        fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn names_runs_after_the_start_time_without_overwriting() {
        let dir = empty_dir("log-naming");

        let (first, _) = create_run_log(&dir).unwrap();
        let (second, _) = create_run_log(&dir).unwrap();

        // Started within the same second, the second run gets `-2` instead of truncating the first.
        assert_ne!(first, second);
        for path in [&first, &second] {
            let name = path.file_name().unwrap().to_string_lossy().into_owned();
            assert!(
                name.starts_with("backend-20") && name.ends_with(".log"),
                "{name}"
            );
        }
        assert_eq!(names_in(&dir).len(), 2);
        fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn stops_writing_at_the_size_cap() {
        let dir = empty_dir("log-cap");
        let path = dir.join("backend-cap.log");
        let mut log = RunLog {
            file: File::create(&path).unwrap(),
            written: LOG_MAX_BYTES - 5,
        };

        log.write(b"crosses the cap\n");
        log.write(b"dropped\n");

        let text = fs::read_to_string(&path).unwrap();
        assert_eq!(
            text,
            "crosses the cap\n[外壳] 日志已到 10 MB，后面的不再写入\n"
        );
        fs::remove_dir_all(&dir).unwrap();
    }
}
