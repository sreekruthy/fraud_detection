import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
<<<<<<< HEAD
import api from "../api/axiosConfig";
import Sidebar from "../components/Sidebar"; 
=======
import api from "../api/axiosConfig.js";
>>>>>>> a7528d0 (alert service added)

function FlaggedTransactions() {

  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
<<<<<<< HEAD
=======

  useEffect(() => {
    api.get("/api/transactions/flagged")
      .then(res => {
        setTransactions(res.data.transactions);
        setLoading(false);
      })
      .catch(err => {
        console.log(err);
        setLoading(false);
      });
  }, []);

  // 🔄 Loading state
  if (loading) return <h3 style={{ textAlign: "center" }}>Loading...</h3>;
>>>>>>> a7528d0 (alert service added)

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
<<<<<<< HEAD
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />
      <div style={{ padding: "30px" }}>
        <h3>Loading...</h3>
      </div>
=======
    <div style={{ textAlign: "center", marginTop: "30px" }}>

      <h2>Flagged Transactions</h2>

      {/* 🔙 Back Button */}
      <button
        onClick={() => navigate("/dashboard")}
        style={{
          marginTop: "10px",
          marginBottom: "20px",
          padding: "10px 15px",
          backgroundColor: "#007bff",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer"
        }}
      >
        ← Back to Dashboard
      </button>

      {/* ❗ Empty state */}
      {transactions.length === 0 ? (
        <p>No flagged transactions found</p>
      ) : (
        <div style={{
          display: "flex",
          justifyContent: "center",
          marginTop: "20px"
        }}>

          <table style={{
            width: "70%",
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
              {transactions.map((txn) => {

                let status = "";
                let color = "";

                if (txn.risk_score < 0.4) {
                  status = "Safe";
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
                    key={txn.id}
                    onClick={() => navigate(`/transaction/${txn.id}`)}
                    style={{
                      borderBottom: "1px solid #eee",
                      cursor: "pointer"
                    }}
                  >
                    <td>{txn.id}</td>
                    <td>{txn.user}</td>
                    <td>{txn.amount}</td>
                    <td>{txn.risk_score}</td>

                    <td style={{ color: color, fontWeight: "bold" }}>
                      {status}
                    </td>
                  </tr>
                );
              })}
            </tbody>

          </table>

        </div>
      )}

>>>>>>> a7528d0 (alert service added)
    </div>
  );
}

<<<<<<< HEAD
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

=======
>>>>>>> a7528d0 (alert service added)
export default FlaggedTransactions;