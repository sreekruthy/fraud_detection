import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import { useState, useEffect } from "react";

function Dashboard() {

  const transactions = [
    { id: "TXN001", risk_score: 0.91 },
    { id: "TXN002", risk_score: 0.67 },
    { id: "TXN003", risk_score: 0.29 }
  ];

  const [alert, setAlert] = useState(null);

  useEffect(() => {
    const risky = transactions.find(t => t.risk_score >= 0.4);

    if (risky) {
      setAlert(risky);
    }
  }, []);

  const closeAlert = () => {
    setAlert(null);
  };

  return (
    <div style={{ display: "flex" }}>

      <Sidebar />

      <div style={{ flex: 1 }}>
        <Navbar />

        <div style={{ padding: "20px" }}>
          <h2>Dashboard</h2>
        </div>

        {/* 🔥 Popup Alert */}
        {alert && (
          <div style={{
            position: "fixed",
            top: "20px",
            right: "20px",
            background: alert.risk_score >= 0.7 ? "#fee2e2" : "#fef3c7",
            padding: "15px",
            borderRadius: "8px",
            boxShadow: "0 2px 10px rgba(0,0,0,0.2)",
            width: "250px"
          }}>

            <strong>
              {alert.risk_score >= 0.7 
                ? "🚨 Flagged Transaction" 
                : "⚠ Suspicious Transaction"}
            </strong>

            <p>Transaction: {alert.id}</p>
            <p>Risk Score: {alert.risk_score}</p>

            <button
              onClick={closeAlert}
              style={{
                marginTop: "10px",
                padding: "6px 10px",
                border: "none",
                background: "#333",
                color: "white",
                borderRadius: "4px",
                cursor: "pointer"
              }}
            >
              Close
            </button>

          </div>
        )}

      </div>

    </div>
  );
}

export default Dashboard;