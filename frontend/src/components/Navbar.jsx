import { useNavigate } from "react-router-dom";

function Navbar(){

  const navigate = useNavigate();

  const handleLogout = () => {

    localStorage.removeItem("isLoggedIn");

    navigate("/");
  };

  return(
    <div style={{
      height:"60px",
      background:"white",
      borderBottom:"1px solid #ddd",
      display:"flex",
      alignItems:"center",
      justifyContent:"space-between",
      padding:"0 20px"
    }}>

      <h3>Fraud Detection Dashboard</h3>

      <button
        onClick={handleLogout}
        style={{
          padding:"8px 14px",
          background:"#000000",
          color:"white",
          border:"none",
          borderRadius:"5px",
          cursor:"pointer"
        }}
      >
        Logout
      </button>

    </div>
  )
}

export default Navbar