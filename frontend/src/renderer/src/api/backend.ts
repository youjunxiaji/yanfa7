// 开发时后端由 `uv run main.py` 起在 8006，打包后的后端固定 8000，与 backend/main.py 保持一致
const BACKEND_PORT = import.meta.env.DEV ? 8006 : 8000

export const API_BASE = `http://localhost:${BACKEND_PORT}`
export const WS_BASE = `ws://localhost:${BACKEND_PORT}`
