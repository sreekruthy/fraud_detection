import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import api from "../api/axiosConfig";
import Sidebar from "../components/Sidebar";

function FlaggedTransactions() {

  const [transactions, setTransactions] = useState([]);
  const [selectedTxn, setSelectedTxn] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();


  useEffect(() => {
    api.get("/api/transactions/flagged")
      .then(res => {
        setTransactions(res.data.transactions || []);   
        setLoading(false);
      })
      .catch(err => {
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

                const risk = txn.final_score ?? 0;

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
                    key={txn.transaction_id}   
                    onClick={() => setSelectedTxn(txn)} 
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

      {selectedTxn && (
  <div style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.7)", zIndex:1000, display:"flex", alignItems:"center", justifyContent:"center", padding:"20px" }}
    onClick={() => setSelectedTxn(null)}>
    <div style={{ background:"#1e293b", border:"1px solid #334155", borderRadius:"14px", padding:"28px", width:"100%", maxWidth:"520px", color:"white" }}
      onClick={e => e.stopPropagation()}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h3 style={{ margin:0, fontSize:"16px", fontWeight:"700" }}>Transaction Details</h3>
        <button onClick={() => setSelectedTxn(null)}
          style={{ background:"#334155", border:"none", color:"#94a3b8", padding:"4px 10px", borderRadius:"6px", cursor:"pointer" }}>✕</button>
      </div>
      {[
        ["Transaction ID", selectedTxn.transaction_id],
        ["User ID",        selectedTxn.user_id],
        ["Amount",         `$${(selectedTxn.amount||0).toLocaleString("en-US",{minimumFractionDigits:2})}`],
        ["Decision",       selectedTxn.decision],
        ["Status",         selectedTxn.txn_status],
        ["Risk Score",     selectedTxn.final_score != null ? `${(selectedTxn.final_score*100).toFixed(0)}%` : "—"],
        ["Feedback",       selectedTxn.customer_feedback || "—"],
      ].map(([k,v]) => (
        <div key={k} style={{ display:"flex", justifyContent:"space-between", padding:"8px 0", borderBottom:"1px solid #334155", fontSize:"13px" }}>
          <span style={{ color:"#64748b" }}>{k}</span>
          <span style={{ fontWeight:"600", color:"white" }}>{v}</span>
        </div>
      ))}
      <button onClick={() => setSelectedTxn(null)}
        style={{ marginTop:"20px", width:"100%", padding:"10px", background:"#334155", border:"none", color:"white", borderRadius:"8px", cursor:"pointer" }}>
        Close
      </button>
    </div>
  </div>
)}


    </div>
  );
}

export default FlaggedTransactions;