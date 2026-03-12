import { BrowserRouter, Routes, Route } from "react-router-dom"
import Login from "./pages/Login"
import Dashboard from "./pages/Dashboard"
import FlaggedTransactions from "./pages/FlaggedTransactions"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/flagged" element={<FlaggedTransactions />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App