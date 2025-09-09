import { Link, useRoute } from "wouter";
import { FiHome, FiClock, FiLogOut } from "react-icons/fi";

function NavItem({ to, icon: Icon, label }) {
  const [isActive] = useRoute(to);
  return (
    <Link href={to}>
      <a
        className={`flex items-center gap-3 px-3 py-2 rounded-lg transition
        ${isActive ? "bg-sky-100 text-sky-700" : "text-slate-600 hover:bg-slate-100"}`}
      >
        <Icon className="text-lg" />
        <span className="font-medium">{label}</span>
      </a>
    </Link>
  );
}

export default function Layout({ user, onLogout, children }) {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top bar FULL-WIDTH */}
      <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-slate-200">
        <div className="w-full px-6 h-14 flex items-center justify-between">
          <div className="font-bold">CobranzaIQ</div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">{user?.email}</span>
            <button
              onClick={onLogout}
              className="inline-flex items-center gap-2 rounded bg-slate-800 text-white px-3 py-1.5 text-sm hover:bg-slate-900"
            >
              <FiLogOut /> Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      {/* Body FULL-WIDTH */}
      <div className="w-full px-6 py-6 grid gap-6
                      grid-cols-1 md:grid-cols-[220px_1fr]">
        {/* Sidebar fijo en vertical */}
        <aside className="md:sticky md:top-16 h-max">
          <nav className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm space-y-2">
            <div className="text-xs uppercase tracking-wide text-slate-500 px-1 pb-1">Menú</div>
            <NavItem to="/" icon={FiHome} label="Home" />
            <NavItem to="/tmo" icon={FiClock} label="TMO / Tiempos muertos" />
          </nav>
        </aside>

        {/* Contenido ocupa TODO el restante */}
        <main className="min-w-0">{children}</main>
      </div>
    </div>
  );
}
