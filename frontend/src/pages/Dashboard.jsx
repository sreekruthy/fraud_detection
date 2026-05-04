import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { useEffect, useState, useCallback, useRef } from "react";
import api from "../api/axiosConfig.js";


//  Countdown hook 
function useCountdown(expiresAt) {
  const [secondsLeft, setSecondsLeft] = useState(null);

  useEffect(() => {
    if (!expiresAt) return;
    const normalized =
      typeof expiresAt === "string" && !expiresAt.endsWith("Z") && !expiresAt.includes("+")
        ? expiresAt + "Z"
        : expiresAt;
    const target = new Date(normalized).getTime();

    const tick = () => {
      const diff = Math.floor((target - Date.now()) / 1000);
      setSecondsLeft(Math.max(0, diff));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAt]);

  return secondsLeft;
}

// CountdownBadge component 
function CountdownBadge({ sec }) {

  if (sec === null) return null;  // early return AFTER all hooks

  const mins = Math.floor(sec / 60);
  const secs = sec % 60;

  if (sec === 0) return (
    <span style={{ background:"#dc2626", color:"white", padding:"3px 10px", borderRadius:"99px", fontSize:"11px", fontWeight:"700" }}>
      ⏰ Window Expired — Admin Action Required
    </span>
  );

  return (
    <span style={{
      background: sec < 30 ? "#dc2626" : "#d97706",
      color:"white", padding:"3px 10px", borderRadius:"99px",
      fontSize:"11px", fontWeight:"700", fontVariantNumeric:"tabular-nums"
    }}>
      ⏱ {mins}:{secs.toString().padStart(2, "0")} remaining
    </span>
  );
}

// HistorySummary component 
function HistorySummary({ summary }) {
  const [open, setOpen] = useState(false);
  if (!summary || summary.total === 0) return (
    <span style={{ fontSize:"12px", color:"#64748b" }}>No transaction history</span>
  );

  return (
    <div>
      <button
        onClick={() => setOpen(o => !o)}
        style={{ background:"#334155", border:"none", color:"#94a3b8", padding:"4px 10px", borderRadius:"4px", cursor:"pointer", fontSize:"11px" }}
      >
        📊 User History ({summary.total} txns) {open ? "▲" : "▼"}
      </button>
      {open && (
        <div style={{ marginTop:"8px", background:"#0f172a", borderRadius:"6px", padding:"12px", fontSize:"12px" }}>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(4, 1fr)", gap:"8px", marginBottom:"10px" }}>
            {[
              { label:"Total Txns",    value: summary.total },
              { label:"Avg Amount",    value: `$${(summary.avg_amount || 0).toLocaleString()}` },
              { label:"Fraud Count",   value: summary.fraud_count,     color: summary.fraud_count > 0 ? "#ef4444" : "#94a3b8" },
              { label:"Avg Risk",      value: `${((summary.avg_risk_score || 0)*100).toFixed(0)}%`, color: summary.avg_risk_score > 0.5 ? "#ef4444" : "#22c55e" },
            ].map(s => (
              <div key={s.label} style={{ textAlign:"center" }}>
                <div style={{ fontWeight:"700", color: s.color || "white" }}>{s.value}</div>
                <div style={{ color:"#64748b", fontSize:"10px" }}>{s.label}</div>
              </div>
            ))}
          </div>
          {summary.recent?.length > 0 && (
            <div>
              <div style={{ color:"#64748b", marginBottom:"4px", fontSize:"10px", textTransform:"uppercase", letterSpacing:"0.5px" }}>Recent transactions</div>
              {summary.recent.map((t, i) => (
                <div key={i} style={{ display:"flex", justifyContent:"space-between", padding:"3px 0", borderBottom:"1px solid #1e293b", color:"#94a3b8" }}>
                  <span>{t.transaction_id}</span>
                  <span>${(t.amount || 0).toLocaleString()}</span>
                  <span style={{ color: t.decision === "FRAUD" ? "#ef4444" : t.decision === "SUSPICIOUS" ? "#f59e0b" : "#22c55e" }}>{t.decision}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function AlertActionsWithTimer({ alert, loading_key, handleAction, setSelectedTxn }) {
  const sec = useCountdown(alert.hold_expires_at);  // countdown lives here
  const expired = sec === 0;

  return (
    <div style={{ marginTop:"8px" }}>
      <div style={{ marginBottom:"8px" }}>
        <CountdownBadge sec={sec} />
      </div>

      {expired && alert.history_summary && (
        <div style={{ marginBottom:"10px" }}>
          <div style={{ fontSize:"12px", color:"#f59e0b", fontWeight:"600", marginBottom:"6px" }}>
            ⚠️ User did not respond. Review their history before deciding:
          </div>
          <HistorySummary summary={alert.history_summary} />
        </div>
      )}
      {!expired && sec !== null && (
        <div style={{ fontSize:"12px", color:"#64748b", marginBottom:"8px" }}>
          Waiting for user response… You can also act now if needed.
        </div>
      )}
      <div style={{ display:"flex", gap:"8px" }}>
        <button onClick={() => setSelectedTxn(alert)}
          style={{ padding:"6px 12px", background:"#334155", border:"none", color:"#e2e8f0", borderRadius:"6px", cursor:"pointer", fontSize:"12px" }}>
          View Details
        </button>
        <button onClick={() => handleAction(alert.transaction_id, "PERMIT")}
          disabled={!!loading_key}
          style={{ padding:"6px 14px", background: loading_key === "PERMIT" ? "#166534" : "#16a34a", border:"none", color:"white", borderRadius:"6px", cursor:"pointer", fontSize:"12px", fontWeight:"600" }}>
          {loading_key === "PERMIT" ? "…" : "✅ Permit"}
        </button>
        <button onClick={() => handleAction(alert.transaction_id, "BLOCK")}
          disabled={!!loading_key}
          style={{ padding:"6px 14px", background: loading_key === "BLOCK" ? "#7f1d1d" : "#dc2626", border:"none", color:"white", borderRadius:"6px", cursor:"pointer", fontSize:"12px", fontWeight:"600" }}>
          {loading_key === "BLOCK" ? "…" : "🚫 Block"}
        </button>
      </div>
    </div>
  );
}


// Main Dashboard
export default function Dashboard() {
  const navigate                    = useNavigate();
  const [alerts, setAlerts]         = useState([]);
  const [flaggedTxns, setFlaggedTxns] = useState([]);
  const [stats, setStats]           = useState(null);
  const [loading, setLoading]       = useState(true);
  const [activeTab, setActiveTab]   = useState("alerts");
  const [actionLoading, setActionLoading] = useState({});
  const [selectedTxn, setSelectedTxn] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [alertRes, allAlertRes, txnRes] = await Promise.all([
        api.get("/api/alerts/?status=OPEN"),
        api.get("/api/alerts/"),
        api.get("/api/transactions/flagged"),
      ]);
      const alertData = alertRes.data.alerts || [];
      const allAlertData = allAlertRes.data.alerts || [];
      const txnData   = txnRes.data.transactions || [];
      setAlerts(alertData);
      setFlaggedTxns(txnData);
      setStats({
        open:      alertData.length,
        critical:  alertData.filter(a => a.severity === "CRITICAL").length,
        high:      alertData.filter(a => a.severity === "HIGH").length,
        flagged:   txnData.length,
        onHold:    txnData.filter(t => t.txn_status === "ON_HOLD").length,
      });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 15000);
    return () => clearInterval(id);
  }, [fetchData]);

  const handleAction = async (txnId, action) => {
    setActionLoading(p => ({ ...p, [txnId]: action }));
    try {
      await api.post("/api/feedback/admin-action", { transaction_id: txnId, action });
      await fetchData();
    } catch (e) {
      alert("Error: " + (e.response?.data?.detail || e.message));
    } finally {
      setActionLoading(p => ({ ...p, [txnId]: null }));
    }
  };

  if (loading) return (
    <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:"100vh", background:"#0f172a", color:"white" }}>
      Loading…
    </div>
  );

  return (
    <div style={{ minHeight:"100vh", background:"#0f172a", color:"white", fontFamily:"'Segoe UI',system-ui,sans-serif" }}>

      {/* Topbar */}
      <div style={{ background:"#1e293b", borderBottom:"1px solid #334155", height:"58px", display:"flex", alignItems:"center", justifyContent:"space-between", padding:"0 24px" }}>
        <div style={{ display:"flex", alignItems:"center", gap:"10px" }}>
          <span style={{ fontSize:"20px" }}>🛡</span>
          <span style={{ fontWeight:"700", fontSize:"15px" }}>FraudShield Admin</span>
          {stats?.open > 0 && (
            <span style={{ background:"#dc2626", color:"white", borderRadius:"99px", padding:"2px 8px", fontSize:"11px", fontWeight:"700" }}>
              {stats.open} open
            </span>
          )}
        </div>
        <div style={{ display:"flex", gap:"10px" }}>
          <button onClick={fetchData} style={{ background:"#334155", border:"none", color:"#94a3b8", padding:"6px 12px", borderRadius:"6px", cursor:"pointer", fontSize:"12px" }}>↻ Refresh</button>
          <button onClick={() => { localStorage.removeItem("isLoggedIn"); navigate("/"); }} style={{ background:"#ef4444", border:"none", color:"white", padding:"6px 14px", borderRadius:"6px", cursor:"pointer", fontSize:"12px", fontWeight:"600" }}>Logout</button>
        </div>
      </div>

      <div style={{ padding:"24px", maxWidth:"1280px", margin:"0 auto" }}>

        {/* Stats */}
        {stats && (
          <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:"12px", marginBottom:"24px" }}>
            {[
              { label:"Open Alerts",  value:stats.open,     color:"#f59e0b", icon:"🔔" },
              { label:"Critical",     value:stats.critical, color:"#ef4444", icon:"🚨" },
              { label:"High Risk",    value:stats.high,     color:"#f59e0b", icon:"⚠️" },
              { label:"Flagged",      value:stats.flagged,  color:"#8b5cf6", icon:"🚩" },
              { label:"On Hold",      value:stats.onHold,   color:"#06b6d4", icon:"⏸" },
            ].map((s,i) => (
              <div key={i} style={{ background:"#1e293b", border:"1px solid #334155", borderRadius:"10px", padding:"16px" }}>
                <div style={{ fontSize:"18px", marginBottom:"6px" }}>{s.icon}</div>
                <div style={{ fontSize:"26px", fontWeight:"800", color:s.color }}>{s.value}</div>
                <div style={{ fontSize:"11px", color:"#64748b", marginTop:"3px" }}>{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div style={{ display:"flex", gap:"4px", marginBottom:"18px", background:"#1e293b", padding:"4px", borderRadius:"8px", width:"fit-content" }}>
          {[
            { id:"alerts",       label:`🔔 Open Alerts (${alerts.length})` },
            { id:"transactions", label:`🚩 Flagged (${flaggedTxns.length})` },
          ].map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              padding:"7px 16px",
              background: activeTab === t.id ? "#3b82f6" : "transparent",
              color:      activeTab === t.id ? "white" : "#64748b",
              border:"none", borderRadius:"6px", cursor:"pointer", fontSize:"12px", fontWeight:"600"
            }}>{t.label}</button>
          ))}
        </div>

        {/* ── Alerts Tab ── */}
        {activeTab === "alerts" && (
          <div style={{ display:"flex", flexDirection:"column", gap:"12px" }}>
            {alerts.length === 0 && (
              <div style={{ background:"#1e293b", border:"1px solid #334155", borderRadius:"10px", padding:"40px", textAlign:"center", color:"#64748b" }}>
                <div style={{ fontSize:"28px", marginBottom:"6px" }}>✅</div>No open alerts
              </div>
            )}

            {alerts.map((alert, i) => {
              const isFraud     = alert.decision === "FRAUD";
              const accentColor = isFraud ? "#ef4444" : "#f59e0b";
              const loading_key = actionLoading[alert.transaction_id];

              return (
                <div key={i} style={{
                  background:"#1e293b",
                  border:`1px solid ${accentColor}44`,
                  borderLeft:`4px solid ${accentColor}`,
                  borderRadius:"10px", padding:"18px 20px"
                }}>

                  {/* Top row */}
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:"10px" }}>
                    <div style={{ display:"flex", gap:"10px", alignItems:"center" }}>
                      <span style={{ fontSize:"18px" }}>{isFraud ? "🚨" : "⚠️"}</span>
                      <div>
                        <span style={{ fontWeight:"700", fontSize:"15px" }}>
                          {alert.decision}
                        </span>
                        <span style={{ color:"#64748b", fontSize:"13px", marginLeft:"8px" }}>
                          ${(alert.amount || 0).toLocaleString("en-US", { minimumFractionDigits:2 })} · {alert.user_id} · {alert.transaction_id}
                        </span>
                      </div>
                    </div>
                    <div style={{ display:"flex", gap:"6px", alignItems:"center", flexShrink:0 }}>
                      <span style={{ background:accentColor, color:"white", padding:"2px 9px", borderRadius:"99px", fontSize:"10px", fontWeight:"700" }}>
                        {alert.severity}
                      </span>
                    
                      {isFraud && (
                        <span style={{ background:"#334155", color:"#94a3b8", padding:"2px 9px", borderRadius:"99px", fontSize:"10px" }}>
                          AUTO-BLOCKED
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Scores */}
                  <div style={{ display:"flex", gap:"14px", fontSize:"12px", color:"#94a3b8", marginBottom:"10px" }}>
                    <span>Final <strong style={{ color:"white" }}>{((alert.final_score||0)*100).toFixed(0)}%</strong></span>
                    <span>ML <strong style={{ color:"white" }}>{((alert.ml_score||0)*100).toFixed(0)}%</strong></span>
                    <span>Rules <strong style={{ color:"white" }}>{((alert.rule_score||0)*100).toFixed(0)}%</strong></span>
                  </div>

                  {/* Triggered rules */}
                  {alert.explainability?.triggered_rules?.length > 0 && (
                    <div style={{ background:"#0f172a", borderRadius:"6px", padding:"10px 12px", marginBottom:"10px" }}>
                      <div style={{ fontSize:"10px", color:"#64748b", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"5px" }}>Why flagged</div>
                      {alert.explainability.triggered_rules.map((r, j) => (
                        <div key={j} style={{ fontSize:"12px", color:"#e2e8f0", marginBottom:"2px" }}>• {r}</div>
                      ))}
                    </div>
                  )}

                  {!isFraud && (
                    <AlertActionsWithTimer
                    alert={alert}
                    loading_key={loading_key}
                    handleAction={handleAction}
                    setSelectedTxn={setSelectedTxn}
                    />
                    )}

                  {/* FRAUD: informational only */}
                  {isFraud && (
                    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                      <span style={{ fontSize:"12px", color:"#94a3b8" }}>
                        Transaction auto-blocked. Informational email sent to user.
                      </span>
                      <button onClick={() => setSelectedTxn(alert)}
                      style={{ padding:"5px 12px", background:"#334155", border:"none", color:"#e2e8f0", borderRadius:"6px", cursor:"pointer", fontSize:"12px" }}>
                        View Details
                        </button>
                    </div>
                  )}

                </div>
              );
            })}
          </div>
        )}

        {/* ── Flagged Transactions Tab ── */}
        {activeTab === "transactions" && (
          <div>
            {flaggedTxns.length === 0 ? (
              <div style={{ background:"#1e293b", border:"1px solid #334155", borderRadius:"10px", padding:"40px", textAlign:"center", color:"#64748b" }}>
                No flagged transactions
              </div>
            ) : (
              <div style={{ background:"#1e293b", border:"1px solid #334155", borderRadius:"10px", overflow:"hidden" }}>
                <table style={{ width:"100%", borderCollapse:"collapse" }}>
                  <thead>
                    <tr style={{ background:"#0f172a", borderBottom:"1px solid #334155" }}>
                      {["Txn ID","User","Amount","Decision","Score","Status","Feedback","Action"].map(h => (
                        <th key={h} style={{ padding:"10px 14px", textAlign:"left", fontSize:"10px", color:"#64748b", fontWeight:"700", textTransform:"uppercase", letterSpacing:"0.5px" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {flaggedTxns.map((txn, i) => {
                      const isFraud = txn.decision === "FRAUD";
                      const c       = isFraud ? "#ef4444" : "#f59e0b";
                      const statusColors = {
                        ON_HOLD:"#f59e0b", BLOCKED:"#ef4444",
                        CONFIRMED_LEGIT:"#22c55e", PROCESSED:"#22c55e"
                      };
                      return (
                        <tr key={i} style={{ borderBottom:"1px solid #0f172a" }}
                          onMouseEnter={e => e.currentTarget.style.background="#0f172a"}
                          onMouseLeave={e => e.currentTarget.style.background="transparent"}>
                          <td style={{ padding:"10px 14px", fontSize:"12px", color:"#94a3b8", cursor:"pointer" }} onClick={() => setSelectedTxn(txn)}>
                            {txn.transaction_id}
                          </td>
                          <td style={{ padding:"10px 14px", fontSize:"12px" }}>{txn.user_id}</td>
                          <td style={{ padding:"10px 14px", fontSize:"12px", fontWeight:"600" }}>${(txn.amount||0).toLocaleString("en-US",{minimumFractionDigits:2})}</td>
                          <td style={{ padding:"10px 14px" }}>
                            <span style={{ color:c, fontWeight:"700", fontSize:"12px" }}>{isFraud?"🚨":"⚠️"} {txn.decision}</span>
                          </td>
                          <td style={{ padding:"10px 14px", fontSize:"12px", color:c, fontWeight:"700" }}>
                            {txn.final_score != null ? `${(txn.final_score*100).toFixed(0)}%` : "—"}
                          </td>
                          <td style={{ padding:"10px 14px", fontSize:"12px", color: statusColors[txn.txn_status] || "#94a3b8" }}>
                            {txn.txn_status}
                          </td>
                          <td style={{ padding:"10px 14px", fontSize:"11px", color:"#64748b" }}>
                            {txn.customer_feedback || "—"}
                          </td>
                          <td style={{ padding:"10px 14px" }}>
                            {txn.txn_status === "ON_HOLD" && !isFraud && (
                              <div style={{ display:"flex", gap:"4px" }}>
                                <button onClick={() => handleAction(txn.transaction_id,"PERMIT")}
                                  disabled={!!actionLoading[txn.transaction_id]}
                                  style={{ padding:"3px 8px", background:"#16a34a", border:"none", color:"white", borderRadius:"4px", cursor:"pointer", fontSize:"10px" }}>Permit</button>
                                <button onClick={() => handleAction(txn.transaction_id,"BLOCK")}
                                  disabled={!!actionLoading[txn.transaction_id]}
                                  style={{ padding:"3px 8px", background:"#dc2626", border:"none", color:"white", borderRadius:"4px", cursor:"pointer", fontSize:"10px" }}>Block</button>
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
        {/* ── Transaction Detail Modal ── */}
{selectedTxn && (
  <div style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.7)", zIndex:1000, display:"flex", alignItems:"center", justifyContent:"center", padding:"20px" }}
    onClick={() => setSelectedTxn(null)}>
    <div style={{ background:"#1e293b", border:"1px solid #334155", borderRadius:"14px", padding:"28px", width:"100%", maxWidth:"520px", color:"white" }}
      onClick={e => e.stopPropagation()}>

      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h3 style={{ margin:0, fontSize:"16px", fontWeight:"700" }}>
          {selectedTxn.decision === "FRAUD" ? "🚨" : "⚠️"} Transaction Details
        </h3>
        <button onClick={() => setSelectedTxn(null)}
          style={{ background:"#334155", border:"none", color:"#94a3b8", padding:"4px 10px", borderRadius:"6px", cursor:"pointer", fontSize:"14px" }}>✕</button>
      </div>

      {/* Details grid */}
      {[
        ["Transaction ID", selectedTxn.transaction_id],
        ["User ID",        selectedTxn.user_id],
        ["Amount",         `$${(selectedTxn.amount||0).toLocaleString("en-US",{minimumFractionDigits:2})}`],
        ["Decision",       selectedTxn.decision],
        ["Status",         selectedTxn.txn_status],
        ["Risk Score",     `${((selectedTxn.final_score||0)*100).toFixed(0)}%`],
        ["ML Score",       `${((selectedTxn.ml_score||0)*100).toFixed(0)}%`],
        ["Rules Score",    `${((selectedTxn.rule_score||0)*100).toFixed(0)}%`],
        ["Location",       selectedTxn.location ? `${selectedTxn.location.city}, ${selectedTxn.location.country}` : "—"],
        ["Device",         selectedTxn.device?.browser || "—"],
        ["IP",             selectedTxn.device?.ip || "—"],
        ["Feedback",       selectedTxn.customer_feedback || "—"],
      ].map(([k, v]) => (
        <div key={k} style={{ display:"flex", justifyContent:"space-between", padding:"8px 0", borderBottom:"1px solid #334155", fontSize:"13px" }}>
          <span style={{ color:"#64748b" }}>{k}</span>
          <span style={{ fontWeight:"600", color: k==="Decision" && selectedTxn.decision==="FRAUD" ? "#ef4444" : k==="Decision" ? "#f59e0b" : "white" }}>{v}</span>
        </div>
      ))}

      {/* Triggered rules */}
      {selectedTxn.explainability?.triggered_rules?.length > 0 && (
        <div style={{ marginTop:"16px" }}>
          <div style={{ fontSize:"11px", color:"#64748b", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"8px" }}>Why Flagged</div>
          {selectedTxn.explainability.triggered_rules.map((r, i) => (
            <div key={i} style={{ fontSize:"12px", color:"#e2e8f0", marginBottom:"4px" }}>• {r}</div>
          ))}
        </div>
      )}

      <button onClick={() => setSelectedTxn(null)}
        style={{ marginTop:"20px", width:"100%", padding:"10px", background:"#334155", border:"none", color:"white", borderRadius:"8px", cursor:"pointer", fontSize:"13px" }}>
        Close
      </button>
    </div>
  </div>
)}

      </div>
    </div>
  );
}