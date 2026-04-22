import { BrowserRouter, Routes, Route } from "react-router-dom"
import Login from "./pages/Login"
import Dashboard from "./pages/Dashboard"
import FlaggedTransactions from "./pages/FlaggedTransactions"
import Transaction from "./pages/Transaction"
import VerifyTransaction from "./pages/Verifytransaction"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"             element={<Login />} />
        <Route path="/dashboard"    element={<Dashboard />} />
        <Route path="/flagged"      element={<FlaggedTransactions />} />
        <Route path="/transaction/:id" element={<Transaction />} />
        <Route path="/verify"       element={<VerifyTransaction />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App