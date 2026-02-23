import { Link } from "react-router-dom";

export default function AdminLayout({ children }) {
  return (
    <>
      <nav style={{ padding: 10, background: "#222" }}>
        <Link to="/" style={{ color: "#fff", marginRight: 15 }}>Dashboard</Link>
        <Link to="/add-client" style={{ color: "#fff", marginRight: 15 }}>Add Client</Link>
        <Link to="/client-types" style={{ color: "#fff" }}>Client Types</Link>
      </nav>
      <div style={{ padding: 20 }}>{children}</div>
    </>
  );
}