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

      </div>
    </div>
  );
}

export default Dashboard;