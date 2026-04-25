import { useParams, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { useEffect, useState } from "react";
import api from "../api/axiosConfig.js";


function Transaction() {

  const { id } = useParams();

  const navigate = useNavigate();
  const [transaction, setTransaction] = useState(null);

useEffect(() => {
    api.get(`/api/transactions/${id}`)
      .then(res => setTransaction(res.data.transaction))
      .catch(err => console.log(err));
  }, [id]);

   if (!transaction) {
    return <h3>Loading...</h3>;
  }
let status = "";
  let color = "";

  if (transaction.risk_score < 0.4) {
    status = "Safe";
    color = "green";
  } 
  else if (transaction.risk_score < 0.7) {
    status = "Might be Flagged";
    color = "orange";
  } 
  else {
    status = "Flagged";
    color = "red";
  }


  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>

      {/* ✅ Sidebar */}
      <Sidebar />

      {/* ✅ Main Content */}
      <div style={{ padding: "30px", flex: 1 }}>

        <h2>Transaction Details</h2>
      <div style={{
        marginTop: "20px",
        padding: "20px",
        background: "white",
        width: "400px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
      }}>

        <p><b>Transaction ID:</b> {transaction.id}</p>
        <p><b>User:</b> {transaction.user}</p>
        <p><b>Amount:</b> {transaction.amount}</p>
        <p><b>Risk Score:</b> {transaction.risk_score}</p>

        <p>
          <b>Status:</b>
          <span style={{ color: color, marginLeft: "10px" }}>
            {status}
          </span>
        </p>

        <p><b>Location:</b> {transaction.location}</p>
        <p><b>Time:</b> {transaction.time}</p>

      </div>
    </div>
    </div>
  );
}

export default Transaction;