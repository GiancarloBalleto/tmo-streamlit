import { useEffect, useState } from "preact/hooks";
import { Route, Switch, Redirect, useLocation } from "wouter";
import "./firebase";
import Login from "./components/Login";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Tmo from "./pages/Tmo";
import { getAuth, onAuthStateChanged, signOut } from "firebase/auth";

function DashboardApp({ user }) {
  const [, setLocation] = useLocation();
  useEffect(() => {
    // Redirección por defecto a Home
    if (location.pathname === "/") setLocation("/");
  }, []);

  return (
    <Layout user={user} onLogout={() => signOut(getAuth())}>
      <Switch>
        <Route path="/" component={Home} />
        <Route path="/tmo" component={Tmo} />
        <Route> {/* fallback 404 -> home */}
          <Redirect to="/" />
        </Route>
      </Switch>
    </Layout>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsub = onAuthStateChanged(getAuth(), (u) => {
      setUser(u || null);
      setLoading(false);
    });
    return () => unsub();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center text-slate-500">
        Cargando…
      </div>
    );
  }

  return user ? <DashboardApp user={user} /> : <Login onLogin={setUser} />;
}
