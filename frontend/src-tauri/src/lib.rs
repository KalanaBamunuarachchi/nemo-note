use std::sync::{Arc, Mutex};

use tauri::Manager;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

fn backend_cleanup_plugin<R: tauri::Runtime>(
    backend_child: Arc<Mutex<Option<CommandChild>>>,
) -> tauri::plugin::TauriPlugin<R> {
    tauri::plugin::Builder::new("backend-cleanup")
        .on_event(move |_app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(child) = backend_child.lock().unwrap().take() {
                    let pid = child.pid();

                    log::info!(
                        "Stopping backend sidecar with PID {}...",
                        pid
                    );

                    // Kill the backend process and its child processes.
                    #[cfg(target_os = "windows")]
                    {
                        match std::process::Command::new("taskkill")
                            .args([
                                "/PID",
                                &pid.to_string(),
                                "/T",
                                "/F",
                            ])
                            .output()
                        {
                            Ok(output) => {
                                if output.status.success() {
                                    log::info!(
                                        "Backend sidecar stopped."
                                    );
                                } else {
                                    log::error!(
                                        "taskkill failed: {}",
                                        String::from_utf8_lossy(
                                            &output.stderr
                                        )
                                    );
                                }
                            }

                            Err(error) => {
                                log::error!(
                                    "Failed to execute taskkill: {}",
                                    error
                                );
                            }
                        }
                    }

                    // Keep the CommandChild alive until after taskkill.
                    drop(child);
                }
            }
        })
        .build()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let backend_child: Arc<Mutex<Option<CommandChild>>> =
        Arc::new(Mutex::new(None));

    let backend_child_for_cleanup =
        Arc::clone(&backend_child);

    let backend_child_for_setup =
        Arc::clone(&backend_child);

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(backend_cleanup_plugin::<tauri::Wry>(
            backend_child_for_cleanup,
        ))
        .setup(move |app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // Resolve the bundled resource directory
            // where engines/ gets copied.
            let engines_dir = if cfg!(debug_assertions) {
                std::path::PathBuf::from(env!(
                    "CARGO_MANIFEST_DIR"
                ))
                .join("../../engines")
                .canonicalize()?
            } else {
                app.path()
                    .resource_dir()?
                    .join("engines")
                    .canonicalize()?
            };

            log::info!(
                "Resolved engines dir: {:?}",
                engines_dir
            );

            // Resolve the persistent application settings directory.
            let settings_dir = app
                .path()
                .app_local_data_dir()?;

            std::fs::create_dir_all(&settings_dir)?;

            log::info!(
                "Resolved settings dir: {:?}",
                settings_dir
            );

            let sidecar = app
                .shell()
                .sidecar("nemo-note-backend")?
                .env("NEMO_ENGINES_DIR", engines_dir)
                .env("NEMO_SETTINGS_DIR", settings_dir);

            let (mut rx, child) = sidecar.spawn()?;

            let pid = child.pid();

            log::info!(
                "Started backend sidecar with PID {}",
                pid
            );

            // Store the child so the cleanup plugin can get
            // its PID when Tauri exits.
            *backend_child_for_setup.lock().unwrap() =
                Some(child);

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            log::info!(
                                "Backend stdout: {}",
                                String::from_utf8_lossy(&line)
                            );
                        }

                        CommandEvent::Stderr(line) => {
                            log::error!(
                                "Backend stderr: {}",
                                String::from_utf8_lossy(&line)
                            );
                        }

                        CommandEvent::Error(error) => {
                            log::error!(
                                "Backend error: {}",
                                error
                            );
                        }

                        CommandEvent::Terminated(payload) => {
                            log::error!(
                                "Backend terminated: code={:?}, signal={:?}",
                                payload.code,
                                payload.signal
                            );
                        }

                        _ => {}
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}