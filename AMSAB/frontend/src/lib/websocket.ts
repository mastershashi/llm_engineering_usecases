export type WsEventType =
  | "plan_created"
  | "plan_approved"
  | "node_started"
  | "node_completed"
  | "node_failed"
  | "node_awaiting_approval"
  | "plan_completed"
  | "plan_failed"
  | "log_line"
  | "token_update";

export interface WsEvent {
  event: WsEventType;
  plan_id: string;
  data: Record<string, unknown>;
  timestamp: string;
}

type EventHandler = (event: WsEvent) => void;

export class PlanSocket {
  private ws: WebSocket | null = null;
  private handlers: Map<WsEventType | "*", EventHandler[]> = new Map();
  private pingInterval: ReturnType<typeof setInterval> | null = null;

  constructor(private planId: string) {}

  connect(): this {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    // Use same host+port as the page — Next.js proxies /ws/* to the backend
    const host = window.location.host;
    this.ws = new WebSocket(`${proto}://${host}/ws/plans/${this.planId}`);

    this.ws.onmessage = (ev) => {
      try {
        const event: WsEvent = JSON.parse(ev.data);
        this.emit(event);
      } catch {
        // ignore malformed
      }
    };

    this.ws.onopen = () => {
      this.pingInterval = setInterval(() => this.ws?.send("ping"), 25_000);
    };

    this.ws.onclose = () => {
      if (this.pingInterval) clearInterval(this.pingInterval);
      // Reconnect after 2s
      setTimeout(() => this.connect(), 2000);
    };

    return this;
  }

  on(event: WsEventType | "*", handler: EventHandler): this {
    const list = this.handlers.get(event) ?? [];
    list.push(handler);
    this.handlers.set(event, list);
    return this;
  }

  off(event: WsEventType | "*", handler: EventHandler): this {
    const list = this.handlers.get(event) ?? [];
    this.handlers.set(event, list.filter((h) => h !== handler));
    return this;
  }

  disconnect(): void {
    if (this.pingInterval) clearInterval(this.pingInterval);
    this.ws?.close();
    this.ws = null;
  }

  private emit(event: WsEvent): void {
    [...(this.handlers.get(event.event) ?? []), ...(this.handlers.get("*") ?? [])].forEach((h) =>
      h(event)
    );
  }
}
