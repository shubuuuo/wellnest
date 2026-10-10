"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function RequireAuth({
  role,
  children,
}: {
  role?: "admin";
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const blocked = !user || (role === "admin" && user.role !== "admin");

  useEffect(() => {
    if (loading) return;
    if (!user) router.replace("/login");
    else if (blocked) router.replace("/app");
  }, [user, loading, blocked, router]);

  if (loading || blocked)
    return <p className="p-8 text-sm text-muted">Loading…</p>;
  return <>{children}</>;
}
