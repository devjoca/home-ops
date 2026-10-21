//! Outbound-only LG Home watcher. Only the configured launcher can be launched.
use futures_util::{SinkExt, StreamExt};
use serde::Deserialize;
use serde_json::{Value, json};
use std::{error::Error, time::Duration};
use tokio::{
    net::TcpStream,
    time::{Instant, timeout},
};
use tokio_tungstenite::{
    Connector, MaybeTlsStream, WebSocketStream,
    tungstenite::{Message, protocol::WebSocketConfig},
};

type Socket = WebSocketStream<MaybeTlsStream<TcpStream>>;
type Result<T> = std::result::Result<T, Box<dyn Error + Send + Sync>>;
#[derive(Deserialize)]
struct Config {
    host: String,
    client_key: String,
    registration: Value,
    #[serde(default = "default_launcher")]
    launcher_id: String,
}
fn default_launcher() -> String {
    "com.gathin.tvhome".into()
}
#[derive(Debug)]
struct AuthRejected;
impl std::fmt::Display for AuthRejected {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("existing TV pairing or permission rejected")
    }
}
impl Error for AuthRejected {}
fn load_config(path: &str) -> Result<Config> {
    let mut cfg: Config = serde_json::from_slice(&std::fs::read(path)?)?;
    if cfg.host.is_empty() || cfg.client_key.is_empty() || !cfg.registration["payload"].is_object()
    {
        return Err("missing host, key or registration payload".into());
    }
    if cfg.launcher_id.is_empty() {
        cfg.launcher_id = default_launcher();
    }
    cfg.registration["payload"]["client-key"] = json!(cfg.client_key);
    Ok(cfg)
}
async fn send(ws: &mut Socket, value: Value) -> Result<()> {
    timeout(
        Duration::from_secs(10),
        ws.send(Message::Text(value.to_string().into())),
    )
    .await??;
    Ok(())
}
async fn receive(ws: &mut Socket) -> Result<Value> {
    timeout(Duration::from_secs(10), async {
        while let Some(msg) = ws.next().await {
            match msg? {
                Message::Text(text) => return Ok(serde_json::from_str(&text)?),
                Message::Close(_) => return Err("TV closed connection".into()),
                _ => {
                    ws.flush().await?;
                }
            }
        }
        Err("TV disconnected".into())
    })
    .await?
}
async fn watch(cfg: &Config, observe: bool) -> Result<()> {
    // Same self-signed-TV certificate policy as the existing Go client.
    let tls = native_tls::TlsConnector::builder()
        .danger_accept_invalid_certs(true)
        .danger_accept_invalid_hostnames(true)
        .build()?;
    let stream = timeout(
        Duration::from_secs(8),
        TcpStream::connect((cfg.host.as_str(), 3001)),
    )
    .await??;
    let url = format!("wss://{}:3001", cfg.host);
    let limits = WebSocketConfig::default()
        .max_message_size(Some(1 << 20))
        .max_frame_size(Some(1 << 20));
    let (mut ws, _) = timeout(
        Duration::from_secs(8),
        tokio_tungstenite::client_async_tls_with_config(
            url,
            stream,
            Some(limits),
            Some(Connector::NativeTls(tls)),
        ),
    )
    .await??;
    eprintln!("TLS WebSocket connected");
    for message in [
        json!({"id":"hello","type":"hello","payload":{}}),
        json!({"id":"sys","type":"request","uri":"ssap://system/getSystemInfo","payload":{}}),
    ] {
        send(&mut ws, message).await?;
        receive(&mut ws).await?;
        eprintln!("TV handshake response received");
    }
    send(&mut ws, cfg.registration.clone()).await?;
    if receive(&mut ws).await?["type"] != "registered" {
        return Err(AuthRejected.into());
    }
    send(&mut ws, json!({"id":"foreground","type":"subscribe","uri":"ssap://com.webos.applicationManager/getForegroundAppInfo","payload":{}})).await?;
    eprintln!("Connected; observing LG Home (redirect={})", !observe);
    let mut last_redirect: Option<Instant> = None;
    let mut next_ping = Instant::now() + Duration::from_secs(15);
    let mut pong_deadline: Option<Instant> = None;
    loop {
        let deadline = pong_deadline.unwrap_or(next_ping);
        tokio::select! {
            _ = tokio::time::sleep_until(deadline) => {
                if pong_deadline.is_some() { return Err("TV heartbeat timeout".into()); }
                timeout(Duration::from_secs(10), ws.send(Message::Ping(Vec::new().into()))).await??;
                pong_deadline = Some(Instant::now() + Duration::from_secs(10));
            }
            incoming = ws.next() => {
                match incoming.ok_or("TV disconnected")?? {
                    Message::Pong(_) => {
                        pong_deadline = None;
                        next_ping = Instant::now() + Duration::from_secs(15);
                    }
                    Message::Ping(_) => { timeout(Duration::from_secs(10), ws.flush()).await??; }
                    Message::Close(_) => return Err("TV closed connection".into()),
                    Message::Text(text) => {
                        let event: Value = serde_json::from_str(&text)?;
                        if (event["id"] == "foreground" || event["id"] == "launch") && event["type"] == "error" {
                            return Err(AuthRejected.into());
                        }
                        if event["id"] != "foreground" || event["type"] != "response" || event["payload"]["appId"] != "com.webos.app.home" { continue; }
                        if observe { eprintln!("LG Home observed; no command sent"); continue; }
                        let now = Instant::now();
                        if last_redirect.is_some_and(|last| now.duration_since(last) < Duration::from_secs(3)) {
                            last_redirect = None;
                            eprintln!("Second Home press: leaving LG Home available");
                            continue;
                        }
                        last_redirect = Some(now);
                        send(&mut ws, json!({"id":"launch","type":"request","uri":"ssap://system.launcher/launch","payload":{"id":cfg.launcher_id}})).await?;
                        eprintln!("LG Home -> {}", cfg.launcher_id);
                    }
                    _ => {}
                }
            }
        }
    }
}
async fn run(cfg: &Config, observe: bool) -> i32 {
    let mut delay = 5;
    loop {
        if let Err(error) = watch(cfg, observe).await {
            if error.downcast_ref::<AuthRejected>().is_some() {
                eprintln!("Existing TV pairing/permission rejected; stopping without re-pairing");
                return 77;
            }
            // Avoid logging peer messages or configuration that can contain credentials.
            let category = if let Some(ws_error) =
                error.downcast_ref::<tokio_tungstenite::tungstenite::Error>()
            {
                match ws_error {
                    tokio_tungstenite::tungstenite::Error::Tls(e) => format!("TLS: {e}"),
                    tokio_tungstenite::tungstenite::Error::Http(r) => {
                        format!("HTTP {}", r.status())
                    }
                    tokio_tungstenite::tungstenite::Error::Io(e) => format!("I/O {:?}", e.kind()),
                    tokio_tungstenite::tungstenite::Error::Protocol(_) => {
                        "WebSocket protocol".into()
                    }
                    _ => "WebSocket closed/error".into(),
                }
            } else if error
                .downcast_ref::<tokio::time::error::Elapsed>()
                .is_some()
            {
                "timeout".into()
            } else {
                "TV session ended".into()
            };
            eprintln!("TV unavailable ({category}); retrying in {delay}s");
        }
        tokio::time::sleep(Duration::from_secs(delay)).await;
        delay = (delay * 2).min(30);
    }
}
#[tokio::main(flavor = "current_thread")]
async fn main() {
    let mut args: Vec<String> = std::env::args().skip(1).collect();
    let observe = args.first().is_some_and(|arg| arg == "--observe");
    if observe {
        args.remove(0);
    }
    if args.len() != 1 {
        eprintln!("usage: lg-home-redirect-rust [--observe] private-config.json");
        std::process::exit(2);
    }
    let cfg = match load_config(&args[0]) {
        Ok(cfg) => cfg,
        Err(_) => {
            eprintln!("Cannot read valid private configuration");
            std::process::exit(78);
        }
    };
    let mut terminate = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
        .expect("SIGTERM handler");
    let code = tokio::select! {
        code = run(&cfg, observe) => code,
        _ = tokio::signal::ctrl_c() => 0,
        _ = terminate.recv() => 0,
    };
    std::process::exit(code);
}
