import { Link } from "react-router-dom";

function Sidebar(){
  return(
    <div style={{
      width:"220px",
      height:"100vh",
      background:"#111827",
      color:"white",
      padding:"20px"
    }}>

      <h2 style={{marginBottom:"40px"}}>Fraud System</h2>

      <div style={{display:"flex",flexDirection:"column",gap:"15px"}}>
        <Link to="/dashboard" style={{color:"white",textDecoration:"none"}}>Dashboard</Link>
        <Link to="/flagged" style={{color:"white",textDecoration:"none"}}>Flagged Transactions</Link>
      </div>

    </div>
  )
}

export default Sidebar