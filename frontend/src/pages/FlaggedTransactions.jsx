function FlaggedTransactions() {

  const transactions = [
    { id: "TXN001", user: "U101", amount: 25000, risk_score: 0.91 },
    { id: "TXN002", user: "U205", amount: 18000, risk_score: 0.67 },
    { id: "TXN003", user: "U303", amount: 29000, risk_score: 0.29 }
  ]

  return (

    <div style={{ textAlign: "center", marginTop: "30px" }}>

      <h2>Flagged Transactions</h2>

      <div style={{
        display: "flex",
        justifyContent: "center",
        marginTop: "20px"
      }}>

        <table style={{
          width: "70%",
          borderCollapse: "collapse",
          background: "white",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
        }}>

          <thead style={{background:"#f1f5f9"}}>
            <tr>
              <th>ID</th>
              <th>User</th>
              <th>Amount</th>
              <th>Risk Score</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {transactions.map((txn) => {

              let status = "";
              let color = "";

              if (txn.risk_score < 0.4) {
                status = "Safe";
                color = "green";
              } 
              else if (txn.risk_score >= 0.4 && txn.risk_score < 0.7) {
                status = "Might be Flagged";
                color = "orange";
              } 
              else {
                status = "Flagged";
                color = "red";
              }

              return (
                <tr key={txn.id} style={{borderBottom:"1px solid #eee"}}>
                  <td>{txn.id}</td>
                  <td>{txn.user}</td>
                  <td>{txn.amount}</td>
                  <td>{txn.risk_score}</td>

                  <td style={{color: color, fontWeight:"bold"}}>
                    {status}
                  </td>
                </tr>
              );
            })}
          </tbody>

        </table>

      </div>

    </div>

  )
}

export default FlaggedTransactions