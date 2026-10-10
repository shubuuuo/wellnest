"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Card from "@/components/Card";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const input =
  "w-full rounded-md border border-line bg-surface px-3 py-2 text-sm";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setProblem(null);
    try {
      const u = await login(email, password);
      router.replace(u.role === "admin" ? "/admin" : "/app");
    } catch (err) {
      setProblem(
        err instanceof ApiError ? err.userMessage : "Something went wrong",
      );
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4">
      <Card title="Log in">
        <form onSubmit={submit} className="space-y-3">
          <input
            className={input}
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className={input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {problem && <p className="text-sm text-brand">{problem}</p>}
          <button
            disabled={busy}
            className="w-full rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {busy ? "Signing in…" : "Log in"}
          </button>
        </form>
        <p className="mt-4 text-sm text-muted">
          New here?{" "}
          <Link href="/register" className="text-brand underline">
            Create an account
          </Link>
        </p>
      </Card>
    </main>
  );
}
