import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import "./PublicReview.css";

export default function PublicReview() {
  const { clientId: token } = useParams();

  const [loading, setLoading] = useState(true);
  const [client, setClient] = useState(null);
  const [realClientId, setRealClientId] = useState(null);

  const [rating, setRating] = useState(0);
  const [language, setLanguage] = useState("English");
  const [product, setProduct] = useState("");

  const [reviewText, setReviewText] = useState("");
  const [status, setStatus] = useState("");
  const [isWriting, setIsWriting] = useState(false);

  /* ---------- TEXT BY LANGUAGE ---------- */
  const t = {
    writing:
      language === "Hindi"
        ? "Review likh rahe hain…"
        : language === "Hinglish"
        ? "Review likh rahe hain…"
        : "Writing your review…",

    copied:
      language === "Hindi"
        ? "✅ Review copy ho gaya hai. Google page par paste karke submit karein…"
        : language === "Hinglish"
        ? "✅ Review copy ho gaya hai. Google page par paste karke submit karein…"
        : "✅ Review copied. Please paste it on Google and submit your review…",

    ratingHint:
      language === "Hindi"
        ? "Rating 3 star se start hoti hai"
        : language === "Hinglish"
        ? "Rating 3 star se start hoti hai"
        : "Rating starts from 3 stars"
  };

  /* ---------- LOAD CLIENT VIA TOKEN ---------- */
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        setLoading(true);

        const r1 = await fetch(`import.meta.env.VITE_API_URL/r/${token}`);
        const tdata = await r1.json();
        setRealClientId(tdata.client_id);

        const r2 = await fetch(
          `import.meta.env.VITE_API_URL/public-client/${tdata.client_id}`
        );
        const cdata = await r2.json();

        if (!cancelled) setClient(cdata);
      } catch {
        if (!cancelled) setClient(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => (cancelled = true);
  }, [token]);

  /* ---------- STAR CLICK ---------- */
  const onStarClick = async (star) => {
    if (star < 3 || !client?.gmb_link || !realClientId) return;

    setRating(star);
    setIsWriting(true);
    setStatus(t.writing);
    setReviewText("");

    try {
      const res = await fetch("import.meta.env.VITE_API_URL/api/generate-review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_id: realClientId,
          rating: star,
          language,
          product
        })
      });

      const data = await res.json();
      const text =
        data.review || data.text || data.generated_review || "";

      if (!text) {
        setIsWriting(false);
        setStatus("Failed to generate review");
        return;
      }

      setReviewText(text);
      await navigator.clipboard.writeText(text);

      setIsWriting(false);
      setStatus(t.copied);

      setTimeout(() => {
        window.location.href = client.gmb_link;
      }, 3000);
    } catch {
      setIsWriting(false);
      setStatus("Failed to generate review");
    }
  };

  if (loading) return <div className="pr-loading">Loading…</div>;
  if (!client) return <div className="pr-loading">Invalid QR</div>;

  return (
    <div className="pr-page">
      <div className="pr-card">

        {/* HEADER */}
        <div className="pr-header">
          <div className="pr-logo">
            {client.logo_url ? (
              <img
                src={client.logo_url}
                alt="logo"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                  e.currentTarget.parentElement.innerHTML =
                    `<span>${client.shop_name?.[0]}</span>`;
                }}
              />
            ) : (
              <span>{client.shop_name?.[0]}</span>
            )}
          </div>

          <div className="pr-shop">
            <h2>{client.shop_name}</h2>
            {client.area && <p>{client.area}</p>}
          </div>
        </div>

        {/* PRODUCT + LANGUAGE */}
        <div className="pr-row">
          <select
            value={product}
            onChange={(e) => setProduct(e.target.value)}
          >
            <option value="">Product / Service</option>
            {(client.products_services || []).map((p, i) => (
              <option key={i} value={p}>{p}</option>
            ))}
          </select>

          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            <option>English</option>
            <option>Hindi</option>
            <option>Hinglish</option>
          </select>
        </div>

        {/* STARS */}
        <div className="pr-stars">
          {[1,2,3,4,5].map(star => (
            <span
              key={star}
              className={`pr-star ${star < 3 ? "disabled" : ""}`}
              style={{ color: star <= rating ? "#fbbf24" : "#ccc" }}
              onClick={() => onStarClick(star)}
            >
              ★
            </span>
          ))}
          <div className="pr-hint">{t.ratingHint}</div>
        </div>

        {/* STATUS */}
        {status && (
          <div className="pr-status">
            {isWriting ? (
              <span className="pr-writing">
                <span className="pr-pen" />
                {status}
              </span>
            ) : status}
          </div>
        )}

        {/* REVIEW PREVIEW */}
        {reviewText && (
          <textarea
            className="pr-textarea"
            value={reviewText}
            readOnly
          />
        )}

      </div>
    </div>
  );
}
