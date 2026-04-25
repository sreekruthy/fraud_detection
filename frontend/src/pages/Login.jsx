import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axiosConfig";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Enter email and password");
      return;
    }

    setLoading(true);

    try {
      const res = await api.post("/api/auth/login", {
        email,
        password,
      });

      localStorage.setItem("isLoggedIn", "true");
      localStorage.setItem("user", res.data.email);

      navigate("/dashboard");
    } catch {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={wrapper}>

      {/* Background Glow */}
      <div style={glow1}></div>
      <div style={glow2}></div>

      {/* Login Card */}
      <div style={card}>

        {/* Title */}
        <div style={{ marginBottom: "25px", textAlign: "center" }}>
          <h2 style={{ margin: 0 }}>🛡 FraudShield</h2>
          <p style={{ color: "#64748b", fontSize: "13px" }}>
            Admin Login Panel
          </p>
        </div>

        <form onSubmit={handleLogin}>

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={input}
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={input}
          />

          {error && (
            <p style={{ color: "#ef4444", fontSize: "12px" }}>{error}</p>
          )}

          <button style={button} disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>

        </form>

      </div>
    </div>
  );
}

export default Login;





// ================= STYLES =================

const wrapper = {
  minHeight: "100vh",
  background: "#0f172a",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  position: "relative",
  overflow: "hidden",
  fontFamily: "'Segoe UI', system-ui, sans-serif"
};

const card = {
  background: "rgba(30, 41, 59, 0.9)",
  backdropFilter: "blur(10px)",
  padding: "35px",
  borderRadius: "14px",
  width: "340px",
  border: "1px solid #334155",
  boxShadow: "0 10px 40px rgba(0,0,0,0.5)",
  zIndex: 2,
  color: "white"
};

const input = {
  width: "100%",
  padding: "12px",
  marginBottom: "12px",
  borderRadius: "8px",
  border: "1px solid #334155",
  background: "#0f172a",
  color: "white",
  outline: "none",
  fontSize: "14px"
};

const button = {
  width: "100%",
  padding: "12px",
  background: "linear-gradient(135deg, #3b82f6, #6366f1)",
  border: "none",
  borderRadius: "8px",
  color: "white",
  fontWeight: "600",
  cursor: "pointer",
  marginTop: "5px"
};

const glow1 = {
  position: "absolute",
  width: "300px",
  height: "300px",
  background: "#3b82f6",
  filter: "blur(120px)",
  top: "-50px",
  left: "-50px",
  opacity: 0.3
};

const glow2 = {
  position: "absolute",
  width: "300px",
  height: "300px",
  background: "#6366f1",
  filter: "blur(120px)",
  bottom: "-50px",
  right: "-50px",
  opacity: 0.3
};