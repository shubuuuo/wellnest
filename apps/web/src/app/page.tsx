// "use client";

// import { useState, type ComponentType } from "react";
// import DatasetTab from "@/components/DatasetTab";
// import ModelsTab from "@/components/ModelsTab";
// import PredictTab from "@/components/PredictTab";
// import OnlineTab from "@/components/OnlineTab";
// import ChatTab from "@/components/ChatTab";
// import { useApi } from "@/lib/useApi";
// import type { DatasetInfo } from "@/lib/types";

// const TABS: {
//   id: string;
//   label: string;
//   View: ComponentType<{ dataset: string }>;
// }[] = [
//   { id: "dataset", label: "Dataset", View: DatasetTab },
//   { id: "models", label: "Models", View: ModelsTab },
//   { id: "predict", label: "Predict", View: PredictTab },
//   { id: "online", label: "Online Learning", View: OnlineTab },
//   { id: "chat", label: "Assistant", View: ChatTab },
// ];

// export default function Home() {
//   const [active, setActive] = useState("dataset");
//   const [chosen, setChosen] = useState<string | null>(null);
//   const { data: datasets, error } = useApi<DatasetInfo[]>("/dataset");

//   const dataset = chosen ?? datasets?.[0]?.id ?? null;
//   const label = datasets?.find((d) => d.id === dataset)?.label;

//   return (
//     <div className="min-h-screen">
//       <header className="border-b border-line bg-surface">
//         <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4">
//           <div>
//             <h1 className="text-xl font-semibold text-brand">WellNest</h1>
//             <p className="text-sm text-muted">
//               Model training and online learning demo{label ? `: ${label}` : ""}
//             </p>
//           </div>
//           {datasets && datasets.length > 0 && (
//             <label className="text-sm">
//               Dataset{" "}
//               <select
//                 className="rounded-md border border-line bg-surface px-2 py-1"
//                 value={dataset ?? ""}
//                 onChange={(e) => setChosen(e.target.value)}
//               >
//                 {datasets.map((d) => (
//                   <option key={d.id} value={d.id}>
//                     {d.label}
//                   </option>
//                 ))}
//               </select>
//             </label>
//           )}
//         </div>
//         <nav className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4">
//           {TABS.map((t) => (
//             <button
//               key={t.id}
//               onClick={() => setActive(t.id)}
//               className={`whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium ${
//                 active === t.id
//                   ? "border-brand text-brand"
//                   : "border-transparent text-muted hover:text-ink"
//               }`}
//             >
//               {t.label}
//             </button>
//           ))}
//         </nav>
//       </header>
//       <main className="mx-auto max-w-6xl px-4 py-6">
//         {error && <p className="text-sm text-brand">{error}</p>}
//         {datasets && datasets.length === 0 && (
//           <p className="text-sm text-muted">
//             No trained dataset yet. Run: python ml/train.py lung
//           </p>
//         )}
//         {/* changing the key remounts the tab, which resets the charts and forms for the new dataset */}
//         {dataset &&
//           TABS.map(({ id, View }) => (
//             <div
//               key={`${dataset}-${id}`}
//               className={active === id ? "" : "hidden"}
//             >
//               <View dataset={dataset} />
//             </div>
//           ))}
//       </main>
//     </div>
//   );
// }

"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function Landing() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user)
      router.replace(user.role === "admin" ? "/admin" : "/app");
  }, [user, loading, router]);

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-6 px-4 text-center">
      <h1 className="text-4xl font-bold tracking-tight text-brand">WellNest</h1>
      <p className="text-lg text-muted">
        Estimate cancer risk from health data with transparent machine learning.
        An educational project, not medical advice.
      </p>
      <div className="flex gap-3">
        <Link
          href="/register"
          className="rounded-md bg-brand px-5 py-2 text-sm font-medium text-white"
        >
          Create account
        </Link>
        <Link
          href="/login"
          className="rounded-md border border-line px-5 py-2 text-sm font-medium"
        >
          Log in
        </Link>
      </div>
    </main>
  );
}
