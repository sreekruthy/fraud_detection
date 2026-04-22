import axios from "axios";

const api = axios.create({
<<<<<<< HEAD
  baseURL: "http://127.0.0.1:5001"
});
=======
  baseURL: "http://localhost:5001",
})
>>>>>>> a7528d0 (alert service added)

export default api;