import { BrowserRouter, Routes, Route } from "react-router-dom"
import Login from "./pages/Login"
import Dashboard from "./pages/Dashboard"
import FlaggedTransactions from "./pages/FlaggedTransactions"
import VerifyTransaction from "./pages/VerifyTransaction"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"             element={<Login />} />
        <Route path="/dashboard"    element={<Dashboard />} />
        <Route path="/flagged"      element={<FlaggedTransactions />} />
        <Route path="/verify"       element={<VerifyTransaction />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;