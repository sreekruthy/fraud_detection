import { useParams, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { useEffect, useState } from "react";
import api from "../api/axiosConfig";

function Transaction() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [transaction, setTransaction] = useState(null);

  useEffect(() => {
    api.get(`/api/transactions/${id}`)
      .then(res => setTransaction(res.data))   // ✅ FIXED
      .catch(err => console.log(err));
  }, [id]);

  if (!transaction) {
    return <h3 style={{ color: "white" }}>Loading...</h3>;
  }

  // ✅ SAFE risk handling
  const risk = transaction.risk_score ?? 0;

  let status = "";
  let color = "";

  if (risk < 0.4) {
    status = "Safe";
    color = "green";
  } else if (risk < 0.7) {
    status = "Suspicious";
    color = "orange";
  } else {
    status = "Fraud";
    color = "red";
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div style={{ padding: "30px", flex: 1, background: "#0f172a", color: "white" }}>
        <h2>Transaction Details</h2>

        <div style={{
          marginTop: "20px",
          padding: "20px",
          background: "#1e293b",
          width: "420px",
          borderRadius: "10px",
          border: "1px solid #334155"
        }}>

          <p><b>Transaction ID:</b> {transaction.transaction_id}</p>
          <p><b>User:</b> {transaction.user_id}</p>
          <p><b>Amount:</b> ${transaction.amount}</p>

          <p><b>Decision:</b> {transaction.decision}</p>

          <p>
            <b>Risk Score:</b> {risk}
          </p>

          <p>
            <b>Status:</b>
            <span style={{ color, marginLeft: "10px" }}>
              {status}
            </span>
          </p>

          <p><b>Location:</b> {transaction.location || "N/A"}</p>
          <p><b>Time:</b> {transaction.timestamp || "N/A"}</p>

          {/* Action buttons */}
          <div style={{ marginTop: "15px" }}>
            <button
              onClick={() => navigate(-1)}
              style={btnSecondary}
            >
              Back
            </button>

            {transaction.decision !== "FRAUD" && (
              <button
                onClick={async () => {
                  await api.put(`/api/transactions/verify/${id}`);
                  alert("Transaction Verified");
                  navigate("/dashboard");
                }}
                style={btnPrimary}
              >
                Verify
              </button>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

const btnPrimary = {
  marginLeft: "10px",
  padding: "8px 12px",
  background: "#3b82f6",
  color: "white",
  border: "none",
  borderRadius: "6px",
};

const btnSecondary = {
  padding: "8px 12px",
  background: "#475569",
  color: "white",
  border: "none",
  borderRadius: "6px",
};

export default Transaction;