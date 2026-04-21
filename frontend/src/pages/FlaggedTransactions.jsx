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
        setTransactions(res.data?.transactions || []);
        setLoading(false);
      })
      .catch(err => {
        console.log("API RESPONSE: ", res.data);
        console.log(err);
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
    <div style={{ display: "flex" }}> {/* ✅ layout */}

      {/* ✅ Sidebar */}
      <Sidebar />

      {/* ✅ Main Content */}
      <div style={{ flex: 1, padding: "30px" }}>

        <h2>Flagged Transactions</h2>


        {transactions.length === 0 ? (
          <p>No flagged transactions found</p>
        ) : (
          <table style={{
            width: "80%",
            borderCollapse: "collapse",
            background: "white",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
          }}>

            <thead style={{ background: "#f1f5f9" }}>
              <tr>
                <th>ID</th>
                <th>User</th>
                <th>Amount</th>
                <th>Risk Score</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {Array.isArray(transactions) && transactions.map((txn) => {

                let status = "";
                let color = "";

                if (txn.risk_score < 0.4) {
                  status = "Legitimate";
                  color = "green";
                } 
                else if (txn.risk_score < 0.7) {
                  status = "Suspicious";
                  color = "orange";
                } 
                else {
                  status = "Flagged";
                  color = "red";
                }

                return (
                  <tr
                    key={txn._id}
                    onClick={() => navigate(`/transaction/${txn._id}`)}
                    style={{ cursor: "pointer" }}
                  >
                    <td>{txn._id}</td>
                    <td>{txn.user}</td>
                    <td>{txn.amount}</td>
                    <td>{txn.risk_score}</td>
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