const STREAMLIT_URL =
  import.meta.env.VITE_STREAMLIT_URL || "http://localhost:8501/?embed=true";

export default function Tmo() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow overflow-hidden">
      <div className="px-6 pt-6">
        <h2 className="text-lg font-semibold">TMO / Tiempos sin gestión</h2>
        <p className="text-slate-500 text-sm mb-4">
          Vista embebida de tu app de análisis (Streamlit).
        </p>
      </div>

      {/* Ocupa todo el alto visible (restando la topbar y paddings) */}
      <iframe
        title="tiempo-sin-gestion"
        src={STREAMLIT_URL}
        className="block w-full h-[calc(100vh-160px)] min-h-[720px]"
        frameBorder="0"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
    </div>
  );
}
