import { useParams, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";

function Transaction() {

  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>

      {/* ✅ Sidebar */}
      <Sidebar />

      {/* ✅ Main Content */}
      <div style={{ padding: "30px", flex: 1 }}>

        <h2>Transaction Details</h2>
        <p><strong>ID:</strong> {id}</p>

      </div>
    </div>
  );
}

export default Transaction;