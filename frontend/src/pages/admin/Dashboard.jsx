import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "../../layouts/AdminLayout";
import { supabase } from "../../services/supabaseClient";
import QRCode from "react-qr-code";

/* ---------- IST DATE HELPERS ---------- */
const istToday = () => {
  const now = new Date();
  const ist = new Date(
    now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
  );
  ist.setHours(0, 0, 0, 0);
  return ist;
};

const parseDate = (d) => {
  if (!d) return null;
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
};

export default function Dashboard() {
  const navigate = useNavigate();

  const [clients, setClients] = useState([]);
  const [tokens, setTokens] = useState([]);
  const [qrStats, setQrStats] = useState({});
  const [saving, setSaving] = useState(null);
  const [uploading, setUploading] = useState(null);

  useEffect(() => {
    loadClients();
    loadTokens();
  }, []);

  /* ---------- LOAD CLIENTS ---------- */
  const loadClients = async () => {
    const { data } = await supabase
      .from("clients")
      .select("*, client_types(type_name), duration_days, logo_url");
    setClients(data || []);
  };

  /* ---------- LOAD TOKENS ---------- */
  const loadTokens = async () => {
    const { data } = await supabase
      .from("qr_tokens")
      .select("token, client_id, is_active, assigned_at");
    setTokens(data || []);
  };

  /* ---------- ASSIGN TOKEN ---------- */
  const assignToken = async (token, clientId) => {
    await supabase
      .from("qr_tokens")
      .update({
        client_id: clientId,
        assigned_at: new Date().toISOString()
      })
      .eq("token", token);

    loadTokens();
  };

  /* ---------- UNASSIGN TOKEN ---------- */
  const unassignToken = async (token) => {
    await supabase
      .from("qr_tokens")
      .update({
        client_id: null,
        assigned_at: null
      })
      .eq("token", token);

    loadTokens();
  };

  /* ---------- UPDATE GMB ---------- */
  const updateGmbLink = async (id, value) => {
    setSaving(id);
    await supabase
      .from("clients")
      .update({ gmb_link: value })
      .eq("id", id);
    setSaving(null);
  };

  /* ---------- UPLOAD LOGO ---------- */
  const uploadLogo = async (clientId, file) => {
    if (!file) return;

    setUploading(clientId);

    const path = `${clientId}.png`;

    await supabase.storage
      .from("client-logos")
      .upload(path, file, {
        upsert: true,
        contentType: file.type
      });

    const { data } = supabase.storage
      .from("client-logos")
      .getPublicUrl(path);

    await supabase
      .from("clients")
      .update({ logo_url: data.publicUrl })
      .eq("id", clientId);

    setUploading(null);
    loadClients();
  };

  /* ---------- LOAD QR STATS ---------- */
  const loadQrStats = async (clientId) => {
    if (qrStats[clientId]) return;
    try {
      const res = await fetch(`/admin/qr-stats/${clientId}`);
      const data = await res.json();
      setQrStats(prev => ({ ...prev, [clientId]: data }));
    } catch {
      setQrStats(prev => ({ ...prev, [clientId]: null }));
    }
  };

  const reviewLinkByToken = (token) =>
    `${window.location.origin}/r/${token}`;

  /* ---------- DOWNLOAD QR (HD 1024x1024) ---------- */
  const downloadQR = (token) => {
    const svg = document.getElementById(`qr-${token}`);
    if (!svg) return;

    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(svg);

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const img = new Image();

    img.onload = () => {
      const SIZE = 1024;
      canvas.width = SIZE;
      canvas.height = SIZE;
      ctx.drawImage(img, 0, 0, SIZE, SIZE);

      const png = canvas.toDataURL("image/png");
      const a = document.createElement("a");
      a.href = png;
      a.download = `qr-${token}.png`;
      a.click();
    };

    img.src =
      "data:image/svg+xml;base64," +
      btoa(unescape(encodeURIComponent(svgStr)));
  };

  return (
    <AdminLayout>

      {/* ================= CLIENTS ================= */}
      <h2>Clients</h2>
      <table border="1" cellPadding="6" width="100%">
        <thead>
          <tr>
            <th>Shop</th>
            <th>Type</th>
            <th>Logo</th>
            <th>Active</th>
            <th>Start</th>
            <th>Expiry</th>
          </tr>
        </thead>
        <tbody>
          {clients.map(c => {
            const start = parseDate(c.start_date);
            const today = istToday();
            const end =
              start && c.duration_days
                ? new Date(start.getTime() + c.duration_days * 86400000)
                : null;

            const isBlocked =
              !c.is_active || (end && today > end);

            return (
              <tr key={c.id} style={{ background: isBlocked ? "#fdd" : "#fff" }}>
                <td
                  style={{ cursor: "pointer", color: "blue" }}
                  onClick={() => navigate(`/add-client/${c.id}`)}
                >
                  {c.shop_name}
                </td>

                <td>{c.client_types?.type_name || "-"}</td>

                <td>
                  {c.logo_url && (
                    <img
                      src={c.logo_url}
                      alt="logo"
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: "50%",
                        objectFit: "cover",
                        display: "block",
                        marginBottom: 4
                      }}
                    />
                  )}
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) =>
                      uploadLogo(c.id, e.target.files[0])
                    }
                  />
                  {uploading === c.id && (
                    <div style={{ fontSize: 10 }}>Uploading…</div>
                  )}
                </td>

                <td>
                  <input type="checkbox" checked={!isBlocked} readOnly />
                </td>
                <td>{c.start_date || "-"}</td>
                <td>{end ? end.toISOString().slice(0, 10) : "-"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* ================= QR & REVIEW MANAGER ================= */}
      <h2 style={{ marginTop: 40 }}>QR & Review Manager</h2>

      <table border="1" cellPadding="6" width="100%">
        <thead>
          <tr>
            <th>Token</th>
            <th>Client</th>
            <th>Link</th>
            <th>QR</th>
            <th>Download</th>
            <th>Stats</th>
            <th>GMB</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {tokens.map(t => {
            const client = clients.find(c => c.id === t.client_id);
            const stats = client ? qrStats[client.id] : null;

            return (
              <tr key={t.token}>
                <td>{t.token}</td>

                <td>
                  <select
                    value={t.client_id || ""}
                    onChange={(e) =>
                      assignToken(t.token, e.target.value)
                    }
                  >
                    <option value="">-- Select Client --</option>
                    {clients.map(c => (
                      <option key={c.id} value={c.id}>
                        {c.shop_name}
                      </option>
                    ))}
                  </select>
                </td>

                <td>
                  {t.client_id ? (
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(
                          reviewLinkByToken(t.token)
                        );
                        alert("Link copied");
                      }}
                    >
                      Copy
                    </button>
                  ) : "—"}
                </td>

                <td>
                  {t.client_id && client && (
                    <div style={{ position: "relative", width: 160, height: 160 }}>
                      <QRCode
                        id={`qr-${t.token}`}
                        value={reviewLinkByToken(t.token)}
                        size={160}
                        level="H"
                      />

                      {client.logo_url && (
                        <img
                          src={client.logo_url}
                          alt="logo"
                          style={{
                            position: "absolute",
                            top: "50%",
                            left: "50%",
                            width: 44,
                            height: 44,
                            borderRadius: "50%",
                            transform: "translate(-50%, -50%)",
                            background: "#fff",
                            padding: 4
                          }}
                        />
                      )}
                    </div>
                  )}
                </td>

                <td>
                  {t.client_id && (
                    <button onClick={() => downloadQR(t.token)}>
                      Download
                    </button>
                  )}
                </td>

                <td style={{ fontSize: 12 }}>
                  {client ? (
                    <>
                      <button onClick={() => loadQrStats(client.id)}>
                        Load
                      </button>
                      {stats && (
                        <>
                          <div>Total: {stats.total_scans}</div>
                          <div>Avg: {stats.avg_rating}</div>
                        </>
                      )}
                    </>
                  ) : "—"}
                </td>

                <td>
                  {client && (
                    <input
                      type="text"
                      defaultValue={client.gmb_link || ""}
                      placeholder="Paste GMB link"
                      onBlur={(e) =>
                        updateGmbLink(client.id, e.target.value)
                      }
                    />
                  )}
                </td>

                <td>
                  {t.client_id && (
                    <button
                      style={{ color: "red" }}
                      onClick={() => unassignToken(t.token)}
                    >
                      Unassign
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

    </AdminLayout>
  );
}