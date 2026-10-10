"use client";

import { useCallback, useEffect, useState } from "react";
import Card from "./Card";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { User, UserList } from "@/lib/types";
import UserDetail from "./UserDetail";

const PAGE_SIZE = 15;
const field = "rounded-md border border-line bg-surface px-2 py-1 text-sm";

export default function UsersTab() {
  const { user: me } = useAuth();
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<User | null>(null);
  const [data, setData] = useState<UserList | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
        search,
      });
      if (role) params.set("role", role);
      setData(await api.get<UserList>(`/admin/users?${params}`));
      setProblem(null);
    } catch (e) {
      setProblem(
        e instanceof ApiError ? e.userMessage : "Could not load users",
      );
    }
  }, [page, search, role]);

  useEffect(() => {
    const timer = setTimeout(load, 250);
    return () => clearTimeout(timer);
  }, [load]);

  async function update(
    u: User,
    change: { role?: "user" | "admin"; is_active?: boolean },
  ) {
    try {
      await api.patch<User>(`/admin/users/${u.id}`, change);
      await load();
    } catch (e) {
      setProblem(e instanceof ApiError ? e.userMessage : "Update failed");
    }
  }

  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  if (selected) {
    return (
      <UserDetail
        userId={selected.id}
        name={selected.name}
        email={selected.email}
        onBack={() => setSelected(null)}
      />
    );
  }

  return (
    <Card title="Users">
      <div className="mb-3 flex flex-wrap gap-2">
        <input
          className={field}
          placeholder="Search name or email"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <select
          className={field}
          value={role}
          onChange={(e) => {
            setRole(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All roles</option>
          <option value="user">Users</option>
          <option value="admin">Admins</option>
        </select>
      </div>
      {problem && <p className="mb-3 text-sm text-brand">{problem}</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-muted">
            <tr>
              {[
                "Name",
                "Email",
                "Role",
                "Status",
                "Joined",
                "Last login",
                "Records",
              ].map((h) => (
                <th key={h} className="py-2 pr-4 font-medium">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data?.items.map((u) => {
              const self = u.id === me?.id;
              return (
                <tr key={u.id} className="border-t border-line">
                  <td className="py-2 pr-4 font-medium">
                    {u.name}
                    {self && " (you)"}
                  </td>
                  <td className="py-2 pr-4">{u.email}</td>
                  <td className="py-2 pr-4">
                    <select
                      className={field}
                      value={u.role}
                      disabled={self}
                      onChange={(e) =>
                        update(u, { role: e.target.value as "user" | "admin" })
                      }
                    >
                      <option value="user">user</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td className="py-2 pr-4">
                    <button
                      disabled={self}
                      onClick={() => update(u, { is_active: !u.is_active })}
                      className={`rounded px-2 py-0.5 text-xs disabled:opacity-50 ${u.is_active ? "bg-line" : "bg-brand text-white"}`}
                    >
                      {u.is_active
                        ? "Active (click to deactivate)"
                        : "Deactivated (click to restore)"}
                    </button>
                  </td>
                  <td className="py-2 pr-4">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-2 pr-4">
                    {u.last_login_at
                      ? new Date(u.last_login_at).toLocaleString()
                      : "never"}
                  </td>
                  <td className="py-2 pr-4">
                    <button
                      onClick={() => setSelected(u)}
                      className="rounded border border-line px-2 py-0.5 text-xs hover:border-brand"
                    >
                      View records
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex items-center gap-3 text-sm">
        <button
          disabled={page <= 1}
          onClick={() => setPage(page - 1)}
          className="rounded border border-line px-3 py-1 disabled:opacity-50"
        >
          Previous
        </button>
        <span className="text-muted">
          Page {page} of {pages} ({data?.total ?? 0} users)
        </span>
        <button
          disabled={page >= pages}
          onClick={() => setPage(page + 1)}
          className="rounded border border-line px-3 py-1 disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </Card>
  );
}
