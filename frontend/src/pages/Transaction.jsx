import { useParams } from "react-router-dom";

function Transaction() {

  const { id } = useParams();

  return (
    <div style={{padding:"30px"}}>
      <h2>Transaction Details</h2>
      <p>ID: {id}</p>
    </div>
  );
}

export default Transaction;