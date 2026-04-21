import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <div style={{
      width: "220px",
      height: "100vh",
      background: "#111827",
      color: "white",
      padding: "20px"
    }}>

      <h2 style={{ marginBottom: "40px" }}>Fraud System</h2>

      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

        <NavLink
  to="/dashboard"
  style={({ isActive }) => ({
    display: "block",
    width: "100%",
    padding: "10px 6px",
    borderRadius: "10px",
    color: "#ffffff",
    textDecoration: "none",
    background: isActive ? "#1f2937" : "transparent",
    boxShadow: isActive ? "0 4px 10px rgba(0,0,0,0.3)" : "none",
    borderLeft: isActive ? "4px solid #ffffff" : "4px solid transparent",
    transition: "0.2s"
  })}
  onMouseEnter={(e) => {
    e.currentTarget.style.background = "#1f2937";
  }}
  onMouseLeave={(e) => {
    if (!e.currentTarget.classList.contains("active")) {
      e.currentTarget.style.background = "transparent";
    }
  }}
>
  Dashboard
</NavLink>


       <NavLink
  to="/flagged"
  style={({ isActive }) => ({
    display: "block",
    width: "100%",
    padding: "10px 6px",
    borderRadius: "10px",
    color: "#ffffff",
    textDecoration: "none",
    background: isActive ? "#1f2937" : "transparent",
    boxShadow: isActive ? "0 4px 10px rgba(0,0,0,0.3)" : "none",
    borderLeft: isActive ? "4px solid #ffffff" : "4px solid transparent",
    transition: "0.2s"
  })}
  onMouseEnter={(e) => {
    e.currentTarget.style.background = "#1f2937";
  }}
  onMouseLeave={(e) => {
    if (!e.currentTarget.classList.contains("active")) {
      e.currentTarget.style.background = "transparent";
    }
  }}
>
  Flagged Transactions
</NavLink>

      </div>
    </div>
  );
}

export default Sidebar;