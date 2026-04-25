import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import FlaggedTransactions from "./pages/FlaggedTransactions";
import Transaction from "./pages/Transaction";
import VerifyTransaction from "./pages/VerifyTransaction";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Login */}
        <Route path="/" element={<Login />} />

        {/* Main Pages */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/flagged" element={<FlaggedTransactions />} />
        <Route path="/transaction/:id" element={<Transaction />} />

        {/* Verification (token-based page) */}
        <Route path="/verify" element={<VerifyTransaction />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;