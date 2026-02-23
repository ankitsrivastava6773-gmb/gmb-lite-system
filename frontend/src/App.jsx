import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/admin/Dashboard";
import AddClient from "./pages/admin/AddClient";
import ClientTypes from "./pages/admin/ClientTypes";
import PublicReview from "./pages/public/PublicReview";
import PublicQR from "./pages/PublicQR";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/add-client/:id" element={<AddClient />} />
      <Route path="/add-client" element={<AddClient />} />
      <Route path="/client-types" element={<ClientTypes />} />
      <Route path="/r/:clientId" element={<PublicReview />} />
      <Route path="/review/:clientId" element={<PublicReview />} />
      <Route path="/qr/:token" element={<PublicQR />} />
      
    </Routes>
  );
}

export default App;