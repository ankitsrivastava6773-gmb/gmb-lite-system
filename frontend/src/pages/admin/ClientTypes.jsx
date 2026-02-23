import { useEffect, useState } from "react";
import AdminLayout from "../../layouts/AdminLayout";
import { supabase } from "../../services/supabaseClient";

/* ---------- TAG INPUT ---------- */
const TagInput = ({ label, values, setValues }) => {
  const [input, setInput] = useState("");

  const addTag = () => {
    if (!input.trim()) return;
    if (values.includes(input.trim())) return;
    setValues([...values, input.trim()]);
    setInput("");
  };

  const removeTag = (v) => {
    setValues(values.filter(x => x !== v));
  };

  return (
    <>
      <b>{label}</b><br/>
      {values.map((v,i)=>(
        <span key={i}
          style={{
            border:"1px solid #000",
            padding:"2px 6px",
            margin:4,
            display:"inline-block",
            cursor:"pointer"
          }}
          onClick={()=>removeTag(v)}
          title="Click to remove"
        >
          {v} ✕
        </span>
      ))}
      <br/>
      <input value={input} onChange={e=>setInput(e.target.value)} />
      <button onClick={addTag}>Add</button>
      <br/><br/>
    </>
  );
};

/* ---------- MAIN ---------- */
export default function ClientTypes() {
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    type_name: "",
    contexts: [],
    trust_signals_list: [],
    seo_keywords_list: [],
    tone: "",
    verbosity: 3
  });

  /* ---------- LOAD ---------- */
  const loadTypes = async () => {
    const { data } = await supabase
      .from("client_types")
      .select("*")
      .order("created_at", { ascending: false });

    setTypes(data || []);
  };

  useEffect(() => {
    loadTypes();
  }, []);

  /* ---------- ADD TYPE ---------- */
  const addType = async () => {
    if (!form.type_name) {
      alert("Type name required");
      return;
    }

    setLoading(true);

    const { error } = await supabase.from("client_types").insert([{
      type_name: form.type_name,
      context: form.contexts.join(","),               // legacy
      trust_signals: form.trust_signals_list.join(","),
      seo_keywords: form.seo_keywords_list.join(","),
      contexts: form.contexts,
      trust_signals_list: form.trust_signals_list,
      seo_keywords_list: form.seo_keywords_list,
      tone: form.tone || null,
      verbosity: form.verbosity,
      use_type_defaults: true
    }]);

    setLoading(false);

    if (error) {
      alert("Save failed");
      console.error(error);
      return;
    }

    setForm({
      type_name: "",
      contexts: [],
      trust_signals_list: [],
      seo_keywords_list: [],
      tone: "",
      verbosity: 3
    });

    loadTypes();
  };

  /* ---------- UPDATE TYPE ---------- */
  const updateType = async (t) => {
    await supabase
      .from("client_types")
      .update({
        context: (t.contexts || []).join(","),
        trust_signals: (t.trust_signals_list || []).join(","),
        seo_keywords: (t.seo_keywords_list || []).join(","),
        contexts: t.contexts,
        trust_signals_list: t.trust_signals_list,
        seo_keywords_list: t.seo_keywords_list,
        tone: t.tone,
        verbosity: t.verbosity
      })
      .eq("id", t.id);

    loadTypes();
  };

  return (
    <AdminLayout>
      <h2>Client Types</h2>

      {/* ---------- ADD FORM ---------- */}
      <div style={{ border:"1px solid #ccc", padding:15, marginBottom:20 }}>
        <h3>Add New Type</h3>

        <input
          placeholder="Type Name (Restaurant)"
          value={form.type_name}
          onChange={e=>setForm({...form,type_name:e.target.value})}
        /><br/><br/>

        <TagInput label="Context"
          values={form.contexts}
          setValues={v=>setForm({...form,contexts:v})}
        />

        <TagInput label="Trust Signals"
          values={form.trust_signals_list}
          setValues={v=>setForm({...form,trust_signals_list:v})}
        />

        <TagInput label="SEO Keywords"
          values={form.seo_keywords_list}
          setValues={v=>setForm({...form,seo_keywords_list:v})}
        />

        <b>Default Tone</b><br/>
        <input
          value={form.tone}
          onChange={e=>setForm({...form,tone:e.target.value})}
        /><br/><br/>

        <b>Default Verbosity (1–5)</b><br/>
        <input type="number" min="1" max="5"
          value={form.verbosity}
          onChange={e=>setForm({...form,verbosity:+e.target.value})}
        /><br/><br/>

        <button onClick={addType} disabled={loading}>
          {loading ? "Saving..." : "Add Type"}
        </button>
      </div>

      {/* ---------- EXISTING TYPES ---------- */}
      {types.map(t => (
        <div key={t.id}
          style={{ border:"1px solid #000", padding:15, marginBottom:10 }}
        >
          <h3>{t.type_name}</h3>

          <TagInput label="Context"
            values={t.contexts || []}
            setValues={v=>{
              t.contexts=v; setTypes([...types]);
            }}
          />

          <TagInput label="Trust Signals"
            values={t.trust_signals_list || []}
            setValues={v=>{
              t.trust_signals_list=v; setTypes([...types]);
            }}
          />

          <TagInput label="SEO Keywords"
            values={t.seo_keywords_list || []}
            setValues={v=>{
              t.seo_keywords_list=v; setTypes([...types]);
            }}
          />

          <b>Tone</b><br/>
          <input
            value={t.tone || ""}
            onChange={e=>{
              t.tone=e.target.value; setTypes([...types]);
            }}
          /><br/><br/>

          <b>Verbosity</b><br/>
          <input type="number" min="1" max="5"
            value={t.verbosity}
            onChange={e=>{
              t.verbosity=+e.target.value; setTypes([...types]);
            }}
          /><br/><br/>

          <button onClick={()=>updateType(t)}>Update</button>
        </div>
      ))}
    </AdminLayout>
  );
}