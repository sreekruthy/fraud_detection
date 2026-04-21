import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";

function Dashboard() {

  const navigate = useNavigate();

  return (
    <div style={{ display: "flex" }}> {/* ✅ layout */}

      {/* ✅ Sidebar */}
      <Sidebar />

      {/* ✅ Main Content */}
      <div style={{ flex: 1, padding: "40px" }}>

        <h2>Fraud Detection Dashboard</h2>

        {/* 🔹 Navigation Buttons */}
        <div style={{ marginTop: "30px" }}>


          <button
            onClick={() => navigate("/transaction/TXN001")}
            style={{
              padding: "12px 20px",
              backgroundColor: "#007bff",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer"
            }}
          >
            View Sample Transaction
          </button>

        </div>

        {/* 🔹 Info Section */}
        <div style={{
          marginTop: "40px",
          padding: "20px",
          background: "white",
          width: "400px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
        }}>

          <h3>System Overview</h3>
          <p>✔ Real-time fraud detection</p>
          <p>✔ Risk scoring using rules / ML</p>
          <p>✔ Flagged transaction monitoring</p>
          <p>✔ MongoDB + FastAPI + React</p>

        </div>

      </div>
    </div>
  );
}

export default Dashboard;