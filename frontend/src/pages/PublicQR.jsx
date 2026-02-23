import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function PublicQR() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`http://localhost:8002/qr/${token}`)
      .then(res => res.json())
      .then(data => {
        if (data.redirect_url) {
          navigate(data.redirect_url, { replace: true });
        } else {
          setError("Invalid QR");
        }
      })
      .catch(() => setError("Invalid or expired QR"));
  }, [token, navigate]);

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: 16
    }}>
      {error || "Redirecting…"}
    </div>
  );
}
