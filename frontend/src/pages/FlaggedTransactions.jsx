import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../api/axiosConfig";
import Sidebar from "../components/Sidebar";

function FlaggedTransactions() {

  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();


  useEffect(() => {
    api.get("/api/transactions/flagged")
      .then(res => {
        setTransactions(res.data || []);   // ✅ FIXED
        setLoading(false);
      })
      .catch(err => {
        console.log(err);                  // ✅ FIXED
        setLoading(false);
      });
  }, []);

  if (loading) {
  return (

    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />
      <div style={{ padding: "30px" }}>
        <h3>Loading...</h3>
      </div>
      </div>
  );
}


  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0f172a" }}>

      <Sidebar />

      <div style={{ flex: 1, padding: "30px", color: "white" }}>
        <h2>Flagged Transactions</h2>

        {transactions.length === 0 ? (
          <p>No flagged transactions found</p>
        ) : (
          <table style={{
            width: "80%",
            borderCollapse: "collapse",
            background: "#1e293b",
            marginTop: "20px"
          }}>

            <thead style={{ background: "#334155" }}>
              <tr>
                <th>ID</th>
                <th>User</th>
                <th>Amount</th>
                <th>Risk Score</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {transactions.map((txn) => {

                const risk = txn.risk_score ?? 0;

                let status = "";
                let color = "";

                if (risk < 0.4) {
                  status = "Legitimate";
                  color = "#22c55e";
                } else if (risk < 0.7) {
                  status = "Suspicious";
                  color = "#f59e0b";
                } else {
                  status = "Fraud";
                  color = "#ef4444";
                }

                return (
                  <tr
                    key={txn.transaction_id}   // ✅ FIXED
                    onClick={() => navigate(`/transaction/${txn.transaction_id}`)} // ✅ FIXED
                    style={{ cursor: "pointer" }}
                  >
                    <td>{txn.transaction_id}</td>
                    <td>{txn.user_id}</td>
                    <td>${txn.amount}</td>
                    <td>{risk}</td>
                    <td style={{ color, fontWeight: "bold" }}>
                      {status}
                    </td>
                  </tr>
                );
              })}
            </tbody>

          </table>
        )}

      </div>
    </div>
  );
}

export default FlaggedTransactions;