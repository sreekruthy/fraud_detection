import Navbar from "../components/Navbar"
import Sidebar from "../components/Sidebar"

function Dashboard() {
  return (
    <div style={{ display: "flex" }}>
      <Sidebar />
      <div style={{ flex: 1 }}>
        <Navbar />
        <h2>Dashboard</h2>
      </div>
    </div>
  )
}

export default Dashboard