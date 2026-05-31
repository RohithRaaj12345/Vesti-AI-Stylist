import { useState } from "react";
import { register, verifyOtp, resendOtp, login } from "../api.js";

// Register -> Verify (email OTP) -> Login. Calls onAuthed({name,email}) on login.
export default function AuthPanel({ onAuthed }) {
  const [mode, setMode] = useState("login"); // login | register | verify
  const [form, setForm] = useState({ name: "", mobile: "", email: "", password: "" });
  const [code, setCode] = useState("");
  const [devCode, setDevCode] = useState(null); // shown only when SMTP isn't configured
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const reset = (m) => { setMode(m); setError(""); setInfo(""); };

  async function doRegister(e) {
    e.preventDefault();
    setError(""); setInfo(""); setBusy(true);
    try {
      const res = await register(form);
      setDevCode(res.dev_email_code || null);
      setCode("");
      setMode("verify");
      setInfo("We've emailed you a verification code. Enter it below.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function doVerify() {
    setError(""); setInfo(""); setBusy(true);
    try {
      const res = await verifyOtp(form.email, "email", code);
      if (res.email_verified) {
        reset("login");
        setInfo("Email verified! Please log in.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function doResend() {
    setError(""); setInfo(""); setBusy(true);
    try {
      const res = await resendOtp(form.email, "email");
      if (res.dev_code) setDevCode(res.dev_code);
      setInfo("A new code was emailed to you.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function doLogin(e) {
    e.preventDefault();
    setError(""); setInfo(""); setBusy(true);
    try {
      const data = await login(form.email, form.password);
      onAuthed(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-card">
      {mode === "login" && (
        <form onSubmit={doLogin} className="auth-form">
          <h3>Log in</h3>
          <input type="email" placeholder="Email" value={form.email} onChange={set("email")} required />
          <input type="password" placeholder="Password" value={form.password} onChange={set("password")} required />
          <button className="btn" disabled={busy}>{busy ? "…" : "Log in"}</button>
          <p className="auth-switch">
            New here? <button type="button" onClick={() => reset("register")}>Create an account</button>
          </p>
        </form>
      )}

      {mode === "register" && (
        <form onSubmit={doRegister} className="auth-form">
          <h3>Create your account</h3>
          <input placeholder="Full name" value={form.name} onChange={set("name")} required />
          <input placeholder="Mobile (e.g. 9876543210)" value={form.mobile} onChange={set("mobile")} required />
          <input type="email" placeholder="Email" value={form.email} onChange={set("email")} required />
          <input type="password" placeholder="Password (min 8 chars)" value={form.password} onChange={set("password")} required />
          <button className="btn" disabled={busy}>{busy ? "…" : "Register"}</button>
          <p className="auth-switch">
            Already have an account? <button type="button" onClick={() => reset("login")}>Log in</button>
          </p>
        </form>
      )}

      {mode === "verify" && (
        <div className="auth-form">
          <h3>Verify your email</h3>
          <div className="verify-row">
            <input placeholder="Email code" value={code} onChange={(e) => setCode(e.target.value)} />
            <button type="button" className="btn sm" onClick={doVerify} disabled={busy}>Verify</button>
            <button type="button" className="btn ghost sm" onClick={doResend} disabled={busy}>Resend</button>
          </div>
          {devCode && <p className="auth-dev">Dev code (SMTP off): <b>{devCode}</b></p>}
          <p className="auth-switch">
            <button type="button" onClick={() => reset("login")}>Back to log in</button>
          </p>
        </div>
      )}

      {info && <p className="auth-info">{info}</p>}
      {error && <p className="error small">{error}</p>}
    </div>
  );
}
