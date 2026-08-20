import ws from "k6/ws";
import { check } from "k6";

const baseUrl = (__ENV.BASE_URL || "http://nginx").replace(/^http/, "ws");

export const options = {
  scenarios: {
    live_connections: {
      executor: "constant-vus",
      vus: Number(__ENV.WS_VUS || 100),
      duration: __ENV.DURATION || "5m",
    },
  },
  thresholds: {
    ws_connecting: ["p(95)<500"],
    ws_session_duration: ["p(95)>1000"],
  },
};

export default function () {
  const origin = baseUrl.replace(/^ws/, "http");
  const response = ws.connect(`${baseUrl}/ws/comments`, { headers: { Origin: origin } }, (socket) => {
    socket.on("open", () => socket.send(JSON.stringify({ operation: "ping", data: {} })));
    socket.setTimeout(
      () => socket.close(),
      Number(__ENV.WS_HOLD_SECONDS || 30) * 1000,
    );
  });
  check(response, { "WebSocket upgrades": (result) => result?.status === 101 });
}
