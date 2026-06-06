use serde::Serialize;
use walkdir::WalkDir;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ScanResult {
    file_paths: Vec<String>,
    file_sizes: Vec<u64>,
}

/// Recursively scan `root_dir` for files whose extension is in `extensions`
/// (default `["htm"]`), returning their absolute paths (sorted) and byte sizes.
/// Replaces the Electron main-process `fs:scanDir` IPC handler.
#[tauri::command]
fn scan_dir(root_dir: String, extensions: Option<Vec<String>>) -> ScanResult {
    let exts: Vec<String> = extensions
        .unwrap_or_else(|| vec!["htm".to_string()])
        .iter()
        .map(|e| e.to_lowercase())
        .collect();

    let mut entries: Vec<(String, u64)> = Vec::new();
    for entry in WalkDir::new(&root_dir).into_iter().filter_map(|e| e.ok()) {
        if !entry.file_type().is_file() {
            continue;
        }
        let matches = entry
            .path()
            .extension()
            .and_then(|s| s.to_str())
            .map(|ext| exts.iter().any(|e| e == &ext.to_lowercase()))
            .unwrap_or(false);
        if matches {
            let size = entry.metadata().map(|m| m.len()).unwrap_or(0);
            entries.push((entry.path().to_string_lossy().to_string(), size));
        }
    }

    entries.sort_by(|a, b| a.0.cmp(&b.0));
    ScanResult {
        file_paths: entries.iter().map(|(p, _)| p.clone()).collect(),
        file_sizes: entries.iter().map(|(_, s)| *s).collect(),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_drag::init())
        .invoke_handler(tauri::generate_handler![scan_dir])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
