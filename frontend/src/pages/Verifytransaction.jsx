import { useSearchParams } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import api from "../api/axiosConfig";

// ---------------- COUNTDOWN HOOK ----------------
function useCountdown(expiresAt) {
  const [secondsLeft, setSecondsLeft] = useState(null);

  useEffect(() => {
    if (!expiresAt) return;

    const target = new Date(expiresAt).getTime();

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

// ---------------- COMPONENT ----------------
export default function VerifyTransaction() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const autoResponse = searchParams.get("response");

  const [info, setInfo] = useState(null);
  const [secondsLeft, setSecondsLeft] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ---------------- HANDLE RESPONSE ----------------
  const handleRespond = useCallback(async (response) => {
    try {
      const res = await api.post(
        `/api/feedback/respond?token=${token}&response=${response}`
      );

      setResult(res.data);

    } catch {
      alert("Submission failed");
    }
  }, [token]);

  // ---------------- FETCH DATA ----------------
  useEffect(() => {
    if (!token) {
      setError("Invalid link");
      setLoading(false);
      return;
    }

    api.get(`/api/feedback/verify?token=${token}`)
      .then(res => {
        setInfo(res.data);

        const expiry = new Date(res.data.hold_expires_at || 0);
        setSecondsLeft(Math.max(0, Math.floor((expiry - new Date()) / 1000)));

        // Auto respond (from email links)
        if (autoResponse && !res.data.already_responded) {
          handleRespond(autoResponse);
        }
      })
      .catch(() => setError("Link expired or invalid"))
      .finally(() => setLoading(false));

  }, [token, autoResponse, handleRespond]);

  // ---------------- COUNTDOWN ----------------
  const countdown = useCountdown(info?.hold_expires_at);

  // ---------------- STATES ----------------
  if (loading) return <Screen message="Loading..." />;
  if (error) return <Screen message={error} />;

  if (info?.already_responded) {
    return <Screen message={`Already responded: ${info.feedback}`} />;
  }

  if (result) {
    return (
      <Screen
        message={
          <>
            <h2>Response Recorded</h2>
            <p>Transaction: {result.transaction_id}</p>
            <p>Status: {result.txn_status}</p>
            <p>Feedback: {result.feedback}</p>
          </>
        }
      />
    );
  }

  // ---------------- MODE ----------------
  const isFraud =
    info?.decision === "FRAUD" || info?.purpose === "fraud_feedback";

  const isExpired = countdown === 0 && !isFraud;

  if (isExpired) {
    return <Screen message="Response window expired" />;
  }

  // ---------------- UI ----------------
  return (
    <div style={wrapper}>

      {/* HEADER */}
      <div style={header}>
        <h2>Transaction Verification</h2>
      </div>

      {/* TRANSACTION INFO */}
      <div style={card}>
        <p><b>ID:</b> {info.transaction_id}</p>
        <p><b>Amount:</b> ${info.amount}</p>
        <p><b>Status:</b> {info.decision}</p>

        {info.final_score !== undefined && (
          <p><b>Risk Score:</b> {info.final_score}</p>
        )}

        {info.hold_expires_at && !isFraud && (
          <p>
            <b>Time left:</b>{" "}
            <span style={countdownStyle(countdown)}>
              {countdown}s
            </span>
          </p>
        )}
      </div>

      {/* EXPLAINABILITY */}
      {info.explainability && (
        <div style={card}>
          <h4>Why flagged?</h4>

          <p>
            <b>Rules:</b>{" "}
            {info.explainability.triggered_rules?.join(", ") || "N/A"}
          </p>

          <p>
            <b>Top Features:</b>{" "}
            {info.explainability.top_features?.join(", ") || "N/A"}
          </p>
        </div>
      )}

      {/* ACTIONS */}
      <div style={card}>
        <h4>{isFraud ? "Confirm Fraud" : "Is this your transaction?"}</h4>

        <div style={{ marginTop: "15px" }}>
          <button
            style={btnGreen}
            onClick={() => handleRespond("legitimate")}
          >
            Yes
          </button>

          <button
            style={btnRed}
            onClick={() => handleRespond("fraud")}
          >
            No
          </button>
        </div>
      </div>

    </div>
  );
}

// ---------------- REUSABLE SCREEN ----------------
function Screen({ message }) {
  return (
    <div style={center}>
      <div style={card}>
        {typeof message === "string" ? <h3>{message}</h3> : message}
      </div>
    </div>
  );
}

// ---------------- STYLES ----------------
const wrapper = {
  minHeight: "100vh",
  background: "#0f172a",
  padding: "20px",
  color: "white"
};

const header = {
  marginBottom: "20px"
};

const card = {
  background: "#1e293b",
  padding: "20px",
  borderRadius: "10px",
  marginBottom: "15px"
};

const center = {
  minHeight: "100vh",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  background: "#0f172a",
  color: "white"
};

const btnGreen = {
  background: "#16a34a",
  color: "white",
  border: "none",
  padding: "10px 15px",
  marginRight: "10px",
  borderRadius: "6px"
};

const btnRed = {
  background: "#dc2626",
  color: "white",
  border: "none",
  padding: "10px 15px",
  borderRadius: "6px"
};

const countdownStyle = (sec) => ({
  color: sec < 60 ? "#dc2626" : "#f59e0b",
  fontWeight: "bold"
});