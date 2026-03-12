import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Login() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();

    if(email === "admin@test.com" && password === "1234"){
  localStorage.setItem("isLoggedIn", "true");
  navigate("/dashboard");
 }
 else {
      alert("Invalid Login");
    }
  };

  return (
    <div style={{
      height: "100vh",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      background: "#f4f6f9"
    }}>

      <div style={{
        background: "white",
        padding: "40px",
        borderRadius: "10px",
        boxShadow: "0 4px 10px rgba(0,0,0,0.1)",
        width: "320px"
      }}>

        <h2 style={{textAlign:"center", marginBottom:"20px"}}>
          Admin Login
        </h2>

        <form onSubmit={handleLogin}>

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e)=>setEmail(e.target.value)}
            style={{
              width:"100%",
              padding:"10px",
              marginBottom:"15px"
            }}
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e)=>setPassword(e.target.value)}
            style={{
              width:"100%",
              padding:"10px",
              marginBottom:"20px"
            }}
          />

          <button
            type="submit"
            style={{
              width:"100%",
              padding:"10px",
              background:"#2563eb",
              color:"white",
              border:"none",
              borderRadius:"5px",
              cursor:"pointer"
            }}
          >
            Login
          </button>

        </form>

      </div>

    </div>
  );
}

export default Login;