import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import AdminLayout from "../../layouts/AdminLayout";
import { supabase } from "../../services/supabaseClient";

/* ---------- TAG INPUT ---------- */
const TagInput = ({ label, values, setValues }) => {
  const [input, setInput] = useState("");

  const addTag = () => {
    if (!input) return;
    setValues([...values, input]);
    setInput("");
  };

  const removeTag = (idx) => {
    setValues(values.filter((_, i) => i !== idx));
  };

  return (
    <>
      <b>{label}</b><br/>
      {values.map((v,i)=>(
        <span key={i} style={{border:"1px solid #000",padding:"2px 6px",margin:4,display:"inline-block"}}>
          {v}
          <button onClick={()=>removeTag(i)} style={{marginLeft:6}}>×</button>
        </span>
      ))}
      <br/>
      <input value={input} onChange={e=>setInput(e.target.value)} />
      <button onClick={addTag}>Add</button>
      <br/><br/>
    </>
  );
};

export default function AddClient() {
  const { id } = useParams();
  const isEdit = !!id;

  const [types, setTypes] = useState([]);
  const [selectedType, setSelectedType] = useState(null);

  /* ---------- CORE FORM ---------- */
  const [form, setForm] = useState({
    shop_name:"",
    client_name:"",
    mobile_number:"",
    context:[],
    trust_signals:[],
    seo_keywords:[],
    products_services:[],
    area:[],
    tone:"",
    verbosity:3,
    duration_days: 7, // STEP 1: Added duration_days
    start_date:"",
    end_date:"",
    is_active:true,
    payment_done:false,
    payment_method:"",
    transaction_number:""
  });

  /* ---------- HISTORY ---------- */
  const [serviceHistory, setServiceHistory] = useState([]);
  const [payments, setPayments] = useState([]);

  const [paymentForm, setPaymentForm] = useState({
    amount:"",
    payment_method:"",
    transaction_number:""
  });

  /* ---------- LOAD TYPES ---------- */
  useEffect(()=>{
    supabase.from("client_types").select("*")
      .then(({data})=>setTypes(data||[]));
  },[]);

  /* ---------- LOAD CLIENT ---------- */
  useEffect(()=>{
    if (!isEdit || types.length === 0) return;

    supabase.from("clients").select("*").eq("id", id).single()
      .then(({ data }) => {
        if (!data) return;

        setForm({
          shop_name: data.shop_name || "",
          client_name: data.client_name || "",
          mobile_number: data.mobile_number || "",
          context: data.context ? data.context.split(",") : [],
          trust_signals: data.trust_signals ? data.trust_signals.split(",") : [],
          seo_keywords: data.seo_keywords ? data.seo_keywords.split(",") : [],
          products_services: data.products_services ? data.products_services.split(",") : [],
          area: data.area ? data.area.split(",") : [],
          tone: data.tone || "",
          verbosity: data.verbosity ?? 3,
          duration_days: data.duration_days ?? 7, // STEP 2: Added duration_days in Load
          start_date: data.start_date || "",
          end_date: data.end_date || "",
          is_active: data.is_active ?? true,
          payment_done: data.payment_done ?? false,
          payment_method: data.payment_method || "",
          transaction_number: data.transaction_number || ""
        });

        const t = types.find(t => t.id === data.type_id);
        if (t) setSelectedType(t);
      });

    supabase.from("client_service_history")
      .select("*")
      .eq("client_id", id)
      .order("changed_at", { ascending:false })
      .then(({data})=>setServiceHistory(data||[]));

    supabase.from("client_payments")
      .select("*")
      .eq("client_id", id)
      .order("created_at", { ascending:false })
      .then(({data})=>setPayments(data||[]));

  }, [id, isEdit, types]);

  /* ---------- TYPE SELECT ---------- */
  const selectType = (t) => {
    setSelectedType(t);
    setForm(f => ({
      ...f,
      context: t.context ? t.context.split(",") : f.context,
      trust_signals: t.trust_signals ? t.trust_signals.split(",") : f.trust_signals,
      seo_keywords: t.seo_keywords ? t.seo_keywords.split(",") : f.seo_keywords,
      tone: t.tone || f.tone,
      verbosity: t.verbosity || f.verbosity
    }));
  };

  /* ---------- IST SAFE DATE HELPERS ---------- */
  const istToday = () => {
    const now = new Date();
    const ist = new Date(
      now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
    );
    ist.setHours(0,0,0,0);
    return ist;
  };

  const parseDate = (d) => {
    if (!d) return null;
    const x = new Date(d);
    x.setHours(0,0,0,0);
    return x;
  };

  /* ---------- EXPIRY (IST, NO NEGATIVE) ---------- */
  // STEP 5: New daysLeft logic using duration_days
  const daysLeft = useMemo(() => {
    if (!form.start_date || !form.duration_days) return null;

    const today = istToday();
    const start = parseDate(form.start_date);
    const end = new Date(start.getTime() + form.duration_days * 86400000);

    if (today < start) {
      return Math.ceil((end - start) / 86400000);
    }

    const diff = Math.ceil((end - today) / 86400000);
    return diff < 0 ? 0 : diff;
  }, [form.start_date, form.duration_days]);

  /* ---------- SAVE CLIENT ---------- */
  const saveClient = async () => {
    let oldClient = null;

    if (isEdit) {
      const { data } = await supabase
        .from("clients")
        .select("start_date,end_date")
        .eq("id", id)
        .single();
      oldClient = data;
    }

    const payload = {
      shop_name: form.shop_name,
      client_name: form.client_name,
      mobile_number: form.mobile_number,
      type_id: selectedType?.id || null,
      context: form.context.join(","),
      trust_signals: form.trust_signals.join(","),
      seo_keywords: form.seo_keywords.join(","),
      products_services: form.products_services.join(","),
      area: form.area.join(","),
      tone: form.tone || null,
      verbosity: form.verbosity,
      duration_days: form.duration_days, // STEP 4: Added duration_days to payload
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      is_active: form.is_active,
      payment_done: form.payment_done,
      payment_method: form.payment_method,
      transaction_number: form.transaction_number
    };

    const q = isEdit
      ? supabase.from("clients").update(payload).eq("id", id)
      : supabase.from("clients").insert([payload]);

    const { error } = await q;
    if (error) {
      alert("Save failed");
      return;
    }

    if (
      isEdit &&
      oldClient &&
      (oldClient.start_date !== form.start_date ||
        oldClient.end_date !== form.end_date)
    ) {
      await supabase.from("client_service_history").insert([{
        client_id: id,
        old_start_date: oldClient.start_date,
        old_end_date: oldClient.end_date,
        new_start_date: form.start_date,
        new_end_date: form.end_date
      }]);
    }

    alert("Client saved");
  };

  /* ---------- ADD PAYMENT ---------- */
  const addPayment = async () => {
    if (!paymentForm.amount) return;

    const start = form.start_date || new Date().toISOString().slice(0,10);
    const end = form.end_date || start;

    const { error } = await supabase.from("client_payments").insert([{
      client_id: id,
      amount: paymentForm.amount,
      start_date: start,
      end_date: end,
      payment_method: paymentForm.payment_method,
      transaction_number: paymentForm.transaction_number
    }]);

    if (error) {
      alert("Payment save failed: " + error.message);
      return;
    }

    setPaymentForm({ amount:"", payment_method:"", transaction_number:"" });

    const { data } = await supabase
      .from("client_payments")
      .select("*")
      .eq("client_id", id)
      .order("created_at", { ascending:false });

    setPayments(data || []);
  };

  /* ---------- WHATSAPP ---------- */
  const whatsappReminder = () => {
    if (daysLeft === null) return;
    const msg = `Hello ${form.client_name || ""}, your service for ${form.shop_name} will expire in ${daysLeft} day(s). Please renew to avoid interruption.`;
    window.open(`https://wa.me/91${form.mobile_number}?text=${encodeURIComponent(msg)}`);
  };

  return (
    <AdminLayout>
      <h2>{isEdit ? "Edit Client" : "Add Client"}</h2>

      <input placeholder="Shop Name" value={form.shop_name}
        onChange={e=>setForm({...form,shop_name:e.target.value})}/><br/><br/>

      <input placeholder="Client Name" value={form.client_name}
        onChange={e=>setForm({...form,client_name:e.target.value})}/><br/><br/>

      <input placeholder="Mobile" value={form.mobile_number}
        onChange={e=>setForm({...form,mobile_number:e.target.value})}/>
      {daysLeft !== null && daysLeft <= 7 && (
        <button onClick={whatsappReminder} style={{marginLeft:10}}>
          WhatsApp Reminder
        </button>
      )}
      <br/><br/>

      <label>
        <input type="checkbox" checked={form.is_active}
          onChange={e=>setForm({...form,is_active:e.target.checked})}/>
        Active (AI ON/OFF)
      </label>
      <br/><br/>

      {daysLeft !== null && daysLeft <= 7 && (
        <div style={{color:"red",fontWeight:"bold"}}>
          ⚠ Service expires in {daysLeft} day(s)
        </div>
      )}

      <h3>Select Type</h3>
      {types.map(t=>(
        <div key={t.id} onClick={()=>selectType(t)}
          style={{border:selectedType?.id===t.id?"2px solid green":"1px solid #ccc",padding:6}}>
          {t.type_name}
        </div>
      ))}

      <TagInput label="Context" values={form.context} setValues={v=>setForm({...form,context:v})}/>
      <TagInput label="Trust Signals" values={form.trust_signals} setValues={v=>setForm({...form,trust_signals:v})}/>
      <TagInput label="SEO Keywords" values={form.seo_keywords} setValues={v=>setForm({...form,seo_keywords:v})}/>
      <TagInput label="Products / Services" values={form.products_services} setValues={v=>setForm({...form,products_services:v})}/>
      <TagInput label="Area" values={form.area} setValues={v=>setForm({...form,area:v})}/>

      <b>Tone</b><br/>
      <input value={form.tone}
        onChange={e=>setForm({...form,tone:e.target.value})}/><br/><br/>

      <b>Verbosity</b><br/>
      <input type="number" min="1" max="5" value={form.verbosity}
        onChange={e=>setForm({...form,verbosity:+e.target.value})}/><br/><br/>

      <b>Service Period</b><br/>
      {/* STEP 3: New Service Period UI */}
      <input
        type="date"
        value={form.start_date}
        onChange={e => setForm({ ...form, start_date: e.target.value })}
      />

      {" + "}

      <input
        type="number"
        min="1"
        placeholder="Days"
        value={form.duration_days}
        onChange={e =>
          setForm({ ...form, duration_days: Number(e.target.value) })
        }
      />

      {" = "}

      <b>
        {form.start_date
          ? new Date(
              new Date(form.start_date).getTime() +
                form.duration_days * 86400000
            ).toISOString().slice(0, 10)
          : "-"}
      </b>
      <br/><br/>

      <button onClick={saveClient}>Save Client</button>

      {isEdit && (
        <>
          <hr/>
          <h3>Service History</h3>
          {serviceHistory.map(h=>(
            <div key={h.id}>
              {h.old_start_date} → {h.old_end_date} ➜ {h.new_start_date} → {h.new_end_date}
            </div>
          ))}
        </>
      )}

      {isEdit && (
        <>
          <hr/>
          <h3>Payment History</h3>
          {payments.map(p=>(
            <div key={p.id}>
              ₹{p.amount} | {p.payment_method || "-"} | {p.transaction_number || "-"}
            </div>
          ))}

          <br/>
          <b>Add Payment</b><br/>
          <input placeholder="Amount" value={paymentForm.amount}
            onChange={e=>setPaymentForm({...paymentForm,amount:e.target.value})}/>
          <input placeholder="Method" value={paymentForm.payment_method}
            onChange={e=>setPaymentForm({...paymentForm,payment_method:e.target.value})}/>
          <input placeholder="Remark / Txn" value={paymentForm.transaction_number}
            onChange={e=>setPaymentForm({...paymentForm,transaction_number:e.target.value})}/>
          <button onClick={addPayment}>Add Payment</button>
        </>
      )}
    </AdminLayout>
  );
}