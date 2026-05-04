import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../api/axiosConfig.js";

function useCountdown(expiresAt) {
  const [sec, setSec] = useState(null);
  useEffect(() => {
    if (!expiresAt) return;
    const target = new Date(expiresAt).getTime();
    const tick = () => setSec(Math.max(0, Math.floor((target - Date.now()) / 1000)));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAt]);
  return sec;
}

export default function VerifyTransaction() {
  const [params]                    = useSearchParams();
  const token                       = params.get("token");
  const autoResponse                = params.get("response");

  const [info, setInfo]             = useState(null);
  const [loading, setLoading]       = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult]         = useState(null);
  const [error, setError]           = useState(null);

  const secondsLeft = useCountdown(info?.hold_expires_at);
  const isFraud     = info?.decision === "FRAUD" || info?.purpose === "fraud_feedback";
  const windowOpen  = !isFraud && secondsLeft !== null && secondsLeft > 0;
  const windowExpired = !isFraud && secondsLeft === 0;

  useEffect(() => {
    if (!token) { setError("Missing verification link."); setLoading(false); return; }

    api.get(`/api/feedback/verify?token=${token}`)
      .then(res => {
        setInfo(res.data);
        setLoading(false);
        // Auto-submit if user clicked pre-answered email link and window still open
        if (autoResponse && !res.data.already_responded) {
          const isFraudTxn = res.data.decision === "FRAUD";
          // SUSPICIOUS: only auto-submit if window not expired
          if (isFraudTxn || new Date(res.data.hold_expires_at) > new Date()) {
            handleRespond(autoResponse);
          }
        }
      })
      .catch(err => {
        setError(err.response?.data?.detail || "Invalid or expired link.");
        setLoading(false);
      });
  }, [token]);

  const handleRespond = async (response) => {
    setSubmitting(true);
    try {
      const res = await api.post(`/api/feedback/respond?token=${token}&response=${response}`);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  };

  // Render helpers
  if (loading) return <Page><Card><Center>🔍<br/><br/>Verifying your link…</Center></Card></Page>;
  if (error)   return <Page><Card><Center>❌<br/><br/><strong>Link Error</strong><br/><br/><span style={{color:"#6b7280",fontSize:"14px"}}>{error}</span></Center></Card></Page>;

  // Already responded 
  if (info?.already_responded) return (
    <Page><Card>
      <Center>ℹ️<br/><br/><strong>Already Responded</strong><br/><br/>
        <span style={{color:"#6b7280",fontSize:"14px"}}>
          You already responded to transaction <strong>{info.transaction_id}</strong> as <strong>{info.feedback}</strong>.
        </span>
      </Center>
    </Card></Page>
  );

  // Result screen
  if (result) {
    const isLegit = result.feedback === "legitimate";
    return (
      <Page><Card>
        <div style={{ textAlign:"center", padding:"20px" }}>
          <div style={{ fontSize:"48px", marginBottom:"12px" }}>
            {isLegit ? "✅" : "🚫"}
          </div>
          <h2 style={{ color:"#111827", margin:"0 0 10px", fontSize:"20px" }}>
            {isFraud
              ? (isLegit ? "Response Recorded" : "Report Confirmed")
              : (isLegit ? "Transaction Confirmed" : "Transaction Blocked")}
          </h2>
          <p style={{ color:"#6b7280", fontSize:"14px", lineHeight:"1.6", margin:"0 0 20px" }}>
            {result.message}
          </p>
          <div style={{ background:"#f9fafb", border:"1px solid #e5e7eb", borderRadius:"8px", padding:"12px", fontSize:"13px", color:"#374151" }}>
            <strong>Transaction ID:</strong> {result.transaction_id}<br/>
            <strong>Status:</strong> {result.txn_status}
          </div>
          {isFraud && isLegit && (
            <div style={{ marginTop:"16px", background:"#eff6ff", border:"1px solid #bfdbfe", borderRadius:"8px", padding:"12px", fontSize:"13px", color:"#1d4ed8" }}>
              💡 To complete your payment, please <strong>initiate a new transaction</strong>. This blocked transaction cannot be reversed.
            </div>
          )}
        </div>
      </Card></Page>
    );
  }

  // Window expired (SUSPICIOUS only) 
  if (windowExpired && !isFraud) return (
    <Page><Card>
      <BannerBar color="#6b7280" text="⏰ Response Window Closed" />
      <Center>
        <strong style={{ fontSize:"16px" }}>The response window has expired.</strong><br/><br/>
        <span style={{ color:"#6b7280", fontSize:"14px" }}>
          An admin is reviewing your transaction history and will make a decision.
          You will be notified of the outcome.
        </span><br/><br/>
        <span style={{ fontSize:"12px", color:"#9ca3af" }}>Transaction ID: {info?.transaction_id}</span>
      </Center>
    </Card></Page>
  );

  //Main verify UI
  const triggered  = info?.explainability?.triggered_rules || [];
  const topFeats   = info?.explainability?.top_features || [];
  const scoreStr   = info ? `${(info.final_score * 100).toFixed(0)}%` : "—";
  const ts         = info?.timestamp ? new Date(info.timestamp).toLocaleString() : "—";
  const city       = info?.location?.city || "";
  const country    = info?.location?.country || "";

  return (
    <Page>
      <Card>
        {/* Banner */}
        <BannerBar
          color={isFraud ? "#dc2626" : "#d97706"}
          text={isFraud
            ? "🚨 CRITICAL — Transaction Blocked"
            : "⚠️ HIGH RISK — Transaction On Hold"}
        />

        {/* Countdown (SUSPICIOUS only) */}
        {!isFraud && secondsLeft !== null && secondsLeft > 0 && (
          <div style={{ background: secondsLeft < 30 ? "#fef2f2" : "#fffbeb", border:`1px solid ${secondsLeft < 30 ? "#fca5a5" : "#fde68a"}`, borderRadius:"8px", padding:"12px", textAlign:"center", marginBottom:"16px" }}>
            <div style={{ fontSize:"22px", fontWeight:"800", color: secondsLeft < 30 ? "#dc2626" : "#d97706", fontVariantNumeric:"tabular-nums" }}>
              ⏱ {Math.floor(secondsLeft/60)}:{(secondsLeft%60).toString().padStart(2,"0")}
            </div>
            <div style={{ fontSize:"12px", color: secondsLeft < 30 ? "#991b1b" : "#92400e", marginTop:"4px" }}>
              Time remaining to respond · Transaction is ON HOLD
            </div>
          </div>
        )}

        {/* FRAUD-specific blocked notice */}
        {isFraud && (
          <div style={{ background:"#fef2f2", border:"1px solid #fca5a5", borderRadius:"8px", padding:"12px 14px", marginBottom:"16px", textAlign:"center" }}>
            <div style={{ fontWeight:"700", color:"#dc2626", fontSize:"14px" }}>
              This transaction has been <strong>BLOCKED</strong>.
            </div>
            <div style={{ fontSize:"12px", color:"#991b1b", marginTop:"4px" }}>
              Your response below is for our records and helps improve fraud detection.
              It does not reverse the block.
            </div>
          </div>
        )}

        <h2 style={{ margin:"0 0 4px", fontSize:"18px", fontWeight:"800", color:"#111827" }}>
          {isFraud ? "Was This Transaction Yours?" : "Verify Your Transaction"}
        </h2>
        <p style={{ margin:"0 0 16px", fontSize:"13px", color:"#6b7280" }}>
          {isFraud
            ? "Please confirm whether you attempted this transaction. This helps us improve our system."
            : "This transaction is ON HOLD. Confirm below and it will be processed or cancelled."}
        </p>

        {/* Transaction details */}
        <div style={{ background:"#f9fafb", border:"1px solid #e5e7eb", borderRadius:"8px", padding:"14px", marginBottom:"14px" }}>
          <div style={{ fontSize:"10px", fontWeight:"700", color:"#9ca3af", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"8px" }}>Transaction Details</div>
          {[
            ["ID",       info?.transaction_id],
            ["Amount",   `$${(info?.amount||0).toLocaleString("en-US",{minimumFractionDigits:2})} USD`],
            ["Location", `${city}, ${country}`],
            ["Time",     ts],
            ["Risk",     <span style={{color: isFraud?"#dc2626":"#d97706", fontWeight:"700"}}>{scoreStr} — {info?.decision}</span>],
          ].map(([k,v]) => (
            <div key={k} style={{ display:"flex", justifyContent:"space-between", fontSize:"13px", padding:"4px 0", borderBottom:"1px solid #e5e7eb" }}>
              <span style={{ color:"#6b7280" }}>{k}</span>
              <span style={{ color:"#111827", fontWeight:"500" }}>{v}</span>
            </div>
          ))}
        </div>

        {/* Triggered rules */}
        {triggered.length > 0 && (
          <div style={{ background: isFraud?"#fef2f2":"#fffbeb", border:`1px solid ${isFraud?"#fca5a5":"#fde68a"}`, borderRadius:"8px", padding:"12px", marginBottom:"14px" }}>
            <div style={{ fontSize:"10px", fontWeight:"700", color: isFraud?"#991b1b":"#92400e", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"6px" }}>
              {isFraud ? "Why This Was Blocked" : "Why This Was Flagged"}
            </div>
            {triggered.map((r,i) => <div key={i} style={{ fontSize:"13px", color: isFraud?"#7f1d1d":"#78350f", marginBottom:"3px" }}>• {r}</div>)}
            {isFraud && topFeats.length > 0 && (
              <div style={{ fontSize:"11px", color:"#9ca3af", marginTop:"6px" }}>
                Key factors: <strong>{topFeats.join(", ")}</strong>
              </div>
            )}
          </div>
        )}

        {/* On-hold notice (SUSPICIOUS) */}
        {!isFraud && (
          <div style={{ background:"#eff6ff", border:"1px solid #bfdbfe", borderRadius:"8px", padding:"10px 12px", marginBottom:"16px", fontSize:"13px", color:"#1d4ed8", textAlign:"center" }}>
            ⏸ This transaction is <strong>ON HOLD</strong>. Your response determines whether it's processed or cancelled.
          </div>
        )}

        {/* Action buttons */}
        {submitting ? (
          <div style={{ textAlign:"center", padding:"16px", color:"#6b7280", fontSize:"14px" }}>Processing your response…</div>
        ) : (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"10px" }}>
            <button onClick={() => handleRespond("legitimate")}
              style={{ padding:"13px", background:"#16a34a", color:"white", border:"none", borderRadius:"8px", fontSize:"14px", fontWeight:"700", cursor:"pointer" }}>
              {isFraud ? "✅ Yes — I'll redo it" : "✅ Yes, this was me"}
            </button>
            <button onClick={() => handleRespond("fraud")}
              style={{ padding:"13px", background:"#dc2626", color:"white", border:"none", borderRadius:"8px", fontSize:"14px", fontWeight:"700", cursor:"pointer" }}>
              {isFraud ? "❌ No — This wasn't me" : "❌ No, this wasn't me"}
            </button>
          </div>
        )}

        <p style={{ fontSize:"11px", color:"#9ca3af", textAlign:"center", marginTop:"14px", marginBottom:0 }}>
          {isFraud
            ? "Link valid for 7 days. Your response is for records only — does not unblock the transaction."
            : "Link valid while window is open. Contact support if expired."}
        </p>
      </Card>
    </Page>
  );
}

function Page({ children }) {
  return (
    <div style={{ minHeight:"100vh", background:"#f3f4f6", display:"flex", alignItems:"center", justifyContent:"center", padding:"20px", fontFamily:"'Segoe UI',system-ui,sans-serif" }}>
      {children}
    </div>
  );
}

function Card({ children }) {
  return (
    <div style={{ background:"white", borderRadius:"12px", boxShadow:"0 4px 24px rgba(0,0,0,0.1)", padding:"24px", width:"100%", maxWidth:"480px" }}>
      {children}
    </div>
  );
}

function BannerBar({ color, text }) {
  return (
    <div style={{ background:color, borderRadius:"8px 8px 0 0", padding:"14px 20px", margin:"-24px -24px 18px", textAlign:"center" }}>
      <span style={{ color:"white", fontWeight:"700", fontSize:"15px" }}>{text}</span>
    </div>
  );
}

function Center({ children }) {
  return <div style={{ textAlign:"center", padding:"24px 0", fontSize:"15px", color:"#374151", lineHeight:"1.8" }}>{children}</div>;
}