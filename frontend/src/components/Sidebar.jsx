import { NavLink } from "react-router-dom";

function Sidebar() {
  const linkStyle = ({ isActive }) => ({
    display: "block",
    width: "100%",
    padding: "10px 8px",
    borderRadius: "10px",
    color: "#ffffff",
    textDecoration: "none",
    background: isActive ? "#1f2937" : "transparent",
    boxShadow: isActive ? "0 4px 10px rgba(0,0,0,0.3)" : "none",
    borderLeft: isActive ? "4px solid #3b82f6" : "4px solid transparent",
    transition: "0.2s",
  });

  return (
    <div
      style={{
        width: "220px",
        height: "100vh",
        background: "#111827",
        color: "white",
        padding: "20px",
      }}
    >
      <h2 style={{ marginBottom: "40px" }}>Fraud System</h2>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <NavLink to="/dashboard" style={linkStyle}>
          Dashboard
        </NavLink>

        <NavLink to="/flagged" style={linkStyle}>
          Flagged Transactions
        </NavLink>
      </div>
    </div>
  );
}

export default Sidebar;