// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use sysinfo::{System, SystemExt, CpuExt};

#[derive(serde::Serialize, serde::Deserialize, Debug, Clone)]
pub struct ChatMessage {
    id: String,
    content: String,
    sender: String,
    timestamp: String,
}

#[tauri::command]
async fn get_chat_history() -> Result<Vec<ChatMessage>, String> {
    Ok(vec![])
}

#[tauri::command]
async fn generate_ai_response(message: String) -> Result<String, String> {
    let client = reqwest::Client::new();
    let api_url = "https://api-inference.huggingface.co/models/gpt2"; // Replace with your desired model
    let hf_token = std::env::var("HF_TOKEN").map_err(|e| format!("HF_TOKEN not set: {}", e))?;

    let mut headers = reqwest::header::HeaderMap::new();
    headers.insert("Authorization", format!("Bearer {}", hf_token).parse().unwrap());

    let payload = serde_json::json!({
        "inputs": message
    });

    let res = client.post(api_url)
        .headers(headers)
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("Failed to send request to Hugging Face API: {}", e))?;

    if res.status().is_success() {
        let response_json: serde_json::Value = res.json().await.map_err(|e| format!("Failed to parse response JSON: {}", e))?;
        // Assuming the response is an array of objects with a 'generated_text' field
        if let Some(generated_text) = response_json[0]["generated_text"].as_str() {
            Ok(generated_text.to_string())
        } else {
            Err("Generated text not found in response.".into())
        }
    } else {
        let status = res.status();
        let error_text = res.text().await.map_err(|e| format!("Failed to get error text: {}", e))?;
        Err(format!("Hugging Face API error: {} - {}", status, error_text))
    }
}

#[derive(serde::Serialize, Clone)]
pub struct PerformanceData {
    cpu_usage: f32,
    memory_usage: f32,
}

#[tauri::command]
fn get_performance_data() -> Result<PerformanceData, String> {
    let mut sys = System::new_all();
    sys.refresh_cpu();
    sys.refresh_memory();

    let cpu_usage = sys.global_cpu_info().cpu_usage();
    let memory_usage = (sys.used_memory() as f32 / sys.total_memory() as f32) * 100.0;

    Ok(PerformanceData {
        cpu_usage,
        memory_usage,
    })
}

#[tauri::command]
fn get_active_ai_queries() -> Result<u32, String> {
    // For now, return a dummy value. In a real application, this would query a backend service.
    Ok(5)
}

fn main() {
  dotenv::dotenv().ok();
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![get_chat_history, generate_ai_response, get_performance_data, get_active_ai_queries])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
