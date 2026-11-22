import { useEffect, useState } from "react";

interface Ticket {
  id: number;
  customer_email: string;
  subject: string;
  category: string;
  urgency: string;
  status: string;
  escalation_reason: string | null;
  ai_confidence: number | null;
}

interface SupportEvent {
  id: number;
  sender_email: string;
  subject: string;
  status: string;
  skip_reason: string | null;
}

interface Policy {
  slug: string;
  title: string;
  category: string;
  content: string;
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [events, setEvents] = useState<SupportEvent[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);
  const [tab, setTab] = useState<"tickets" | "events" | "policies">("tickets");

  const fetchAll = async () => {
    const [tRes, eRes, pRes] = await Promise.all([
      fetch("/api/tickets"),
      fetch("/api/events"),
      fetch("/api/policies"),
    ]);
    if (tRes.ok) setTickets(await tRes.json());
    if (eRes.ok) setEvents(await eRes.json());
    if (pRes.ok) setPolicies(await pRes.json());
  };

  useEffect(() => {
    fetchAll();
  }, []);

  const markResolved = async (id: number) => {
    await fetch(`/api/tickets/${id}/resolve`, { method: "POST" });
    fetchAll();
  };

  const savePolicy = async () => {
    if (!selectedPolicy) return;
    await fetch(`/api/policies/${selectedPolicy.slug}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: selectedPolicy.title, content: selectedPolicy.content }),
    });
    setSelectedPolicy(null);
    fetchAll();
  };

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 1100, margin: "0 auto", padding: 24 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0 }}>Lumen Audio — AI Support Ops Console</h1>
          <p style={{ margin: "4px 0 0", color: "#64748b" }}>Autonomous Triage, Policy RAG & Human Escalation Queue</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setTab("tickets")}>Tickets ({tickets.length})</button>
          <button onClick={() => setTab("events")}>Audit Log ({events.length})</button>
          <button onClick={() => setTab("policies")}>Knowledge Base ({policies.length})</button>
          <button onClick={fetchAll}>Refresh</button>
        </div>
      </header>

      {tab === "tickets" && (
        <table border={1} cellPadding={10} style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead style={{ background: "#f1f5f9" }}>
            <tr>
              <th>ID</th>
              <th>Customer</th>
              <th>Subject</th>
              <th>Category</th>
              <th>Status</th>
              <th>Confidence</th>
              <th>Escalation / Action</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={t.id} style={{ background: t.status === "needs_review" ? "#fef3c7" : "white" }}>
                <td>#{t.id}</td>
                <td>{t.customer_email}</td>
                <td>{t.subject}</td>
                <td>{t.category || "-"}</td>
                <td><strong>{t.status}</strong></td>
                <td>{t.ai_confidence ? `${(t.ai_confidence * 100).toFixed(0)}%` : "-"}</td>
                <td>
                  {t.escalation_reason && <div style={{ fontSize: 12, color: "#b45309" }}>{t.escalation_reason}</div>}
                  {t.status === "needs_review" && (
                    <button onClick={() => markResolved(t.id)} style={{ marginTop: 4 }}>Mark Resolved</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === "events" && (
        <table border={1} cellPadding={10} style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead style={{ background: "#f1f5f9" }}>
            <tr>
              <th>ID</th>
              <th>Sender</th>
              <th>Subject</th>
              <th>Status</th>
              <th>Reason / Notes</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id}>
                <td>#{e.id}</td>
                <td>{e.sender_email}</td>
                <td>{e.subject}</td>
                <td><strong>{e.status}</strong></td>
                <td>{e.skip_reason || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === "policies" && (
        <div style={{ display: "grid", gap: 16 }}>
          {policies.map((p) => (
            <div key={p.slug} style={{ border: "1px solid #cbd5e1", padding: 16, borderRadius: 8 }}>
              <h3 style={{ marginTop: 0 }}>{p.title} ({p.slug})</h3>
              <pre style={{ whiteSpace: "pre-wrap", background: "#f8fafc", padding: 12 }}>{p.content}</pre>
              <button onClick={() => setSelectedPolicy(p)}>Edit Policy</button>
            </div>
          ))}
          {selectedPolicy && (
            <div style={{ border: "2px solid #2563eb", padding: 16, borderRadius: 8 }}>
              <h3 style={{ marginTop: 0 }}>Editing: {selectedPolicy.title}</h3>
              <textarea
                rows={10}
                style={{ width: "100%", marginBottom: 8 }}
                value={selectedPolicy.content}
                onChange={(e) => setSelectedPolicy({ ...selectedPolicy, content: e.target.value })}
              />
              <button onClick={savePolicy}>Save to Supabase</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
