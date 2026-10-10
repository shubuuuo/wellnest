"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Card from "@/components/Card";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const input =
  "w-full rounded-md border border-line bg-surface px-3 py-2 text-sm";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
    consent: false,
    training: false,
  });
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm({ ...form, [key]: value });
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setProblem(null);
    if (
      form.password.length < 8 ||
      !/[A-Za-z]/.test(form.password) ||
      !/\d/.test(form.password)
    ) {
      return setProblem(
        "Password needs at least 8 characters, with a letter and a number.",
      );
    }
    if (form.password !== form.confirm)
      return setProblem("Passwords do not match.");
    if (!form.consent) return setProblem("Please accept the data notice.");

    setBusy(true);
    try {
      await register({
        name: form.name,
        email: form.email,
        password: form.password,
        consent: form.consent,
        training_consent: form.training,
      });
      router.replace("/app");
    } catch (err) {
      setProblem(
        err instanceof ApiError ? err.userMessage : "Something went wrong",
      );
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      <Card title="Create your account">
        <form onSubmit={submit} className="space-y-3">
          <input
            className={input}
            placeholder="Full name"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            required
          />
          <input
            className={input}
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
            required
          />
          <input
            className={input}
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) => set("password", e.target.value)}
            required
          />
          <input
            className={input}
            type="password"
            placeholder="Confirm password"
            value={form.confirm}
            onChange={(e) => set("confirm", e.target.value)}
            required
          />
          <label className="flex items-start gap-2 text-xs text-muted">
            <input
              type="checkbox"
              checked={form.consent}
              onChange={(e) => set("consent", e.target.checked)}
              className="mt-0.5"
            />
            <label className="flex items-start gap-2 text-xs text-muted">
              <input
                type="checkbox"
                checked={form.training}
                onChange={(e) => set("training", e.target.checked)}
                className="mt-0.5"
              />
              Optional: if an administrator later confirms my real result, allow
              it to help improve the models, without my name or account. I can
              change this any time under Feedback.
            </label>
            I understand this is an educational tool, not medical advice, and
            that my answers and results will be stored and can be seen by the
            administrators.
          </label>
          {problem && <p className="text-sm text-brand">{problem}</p>}
          <button
            disabled={busy}
            className="w-full rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy ? "Creating…" : "Create account"}
          </button>
        </form>
        <p className="mt-4 text-sm text-muted">
          Already registered?{" "}
          <Link href="/login" className="text-brand underline">
            Log in
          </Link>
        </p>
      </Card>
    </main>
  );
}
