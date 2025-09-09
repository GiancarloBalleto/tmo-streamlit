// src/components/Login.jsx
import { useState, useEffect } from "preact/hooks";
import { FaEye, FaEyeSlash, FaGoogle } from "react-icons/fa";
import {
  getAuth,
  signInWithEmailAndPassword,
  sendPasswordResetEmail,
  GoogleAuthProvider,
  signInWithPopup,
} from "firebase/auth";
// Ajusta la ruta a tu logo (te dejé Logo.png en /assets)
import logo from "../assets/Logo.png";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState(localStorage.getItem("cobranzaiq:lastEmail") || "");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [mensajeIA, setMensajeIA] = useState("Cargando motivación...");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Mensaje motivador cacheado por día
  useEffect(() => {
    const hoy = new Date().toISOString().slice(0, 10);
    try {
      const cache = JSON.parse(localStorage.getItem("cobranzaiq:motivation")) || {};
      if (cache.fecha === hoy && cache.mensaje) {
        setMensajeIA(cache.mensaje);
        return;
      }
    } catch (_) {}
    fetch("https://us-central1-supervision-app-89746.cloudfunctions.net/mensajeMotivador")
      .then((r) => r.json())
      .then((d) => {
        const msg = d?.mensaje || "Analiza. Optimiza. Cobra mejor. 💼📈";
        setMensajeIA(msg);
        localStorage.setItem("cobranzaiq:motivation", JSON.stringify({ fecha: hoy, mensaje: msg }));
      })
      .catch(() => setMensajeIA("Analiza. Optimiza. Cobra mejor. 💼📈"));
  }, []);

  const auth = getAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const cred = await signInWithEmailAndPassword(auth, email.trim(), password);
      if (remember) localStorage.setItem("cobranzaiq:lastEmail", email.trim());
      else localStorage.removeItem("cobranzaiq:lastEmail");
      onLogin?.(cred.user);
    } catch (err) {
      console.error(err);
      setError("Correo o contraseña incorrectos");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setError("");
    if (!email) return setError("Escribe tu correo para enviarte el enlace de recuperación");
    try {
      await sendPasswordResetEmail(auth, email.trim());
      setError("Te enviamos un enlace para restablecer tu contraseña ✉️");
    } catch (err) {
      console.error(err);
      setError("No pudimos enviar el correo. Revisa el email ingresado.");
    }
  };

  const handleGoogle = async () => {
    setError("");
    setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      const cred = await signInWithPopup(auth, provider);
      onLogin?.(cred.user);
    } catch (err) {
      console.error(err);
      setError("No se pudo iniciar sesión con Google");
    } finally {
      setLoading(false);
    }
  };

  const isDisabled = loading || !email || password.length < 6;

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center">
      <div className="w-full max-w-md px-6">
        {/* Marca */}
       {/* Marca + slogan (solo logo, más grande) */}
<div className="flex flex-col items-center text-center mb-8">
  <img
    src={logo}
    alt="CobranzaIQ"
    className="w-48 sm:w-64 md:w-72 lg:w-80 h-auto object-contain drop-shadow-xl"
  />
  <p className="text-slate-500 text-sm italic mt-4">{mensajeIA}</p>
</div>

        {/* Card */}
        <section className="bg-white/80 backdrop-blur-xl border border-slate-200 shadow-xl rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">🔐 Iniciar sesión</h2>

          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label htmlFor="email" className="sr-only">Correo</label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                inputMode="email"
                placeholder="Correo electrónico"
                value={email}
                onInput={(e) => setEmail(e.currentTarget.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-3 outline-none focus:ring-2 focus:ring-sky-400"
              />
            </div>

            <div className="relative">
              <label htmlFor="password" className="sr-only">Contraseña</label>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Contraseña"
                value={password}
                onInput={(e) => setPassword(e.currentTarget.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-3 pr-11 outline-none focus:ring-2 focus:ring-sky-400"
              />
              <button
                type="button"
                aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                onClick={() => setShowPassword((s) => !s)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700"
              >
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </button>
            </div>

            {error && (
              <div className={`text-sm ${error.includes("enlace") ? "text-emerald-600" : "text-rose-600"}`}>
                {error}
              </div>
            )}

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 select-none text-slate-600">
                <input
                  type="checkbox"
                  className="accent-sky-600"
                  checked={remember}
                  onChange={(e) => setRemember(e.currentTarget.checked)}
                />
                Recordarme
              </label>
              <button type="button" onClick={handleReset} className="text-sky-700 hover:underline">
                ¿Olvidaste tu contraseña?
              </button>
            </div>

            <button
              type="submit"
              disabled={isDisabled}
              className={`w-full rounded-lg py-3 font-medium text-white transition
                ${isDisabled ? "bg-slate-400 cursor-not-allowed" : "bg-sky-600 hover:bg-sky-700"}`}
            >
              {loading ? "Ingresando..." : "Iniciar sesión"}
            </button>

            <div className="relative my-2">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-white/80 px-3 text-xs text-slate-400">o</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleGoogle}
              className="w-full rounded-lg py-3 font-medium border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 flex items-center justify-center gap-2"
            >
              <FaGoogle /> Continuar con Google
            </button>
          </form>
        </section>

        <footer className="mt-6 text-center text-xs text-slate-400">
          © {new Date().getFullYear()} CobranzaIQ · Desarrollado por Giancarlo Balleto
        </footer>
      </div>
    </div>
  );
}
